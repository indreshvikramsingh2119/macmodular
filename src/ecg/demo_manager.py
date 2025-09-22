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
        self.demo_fs = 200  # Demo sampling rate (150 Hz)
        self.demo_thread = None
        self.demo_timer = None
        self.demo_heart_rates = []  # For heart rate smoothing
        
        # Wave speed control variables
        self.current_wave_speed = 12.5  # mm/s
        self.samples_per_second = 200  # Base sampling rate
        self.speed_multiplier = 1.0  # Will be calculated based on wave speed
    
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
            current_gain = self.ecg_test_page.settings_manager.get_wave_gain()

            print("🟢 Demo mode ON - Starting demo data...")
            
            # Update wave speed settings before starting
            self._update_wave_speed_settings()
            
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
        # Path to dummy.csv file - fix the path
        csv_path = os.path.join(os.path.dirname(__file__), 'dummycsv.csv')
        
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
            for lead in lead_columns:
                if lead in self.ecg_test_page.leads:
                    lead_index = self.ecg_test_page.leads.index(lead)
                    # Add first few samples to start
                    initial_samples = min(10, len(df))
                    for i, value in enumerate(df[lead].iloc[:initial_samples]):
                        if i < self.ecg_test_page.buffer_size:
                            self.ecg_test_page.data[lead_index][i] = value
            
            # Start reading data row by row from CSV with wave speed control
            def read_csv_data():
                row_index = 10  # Start from 11th row (first 10 already added)
                while self.ecg_test_page.demo_toggle.isChecked() and row_index < len(df):
                    # Read data for all leads
                    for lead in lead_columns:
                        if lead in self.ecg_test_page.leads:
                            lead_index = self.ecg_test_page.leads.index(lead)
                            value = df[lead].iloc[row_index]
                            
                            # Update data using numpy roll method
                            self.ecg_test_page.data[lead_index] = np.roll(self.ecg_test_page.data[lead_index], -1)
                            self.ecg_test_page.data[lead_index][-1] = value
                    
                    row_index += 1
                    
                    # Loop back to beginning if we reach the end 
                    if row_index >= len(df):
                        row_index = 0
                        print("🔄 Restarting ECG data from beginning...")
                    
                    # Dynamic delay based on wave speed
                    # Slower wave speed = longer delay = slower visual movement
                    base_delay = 0.00667  # 150 samples per second base
                    actual_delay = base_delay / self.speed_multiplier
                    time.sleep(actual_delay)
            
            # Start CSV data reading in background thread
            self.demo_thread = threading.Thread(target=read_csv_data, daemon=True)
            self.demo_thread.start()
            
            # Start timer to update plots with real CSV data
            # Timer interval also affected by wave speed
            self.demo_timer = QTimer()
            self.demo_timer.timeout.connect(self.update_demo_plots)
            
            # Adjust timer interval based on wave speed
            base_interval = 6.67  # 150 FPS base
            timer_interval = int(base_interval / self.speed_multiplier)
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
            self._update_wave_speed_settings()
            # Restart demo with new speed settings
            if self.ecg_test_page.demo_toggle.isChecked():
                self.stop_demo_data()
                self.start_demo_data()
                return
        
        for i, lead in enumerate(self.ecg_test_page.leads):
            if i < len(self.ecg_test_page.data_lines) and i < len(self.ecg_test_page.data):
                lead_data = self.ecg_test_page.data[i]

                # Center baseline
                centered = lead_data - np.mean(lead_data)

                # Apply gain
                gain = self.ecg_test_page.settings_manager.get_wave_gain() / 10.0
                centered *= gain

                # Wave speed → horizontal time scaling
                wave_speed = float(self.ecg_test_page.settings_manager.get_wave_speed())  # 12.5 / 25 / 50
                display_len = 1000  # keep grid resolution constant
                scale = max(0.4, min(2.5, 25.0 / max(1e-6, wave_speed)))  # 12.5→2.0, 25→1.0, 50→0.5 (clamped)
                window_len = max(10, int(display_len * scale))
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
    
    def _calculate_demo_intervals(self):
        """Calculate ECG intervals for dashboard display in demo mode"""
        try:
            # Get Lead II data for interval calculations (Lead II is index 1)
            if len(self.ecg_test_page.data) > 1:
                lead2_data = self.ecg_test_page.data[1]  # Lead II is at index 1
                lead_I_data = self.ecg_test_page.data[0]  # Lead I is at index 0
                lead_aVF_data = self.ecg_test_page.data[5]  # Lead aVF is at index 5
                
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
                        
                        # Update dashboard with demo intervals
                        self.ecg_test_page.dashboard_callback({
                            'Heart_Rate': heart_rate,
                            'PR': pr_interval,
                            'QRS': qrs_duration,
                            'QTc': qtc_interval,
                            'QRS_axis': qrs_axis,
                            'ST': st_segment
                        })
                        
                        # Fixed print statement to handle None values
                        pr_str = f"{pr_interval:.1f}" if pr_interval is not None else "N/A"
                        qrs_str = f"{qrs_duration:.1f}" if qrs_duration is not None else "N/A"
                        hr_str = f"{heart_rate:.1f}" if heart_rate is not None else "N/A"
                        
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
        if hasattr(self, 'demo_timer') and self.demo_timer:
            self.demo_timer.stop()
            print("⏹️ Demo timer stopped")
        
        if hasattr(self, 'demo_thread') and self.demo_thread:
            # Clear demo data - data is a list of numpy arrays
            for i in range(len(self.ecg_test_page.data)):
                self.ecg_test_page.data[i] = np.zeros(self.ecg_test_page.buffer_size)
            
            # Clear all plots
            for line in self.ecg_test_page.data_lines:
                line.setData(np.zeros(self.ecg_test_page.buffer_size))
            
            print("🧹 Demo data cleared and plots reset")
        
        # Clear heart rate smoothing data
        self.demo_heart_rates.clear()
        print("✅ Demo mode stopped successfully")
