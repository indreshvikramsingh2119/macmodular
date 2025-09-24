import os
import time
import threading
import numpy as np
import pandas as pd
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QMessageBox
from scipy.signal import find_peaks
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas


class DemoManager:
    
    def __init__(self, ecg_test_page):

        self.ecg_test_page = ecg_test_page
        self.demo_fs = 200  # Demo sampling rate (200 Hz)
        self.demo_thread = None
        self.demo_timer = None
        self.demo_heart_rates = []  # For heart rate smoothing
        # Thread coordination
        self._stop_event = threading.Event()
        self._lock = threading.Lock()
        
        # Wave speed control variables
        self.current_wave_speed = 12.5  # mm/s
        self.samples_per_second = 200  # Base sampling rate
        self.speed_multiplier = 1.0  # Will be calculated based on wave speed
        
        # Provide dashboard with effective sampling rate when in demo
        self._set_demo_sampling_rate(self.samples_per_second)
        # Fixed metrics store for demo stability
        self._demo_fixed_metrics = None
        # Internal running flag to avoid touching Qt widgets from worker thread
        self._running_demo = False
        # Stop threads if the page is destroyed
        try:
            self.ecg_test_page.destroyed.connect(self._on_page_destroyed)
        except Exception:
            pass
    
    def _get_calculation_functions(self):
       
        from .twelve_lead_test import calculate_qrs_axis, calculate_st_segment
        return calculate_qrs_axis, calculate_st_segment
    
    def _update_wave_speed_settings(self):
        """
        Update wave speed settings based on current settings manager.
        This affects the visual speed and spacing of ECG waves.
        """
        # Get current wave speed from settings
        self.current_wave_speed = self.ecg_test_page.settings_manager.get_wave_speed()
        
        # Calculate speed multiplier based on wave speed
        # 12.5 mm/s = slow (0.5x), 25 mm/s = normal (1.0x), 50 mm/s = fast (2.0x)
        if self.current_wave_speed <= 12.5:
            self.speed_multiplier = 0.5  # Slow waves, peaks closer together
        elif self.current_wave_speed <= 25.0:
            self.speed_multiplier = 1.0  # Normal speed
        else:  # 50 mm/s
            self.speed_multiplier = 2.0  # Fast waves, peaks further apart
        
        # Update sampling rate for demo data reading
        # self.samples_per_second = int(200 * self.speed_multiplier)
        
        print(f"🌊 Wave speed updated: {self.current_wave_speed}mm/s (multiplier: {self.speed_multiplier}x)")

    
    
    def _set_demo_sampling_rate(self, sampling_rate):
        """Expose effective sampling rate to dashboard calculators via ecg_test_page.sampler."""
        try:
            if not hasattr(self.ecg_test_page, 'sampler') or self.ecg_test_page.sampler is None:
                self.ecg_test_page.sampler = type('Sampler', (), {})()
            # Keep dashboard filter stable: clamp to >=200 Hz
            safe_fs = max(200.0, float(sampling_rate))
            self.ecg_test_page.sampler.sampling_rate = safe_fs
        except Exception:
            pass

    def toggle_demo_mode(self, is_checked):
        
        if is_checked:
            # If real acquisition is running, prevent enabling demo
            try:
                if hasattr(self.ecg_test_page, 'timer') and self.ecg_test_page.timer.isActive():
                    self.ecg_test_page.demo_toggle.setChecked(False)
                    return
            except Exception as e:
                print(f"[Demo Toggle] Check real run state failed: {e}")

            # Demo is being turned ON
            self.ecg_test_page.demo_toggle.setText("ON")

            # Get current wave speed and print it
            current_speed = self.ecg_test_page.settings_manager.get_wave_speed()
            # current_gain removed from recent changes

            print("🟢 Demo mode ON - Starting demo data...")
            
            # Update wave speed settings before starting
            self._update_wave_speed_settings()
            
            # Reset fixed metrics for new demo session
            self._demo_fixed_metrics = None
            self._running_demo = True
            # Start demo data generation in the existing 12-lead grid
            self.start_demo_data()
            
        else:
            # Demo is being turned OFF
            self.ecg_test_page.demo_toggle.setText("OFF")
            print("🔴 Demo mode OFF - Stopping demo data...")
            
            # Stop demo data generation
            self.stop_demo_data()
    
    def start_demo_data(self):
        """Start reading real ECG data from dummycsv.csv file with wave speed control"""
        # Ensure any previous demo resources are stopped before starting new
        try:
            self._stop_event.set()
            if self.demo_thread and self.demo_thread.is_alive():
                self.demo_thread.join(timeout=1.0)
        except Exception:
            pass
        finally:
            self._stop_event.clear()
            self.demo_thread = None
            # Stop and delete any existing timer
            try:
                if self.demo_timer:
                    self.demo_timer.stop()
                    self.demo_timer.deleteLater()
            except Exception:
                pass
            self.demo_timer = None
        # Resolve dummycsv.csv from common locations
        ecg_dir = os.path.dirname(__file__)
        src_dir = os.path.abspath(os.path.join(ecg_dir, '..'))
        project_root = os.path.abspath(os.path.join(src_dir, '..'))
        candidates = [
            os.path.join(ecg_dir, 'dummycsv.csv'),
            os.path.join(project_root, 'dummycsv.csv'),
            os.path.abspath('dummycsv.csv')
        ]
        csv_path = None
        for p in candidates:
            if os.path.exists(p):
                csv_path = p
                break
        if not csv_path:
            msg = (
                "dummycsv.csv not found. Place it in one of these locations:\n"
                f"- {os.path.join(ecg_dir, 'dummycsv.csv')}\n"
                f"- {os.path.join(project_root, 'dummycsv.csv')}\n"
                f"- {os.path.abspath('dummycsv.csv')}"
            )
            QMessageBox.warning(self.ecg_test_page, "Demo file missing", msg)
            # Don't start demo if CSV is missing
            self.ecg_test_page.demo_toggle.setChecked(False)
            return
        
        try:
            # Read the CSV file
            df = pd.read_csv(csv_path, sep='\t')  # Use tab separator
            print(f"✅ Successfully loaded {len(df)} rows from dummycsv.csv")
            
            # Get all lead columns (excluding 'Sample' column)
            lead_columns = [col for col in df.columns if col != 'Sample']
            print(f" Found leads: {lead_columns}")
            
            # Clear existing data - data is a list of numpy arrays, not a dictionary
            for i in range(len(self.ecg_test_page.data)):
                self.ecg_test_page.data[i] = np.zeros(self.ecg_test_page.buffer_size)
            
            # Initialize data with first few rows
            # Prefill enough samples to immediately show ~4 peaks
            csv_base_fs = int(150 * self.speed_multiplier)  # demo CSV base
            prefill_needed = min(self.ecg_test_page.buffer_size, max(100, int(csv_base_fs * 4.0)), len(df))
            for lead in lead_columns:
                if lead in self.ecg_test_page.leads:
                    lead_index = self.ecg_test_page.leads.index(lead)
                    # Add initial prefill samples to start
                    initial_samples = prefill_needed
                    series = df[lead].iloc[:initial_samples]
                    count = min(len(series), self.ecg_test_page.buffer_size)
                    self.ecg_test_page.data[lead_index][:count] = np.array(series[:count])
            
            # Start reading data row by row from CSV with wave speed control
            def read_csv_data():
                try:
                    row_index = prefill_needed  # continue after prefill
                    consecutive_errors = 0
                    max_consecutive_errors = 10
                    
                    while (not self._stop_event.is_set()) and self._running_demo and row_index < len(df):
                        try:
                            # Read data for all leads with error handling
                            for lead in lead_columns:
                                try:
                                    if lead in self.ecg_test_page.leads:
                                        lead_index = self.ecg_test_page.leads.index(lead)
                                        
                                        # Validate row index
                                        if row_index >= len(df) or row_index < 0:
                                            print(f"❌ Invalid row index: {row_index}")
                                            continue
                                        
                                        # Get value with validation
                                        value = df[lead].iloc[row_index]
                                        
                                        # Validate value
                                        if pd.isna(value) or np.isnan(value) or np.isinf(value):
                                            print(f"❌ Invalid value for {lead} at row {row_index}: {value}")
                                            value = 0.0
                                        
                                        # Convert to float safely
                                        try:
                                            value = float(value)
                                        except (ValueError, TypeError):
                                            print(f"❌ Cannot convert value to float: {value}")
                                            value = 0.0
                                        
                                        # Update data using numpy roll method with bounds checking
                                        with self._lock:
                                            if (hasattr(self.ecg_test_page, 'data') and 
                                                lead_index < len(self.ecg_test_page.data) and
                                                len(self.ecg_test_page.data[lead_index]) > 0):
                                                
                                                self.ecg_test_page.data[lead_index] = np.roll(
                                                    self.ecg_test_page.data[lead_index], -1)
                                                self.ecg_test_page.data[lead_index][-1] = value
                                            else:
                                                print(f"❌ Invalid data buffer for lead {lead_index}")
                                                
                                except Exception as e:
                                    print(f"❌ Error processing lead {lead} at row {row_index}: {e}")
                                    continue
                            
                            row_index += 1
                            consecutive_errors = 0  # Reset error counter on success
                            
                            # Loop back to beginning if we reach the end 
                            if row_index >= len(df):
                                row_index = 0
                                print("🔄 Restarting ECG data from beginning...")
                            
                            # Dynamic delay based on wave speed with error handling
                            try:
                                base_delay = 0.004  # 250 samples per second base (matching real hardware)
                                actual_delay = max(0.001, base_delay / max(0.1, self.speed_multiplier))
                                time.sleep(actual_delay)
                            except Exception as e:
                                print(f"❌ Error in sleep delay: {e}")
                                time.sleep(0.004)  # Fallback delay
                                
                        except Exception as e:
                            consecutive_errors += 1
                            print(f"❌ Error in CSV data reading (attempt {consecutive_errors}): {e}")
                            
                            if consecutive_errors >= max_consecutive_errors:
                                print(f"❌ Too many consecutive errors ({consecutive_errors}), stopping demo")
                                self._stop_event.set()
                                break
                            
                            # Try to recover by skipping problematic row
                            row_index += 1
                            if row_index >= len(df):
                                row_index = 0
                            
                            # Short delay before retry
                            time.sleep(0.01)
                            
                except Exception as e:
                    print(f"❌ Critical error in read_csv_data: {e}")
                    self._stop_event.set()
            
            # Start CSV data reading in background thread
            self.demo_thread = threading.Thread(target=read_csv_data, name="ECGDemoCSVThread", daemon=True)
            self.demo_thread.start()
            
            # Update effective sampling rate for CSV demo (base 150 Hz scaled by speed)
            self.samples_per_second = int(150 * self.speed_multiplier)
            self._set_demo_sampling_rate(self.samples_per_second)

            # Start timer to update plots with real CSV data
            # Timer interval also affected by wave speed
            self.demo_timer = QTimer(self.ecg_test_page)
            self.demo_timer.timeout.connect(self.update_demo_plots)
            
            # Adjust timer interval based on wave speed
            # Use a reasonable UI FPS (~30-60 FPS)
            base_interval = 33  # ~30 FPS base
            timer_interval = max(10, int(base_interval / self.speed_multiplier))
            self.demo_timer.start(timer_interval)
            
            print(f"🚀 Demo mode started with wave speed: {self.current_wave_speed}mm/s")
            
        except Exception as e:
            print(f"❌ Error reading dummycsv.csv: {e}")
            QMessageBox.warning(self.ecg_test_page, "Error", f"Failed to load dummycsv.csv: {str(e)}")
            # Don't start demo if CSV reading fails
            self.ecg_test_page.demo_toggle.setChecked(False)

    def update_demo_plots(self):
        current_speed = self.ecg_test_page.settings_manager.get_wave_speed()
        if current_speed != self.current_wave_speed:
            # Update internal speed and adjust timer interval without full restart
            self._update_wave_speed_settings()
            try:
                if self.demo_timer:
                    base_interval = 33  # ~30 FPS base
                    timer_interval = max(10, int(base_interval / self.speed_multiplier))
                    self.demo_timer.setInterval(timer_interval)
                # Keep dashboard calculator in sync with effective sampling rate
                # CSV demo base is 150Hz; synthetic is handled in start_synthetic_demo
                self.samples_per_second = int(150 * self.speed_multiplier)
                self._set_demo_sampling_rate(self.samples_per_second)
            except Exception:
                pass
        
        for i, lead in enumerate(self.ecg_test_page.leads):
            if i < len(self.ecg_test_page.data_lines) and i < len(self.ecg_test_page.data):
                lead_data = self.ecg_test_page.data[i]

                # Center baseline and apply gain 5/10/20
                centered = lead_data - np.mean(lead_data)
                try:
                    gain = float(self.ecg_test_page.settings_manager.get_wave_gain()) / 10.0
                except Exception:
                    gain = 1.0
                centered *= gain

                # Target about 4 peaks (≈4 seconds at 60 BPM) in view regardless of speed
                display_len = 1000  # keep grid resolution constant
                desired_seconds = 4.0
                try:
                    effective_fs = float(self.samples_per_second) if self.samples_per_second else 250.0
                except Exception:
                    effective_fs = 250.0
                window_len = int(max(100, min(len(lead_data), effective_fs * desired_seconds)))
                src = np.asarray(centered[-window_len:])
                if src.size < 2:
                    resampled = np.zeros(display_len)
                else:
                    x_src = np.linspace(0, 1, src.size)
                    x_dst = np.linspace(0, 1, display_len)
                    resampled = np.interp(x_dst, x_src, src)

                self.ecg_test_page.data_lines[i].setData(resampled)

                # Dynamic Y-range based on resampled data
                data_range = np.max(np.abs(resampled)) if resampled.size else 1000
                y_min = -data_range * 1.2
                y_max = data_range * 1.2
                if (y_max - y_min) < 200:
                    c = (y_max + y_min) / 2
                    y_min, y_max = c - 100, c + 100
                self.ecg_test_page.plot_widgets[i].setYRange(y_min, y_max, padding=0.1)
        
        # Calculate intervals for dashboard in demo mode
        if hasattr(self.ecg_test_page, 'dashboard_callback') and self.ecg_test_page.dashboard_callback:
            self._calculate_demo_intervals()

    def start_synthetic_demo(self):
        """Stream synthetic ECG-like waves when CSV is unavailable."""
        # Ensure any previous demo resources are stopped before starting new
        try:
            self._stop_event.set()
            if self.demo_thread and self.demo_thread.is_alive():
                self.demo_thread.join(timeout=1.0)
        except Exception:
            pass
        finally:
            self._stop_event.clear()
            self.demo_thread = None
            try:
                if self.demo_timer:
                    self.demo_timer.stop()
                    self.demo_timer.deleteLater()
            except Exception:
                pass
            self.demo_timer = None
        # Initialize buffers
        for i in range(len(self.ecg_test_page.data)):
            self.ecg_test_page.data[i] = np.zeros(self.ecg_test_page.buffer_size)

        # Parameters
        try:
            fs = 250.0
            hr_bpm = 72.0
            rr = 60.0 / hr_bpm
            two_pi = 2.0 * np.pi
            gain = 1.0
            # Update speed settings
            self._update_wave_speed_settings()
        except Exception:
            fs = 250.0
            rr = 0.8
            gain = 1.0

        # Background thread to stream samples

        def stream():
            t = 0.0
            dt = 1.0 / fs
            while (not self._stop_event.is_set()) and self._running_demo:
                # Simple synthetic lead II heartbeat shape using summed gaussians
                # Base heartbeat
                phase = (t % rr) / rr
                # Construct a crude P-QRS-T morphology
                p = 0.1 * np.exp(-((phase - 0.2) ** 2) / 0.0008)
                q = -0.25 * np.exp(-((phase - 0.35) ** 2) / 0.0002)
                r = 1.0 * np.exp(-((phase - 0.375) ** 2) / 0.00005)
                s = -0.35 * np.exp(-((phase - 0.40) ** 2) / 0.0001)
                t_w = 0.3 * np.exp(-((phase - 0.6) ** 2) / 0.003)
                sample = (p + q + r + s + t_w) * 1000.0 * gain

                # Add a tiny noise
                sample += np.random.normal(0, 5)

                # Update all leads with simple variations
                for li in range(len(self.ecg_test_page.data)):
                    val = sample * (0.8 + 0.4 * np.sin(two_pi * (li + 1) * 0.03 * t))
                    with self._lock:
                        self.ecg_test_page.data[li] = np.roll(self.ecg_test_page.data[li], -1)
                        self.ecg_test_page.data[li][-1] = val

                # Respect wave speed for visual pacing
                delay = (1.0 / fs) / max(0.5, self.speed_multiplier)
                time.sleep(delay)
                t += dt

        self.demo_thread = threading.Thread(target=stream, name="ECGDemoSynthThread", daemon=True)
        self.demo_thread.start()

        # Timer to draw plots
        self.demo_timer = QTimer(self.ecg_test_page)
        self.demo_timer.timeout.connect(self.update_demo_plots)
        base_interval = 33  # ~30 FPS base
        timer_interval = int(base_interval / max(0.5, self.speed_multiplier))
        self.demo_timer.start(max(10, timer_interval))

        # Effective sampling for synthetic: fs scaled by speed multiplier (min 0.5x)
        self.samples_per_second = int(fs * max(0.5, self.speed_multiplier))
        self._set_demo_sampling_rate(self.samples_per_second)
        print("🚀 Synthetic demo started (CSV missing)")
    
    def _calculate_demo_intervals(self):
        """Calculate ECG intervals for dashboard display in demo mode"""
        try:
            # Get Lead II data for interval calculations (Lead II is index 1)
            if len(self.ecg_test_page.data) > 1:
                # Copy under lock to avoid race with writer thread
                with self._lock:
                    lead2_data = np.copy(self.ecg_test_page.data[1])  # Lead II
                    lead_I_data = np.copy(self.ecg_test_page.data[0])  # Lead I
                    lead_aVF_data = np.copy(self.ecg_test_page.data[5])  # Lead aVF
                
                if len(lead2_data) > 100:  # Need enough data for calculations
                    # Use adjusted sampling rate based on wave speed
                    sampling_rate = self.samples_per_second
                    
                    # Use recent data for calculations
                    recent_data = np.array(lead2_data[-500:])
                    centered_data = recent_data - np.mean(recent_data)
                    
                    # Demo-specific peak detection with adjusted parameters
                    r_peaks, _ = find_peaks(centered_data, 
                                          distance=int(0.6 * sampling_rate),
                                          prominence=1.0 * np.std(centered_data))
                    
                    # Calculate intervals only if we have R peaks
                    if len(r_peaks) > 1:
                        # RR intervals and heart rate
                        rr_intervals = np.diff(r_peaks) / sampling_rate
                        mean_rr = np.mean(rr_intervals)
                        heart_rate = 60 / mean_rr if mean_rr > 0 else None
                        
                        # Apply demo heart rate correction
                        if heart_rate and heart_rate > 100:
                            # If demo heart rate is too high, apply correction factor
                            correction_factor = 0.6  # Reduce by 40%
                            heart_rate = heart_rate * correction_factor
                            print(f"💓 Demo heart rate corrected: {heart_rate:.1f} BPM")
                        
                        # Apply demo heart rate smoothing
                        if heart_rate and 30 <= heart_rate <= 200:
                            self.demo_heart_rates.append(heart_rate)
                            if len(self.demo_heart_rates) > 3:
                                self.demo_heart_rates.pop(0)
                            
                            # Use smoothed heart rate for demo
                            heart_rate = np.mean(self.demo_heart_rates)
                            print(f"📊 Demo smoothed heart rate: {heart_rate:.1f} BPM")
                        
                        # Calculate P, Q, S, T peaks
                        q_peaks, s_peaks = self._calculate_qs_peaks(centered_data, r_peaks, sampling_rate)
                        p_peaks = self._calculate_p_peaks(centered_data, q_peaks, sampling_rate)
                        t_peaks = self._calculate_t_peaks(centered_data, s_peaks, sampling_rate)
                        
                        # Calculate intervals
                        pr_interval = self._calculate_pr_interval(p_peaks, r_peaks, sampling_rate)
                        qrs_duration = self._calculate_qrs_duration(q_peaks, s_peaks, sampling_rate)
                        qt_interval = self._calculate_qt_interval(q_peaks, t_peaks, sampling_rate)
                        qtc_interval = self._calculate_qtc_interval(qt_interval, heart_rate)
                        
                        # Get calculation functions at runtime to avoid circular import
                        calculate_qrs_axis, calculate_st_segment = self._get_calculation_functions()
                        
                        # Calculate QRS axis and ST segment using imported functions
                        qrs_axis = calculate_qrs_axis(lead_I_data, lead_aVF_data, r_peaks)
                        st_segment = calculate_st_segment(lead2_data, r_peaks, fs=sampling_rate)
                        
                        # Prepare safe ST value (numeric or descriptive text)
                        try:
                            if isinstance(st_segment, (int, float, np.floating)):
                                st_out = int(round(float(st_segment)))
                            elif isinstance(st_segment, str):
                                st_out = st_segment
                            else:
                                st_out = None
                        except Exception:
                            st_out = None

                        # Initialize fixed demo metrics once, then keep constant
                        if self._demo_fixed_metrics is None:
                            try:
                                fixed_hr = 60
                                fixed_pr = int(round(pr_interval)) if pr_interval is not None else 160
                                fixed_qrs = int(round(qrs_duration)) if qrs_duration is not None else 90
                                fixed_qtc = int(round(qtc_interval)) if (qtc_interval is not None and qtc_interval >= 0) else 400
                                fixed_axis = qrs_axis if qrs_axis is not None else "0°"
                                fixed_st = st_out if st_out is not None else "Isoelectric"
                            except Exception:
                                fixed_hr, fixed_pr, fixed_qrs, fixed_qtc, fixed_axis, fixed_st = 60, 160, 90, 400, "0°", "Isoelectric"
                            self._demo_fixed_metrics = {
                                'Heart_Rate': fixed_hr,
                                'PR': fixed_pr,
                                'QRS': fixed_qrs,
                                'QTc': fixed_qtc,
                                'QRS_axis': fixed_axis,
                                'ST': fixed_st
                            }

                        # Always send fixed metrics in demo mode
                        payload = dict(self._demo_fixed_metrics)
                        try:
                            self.ecg_test_page.dashboard_callback(payload)
                        except Exception as cb_err:
                            print(f"❌ Error updating dashboard from demo: {cb_err}")
                        
                        # Fixed print statement to handle None values
                        pr_str = f"{self._demo_fixed_metrics['PR']} ms" if self._demo_fixed_metrics else "N/A"
                        qrs_str = f"{self._demo_fixed_metrics['QRS']} ms" if self._demo_fixed_metrics else "N/A"
                        hr_str = f"{self._demo_fixed_metrics['Heart_Rate']} bpm" if self._demo_fixed_metrics else "N/A"
                        
                        print(f"📈 Demo intervals updated: HR={hr_str}, PR={pr_str}, QRS={qrs_str}")
                        
        except Exception as e:
            print(f"❌ Error calculating demo intervals: {e}")
    
    def _calculate_qs_peaks(self, centered_data, r_peaks, sampling_rate):
        """Calculate Q and S peaks"""
        q_peaks = []
        s_peaks = []
        for r in r_peaks:
            # Q peak before R
            q_start = max(0, r - int(0.06 * sampling_rate))
            q_end = r
            if q_end > q_start:
                q_idx = np.argmin(centered_data[q_start:q_end]) + q_start
                q_peaks.append(q_idx)
            
            # S peak after R
            s_start = r
            s_end = min(len(centered_data), r + int(0.06 * sampling_rate))
            if s_end > s_start:
                s_idx = np.argmin(centered_data[s_start:s_end]) + s_start
                s_peaks.append(s_idx)
        
        return q_peaks, s_peaks
    
    def _calculate_p_peaks(self, centered_data, q_peaks, sampling_rate):
        """Calculate P peaks"""
        p_peaks = []
        for q in q_peaks:
            p_start = max(0, q - int(0.2 * sampling_rate))
            p_end = q - int(0.08 * sampling_rate)
            if p_end > p_start:
                p_candidates, _ = find_peaks(centered_data[p_start:p_end], 
                                           prominence=0.1 * np.std(centered_data))
                if len(p_candidates) > 0:
                    p_peaks.append(p_start + p_candidates[-1])
        return p_peaks
    
    def _calculate_t_peaks(self, centered_data, s_peaks, sampling_rate):
        """Calculate T peaks"""
        t_peaks = []
        for s in s_peaks:
            t_start = s + int(0.08 * sampling_rate)
            t_end = min(len(centered_data), s + int(0.4 * sampling_rate))
            if t_end > t_start:
                t_candidates, _ = find_peaks(centered_data[t_start:t_end], 
                                           prominence=0.1 * np.std(centered_data))
                if len(t_candidates) > 0:
                    t_peaks.append(t_start + t_candidates[np.argmax(centered_data[t_start + t_candidates])])
        return t_peaks
    
    def _calculate_pr_interval(self, p_peaks, r_peaks, sampling_rate):
        """Calculate PR interval"""
        if len(p_peaks) > 0 and len(r_peaks) > 0:
            return (r_peaks[-1] - p_peaks[-1]) * 1000 / sampling_rate
        return None
    
    def _calculate_qrs_duration(self, q_peaks, s_peaks, sampling_rate):
        """Calculate QRS duration"""
        if len(q_peaks) > 0 and len(s_peaks) > 0:
            return (s_peaks[-1] - q_peaks[-1]) * 1000 / sampling_rate
        return None
    
    def _calculate_qt_interval(self, q_peaks, t_peaks, sampling_rate):
        """Calculate QT interval"""
        if len(q_peaks) > 0 and len(t_peaks) > 0:
            return (t_peaks[-1] - q_peaks[-1]) * 1000 / sampling_rate
        return None
    
    def _calculate_qtc_interval(self, qt_interval, heart_rate):
        """Calculate QTc interval using Bazett's formula"""
        if qt_interval and heart_rate:
            return qt_interval / np.sqrt(60 / heart_rate)
        return None
    
    def stop_demo_data(self):
        """Stop demo data generation"""
        self._running_demo = False
        # Signal thread to stop and join
        try:
            self._stop_event.set()
            if self.demo_thread and self.demo_thread.is_alive():
                self.demo_thread.join(timeout=1.0)
        except Exception:
            pass
        finally:
            self.demo_thread = None

        # Stop and delete timer
        try:
            if self.demo_timer:
                self.demo_timer.stop()
                self.demo_timer.deleteLater()
                print("⏹️ Demo timer stopped")
        except Exception:
            pass
        finally:
            self.demo_timer = None

        # Clear demo data and plots safely
        try:
            with self._lock:
                for i in range(len(self.ecg_test_page.data)):
                    self.ecg_test_page.data[i] = np.zeros(self.ecg_test_page.buffer_size)
                for line in self.ecg_test_page.data_lines:
                    line.setData(np.zeros(self.ecg_test_page.buffer_size))
            print("🧹 Demo data cleared and plots reset")
        except Exception:
            pass

        # Clear heart rate smoothing data
        self.demo_heart_rates.clear()
        print("✅ Demo mode stopped successfully")

    def _on_page_destroyed(self):
        """Safely stop background activity when the owning page is destroyed."""
        try:
            self._running_demo = False
            self._stop_event.set()
            if self.demo_thread and self.demo_thread.is_alive():
                self.demo_thread.join(timeout=0.5)
        except Exception:
            pass