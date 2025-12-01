"""
Expanded Lead View - Detailed ECG lead analysis with PQRST labeling and metrics
This module provides an expanded view of individual ECG leads with comprehensive analysis.
"""

import sys
import numpy as np
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QGridLayout,
    QSizePolicy, QScrollArea, QGroupBox, QFormLayout, QLineEdit, QComboBox,
    QMessageBox, QApplication, QDialog, QGraphicsDropShadowEffect, QSlider
)
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtCore import Qt, QTimer
from scipy.signal import find_peaks, butter, filtfilt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class PQRSTAnalyzer:
    """Analyze ECG signal to detect P, Q, R, S, T waves and calculate metrics"""
    
    def __init__(self, sampling_rate=500):
        self.fs = sampling_rate
        self.r_peaks = []
        self.p_peaks = []
        self.q_peaks = []
        self.s_peaks = []
        self.t_peaks = []
        
    def analyze_signal(self, signal):
        """Analyze ECG signal and detect all wave components"""
        try:
            # Filter the signal
            filtered_signal = self._filter_signal(signal)
            
            # Detect R peaks first
            self.r_peaks = self._detect_r_peaks(filtered_signal)
            
            if len(self.r_peaks) > 0:
                # Detect other waves based on R peaks
                self.p_peaks = self._detect_p_waves(filtered_signal, self.r_peaks)
                self.q_peaks = self._detect_q_waves(filtered_signal, self.r_peaks)
                self.s_peaks = self._detect_s_waves(filtered_signal, self.r_peaks)
                self.t_peaks = self._detect_t_waves(filtered_signal, self.r_peaks)
            
            return {
                'r_peaks': self.r_peaks,
                'p_peaks': self.p_peaks,
                'q_peaks': self.q_peaks,
                's_peaks': self.s_peaks,
                't_peaks': self.t_peaks
            }
        except Exception as e:
            print(f"Error in PQRST analysis: {e}")
            return {'r_peaks': [], 'p_peaks': [], 'q_peaks': [], 's_peaks': [], 't_peaks': []}
    
    def _filter_signal(self, signal):
        """Apply bandpass filter to ECG signal"""
        try:
            nyq = 0.5 * self.fs
            low = 0.5 / nyq
            high = 40 / nyq
            b, a = butter(4, [low, high], btype='band')
            return filtfilt(b, a, signal)
        except:
            return signal
    
    def _detect_r_peaks(self, signal):
        """Detect R peaks using Pan-Tompkins algorithm"""
        try:
            # Differentiate
            diff = np.ediff1d(signal)
            # Square
            squared = diff ** 2
            # Moving window integration
            window_size = int(0.15 * self.fs)
            mwa = np.convolve(squared, np.ones(window_size)/window_size, mode='same')
            
            # Find peaks
            threshold = np.mean(mwa) + 0.5 * np.std(mwa)
            min_distance = int(0.2 * self.fs)
            peaks, _ = find_peaks(mwa, height=threshold, distance=min_distance)
            return peaks
        except:
            return []
    
    def _detect_p_waves(self, signal, r_peaks):
        """Detect P waves before R peaks"""
        p_peaks = []
        for r in r_peaks:
            # Look for P wave 120-200ms before R peak for better accuracy
            start = max(0, r - int(0.20 * self.fs))
            end = max(0, r - int(0.12 * self.fs))
            if end > start:
                segment = signal[start:end]
                if len(segment) > 0:
                    p_idx = start + np.argmax(segment)
                    p_peaks.append(p_idx)
        return p_peaks
    
    def _detect_q_waves(self, signal, r_peaks):
        """Detect Q waves (negative deflection before R)"""
        q_peaks = []
        for r in r_peaks:
            # Look for Q wave up to 80ms before R peak
            start = max(0, r - int(0.08 * self.fs))
            end = r
            if end > start:
                segment = signal[start:end]
                if len(segment) > 0:
                    # Q wave is the minimum point between the P wave end and R peak
                    q_idx = start + np.argmin(segment)
                    q_peaks.append(q_idx)
        return q_peaks
    
    def _detect_s_waves(self, signal, r_peaks):
        """Detect S waves (negative deflection after R)"""
        s_peaks = []
        for r in r_peaks:
            # Look for S wave up to 80ms after R peak
            start = r
            end = min(len(signal), r + int(0.08 * self.fs))
            if end > start:
                segment = signal[start:end]
                if len(segment) > 0:
                    s_idx = start + np.argmin(segment)
                    s_peaks.append(s_idx)
        return s_peaks
    
    def _detect_t_waves(self, signal, r_peaks):
        """Detect T waves after S waves"""
        t_peaks = []
        for r in r_peaks:
            # Look for T wave 100-300ms after R peak
            start = min(len(signal), r + int(0.1 * self.fs))
            end = min(len(signal), r + int(0.3 * self.fs))
            if end > start:
                segment = signal[start:end]
                if len(segment) > 0:
                    t_idx = start + np.argmax(segment)
                    t_peaks.append(t_idx)
        return t_peaks

class MetricsCard(QFrame):
    """Individual metric card with color coding and animations"""
    
    def __init__(self, title, value, unit, color="#0984e3", parent=None):
        super().__init__(parent)
        self.title = title
        self.value = value
        self.unit = unit
        self.color = color
        # Base sizes used for responsive scaling - reduced for smaller screens
        self._base_title_pt = 11
        self._base_value_pt = 20
        self._base_status_pt = 10
        
        # Increase card vertical room to prevent value text cropping on macOS/Windows
        self.setMinimumHeight(160)
        self.setMaximumHeight(200)
        self.base_style = f"""
            QFrame {{
                background: white;
                border-radius: 8px;
                border: 2px solid #e0e0e0;
                border-top: 4px solid {self.color};
                margin: 4px;
            }}
        """
        self.hover_style = f"""
            QFrame {{
                background: #f8f9fa;
                border-radius: 8px;
                border: 2px solid {self.color};
                border-top: 4px solid {self.color};
                margin: 4px;
            }}
        """
        self.setStyleSheet(self.base_style)
        
        # Add shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setXOffset(0)
        shadow.setYOffset(2)
        shadow.setColor(QColor(0, 0, 0, 20))
        self.setGraphicsEffect(shadow)
        
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        
        # Title
        title_label = QLabel(self.title)
        title_label.setFont(QFont("Segoe UI", self._base_title_pt, QFont.Bold))
        title_label.setStyleSheet(f"color: {self.color}; border: none; margin: 0; padding: 0; font-weight: bold; background: transparent;")
        title_label.setAlignment(Qt.AlignLeft)
        layout.addWidget(title_label)
        
        # Value
        self.value_label = QLabel(f"{self.value} {self.unit}")
        self.value_label.setFont(QFont("Segoe UI", self._base_value_pt, QFont.Bold))
        self.value_label.setStyleSheet("color: #2c3e50; border: none; margin: 4px 0; font-weight: bold; background: transparent;")
        self.value_label.setAlignment(Qt.AlignLeft)
        # Ensure enough label height for larger fonts to avoid clipping
        self.value_label.setMinimumHeight(40)
        self.value_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.value_label.setWordWrap(True)
        layout.addWidget(self.value_label)
        
        layout.addStretch()
        
        # Status indicator
        self.status_label = QLabel(self.get_status())
        self.status_label.setFont(QFont("Segoe UI", self._base_status_pt, QFont.Bold))
        self.status_label.setStyleSheet(f"color: white; background-color: {self.get_status_color()}; border-radius: 6px; padding: 6px 10px; font-weight: bold;")
        self.status_label.setAlignment(Qt.AlignLeft)
        self.status_label.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        layout.addWidget(self.status_label)
        
    def enterEvent(self, event):
        self.setStyleSheet(self.hover_style)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setStyleSheet(self.base_style)
        super().leaveEvent(event)

    def get_status(self):
        """Get status based on metric value"""
        if self.title == "Heart Rate":
            if 60 <= self.value <= 100: return "NORMAL"
            elif self.value < 60: return "BRADYCARDIA"
            else: return "TACHYCARDIA"
        elif self.title == "PR Interval":
            if 120 <= self.value <= 200: return "NORMAL"
            elif self.value < 120: return "SHORT"
            else: return "PROLONGED"
        elif self.title == "QRS Duration":
            if 80 <= self.value <= 120: return "NORMAL"
            elif self.value < 80: return "NARROW"
            else: return "WIDE"
        elif self.title == "QTc Interval":
            if 350 <= self.value <= 450: return "NORMAL"
            elif self.value < 350: return "SHORT"
            else: return "PROLONGED"
        else:
            return "MEASURED"
    
    def get_status_color(self):
        """Get color based on status"""
        status = self.get_status()
        if status == "NORMAL": return "#2ecc71"  # Green
        if status in ["BRADYCARDIA", "TACHYCARDIA", "PROLONGED", "WIDE"]: return "#e74c3c"  # Red
        if status in ["SHORT", "NARROW"]: return "#f39c12" # Orange
        return "#3498db" # Blue
    
    def update_value(self, new_value):
        """Update the metric value"""
        self.value = new_value
        self.value_label.setText(f"{self.value} {self.unit}")
        self.status_label.setText(self.get_status())
        self.status_label.setStyleSheet(f"color: white; background-color: {self.get_status_color()}; border-radius: 4px; padding: 2px 6px;")

    def set_scale(self, scale: float) -> None:
        """Scale fonts responsively based on a scale factor.

        The scale is typically derived from current window size vs. baseline.
        """
        scale = max(0.7, min(1.6, scale))
        self.value_label.setFont(QFont("Segoe UI", int(self._base_value_pt * scale), QFont.Bold))
        self.status_label.setFont(QFont("Segoe UI", int(self._base_status_pt * scale), QFont.Bold))
        # Title is the first child label in layout
        if isinstance(self.layout().itemAt(0).widget(), QLabel):
            self.layout().itemAt(0).widget().setFont(QFont("Segoe UI", int(self._base_title_pt * scale), QFont.Bold))

class ArrhythmiaDetector:
    """Detect various types of arrhythmias from ECG data"""
    
    def __init__(self, sampling_rate=500):
        self.fs = sampling_rate
    
    def detect_arrhythmias(self, signal, r_peaks):
        """Detect various arrhythmias"""
        arrhythmias = []
        
        if len(r_peaks) < 3:
            return ["Insufficient data for arrhythmia detection."]
        
        # Calculate RR intervals
        rr_intervals = np.diff(r_peaks) / self.fs * 1000  # in ms
        
        # Check for specific arrhythmias first
        if self._is_atrial_fibrillation(signal, r_peaks):
            arrhythmias.append("Possible Atrial Fibrillation")
        if self._is_ventricular_tachycardia(rr_intervals):
            arrhythmias.append("Possible Ventricular Tachycardia")
        if self._is_premature_ventricular_contractions(signal, r_peaks):
            arrhythmias.append("Premature Ventricular Contractions Detected")
        
        # If no major arrhythmia, check rate-based conditions
        if not arrhythmias:
            if self._is_bradycardia(rr_intervals):
                arrhythmias.append("Sinus Bradycardia")
            elif self._is_tachycardia(rr_intervals):
                arrhythmias.append("Sinus Tachycardia")

        # If still nothing, check for NSR
        if not arrhythmias and self._is_normal_sinus_rhythm(rr_intervals):
            return ["Normal Sinus Rhythm"]
            
        return arrhythmias if arrhythmias else ["Unspecified Irregular Rhythm"]
    
    def detect_arrhythmias_with_probabilities(self, signal, r_peaks, window_size=2.0):
        """
        Detect arrhythmias with probability scores over time windows
        Returns a dictionary with time windows and probability scores for each arrhythmia type
        """
        if len(r_peaks) < 3:
            return {}
        
        # Calculate RR intervals
        rr_intervals = np.diff(r_peaks) / self.fs * 1000  # in ms
        time_points = r_peaks[:-1] / self.fs  # Time points for each RR interval
        
        # Initialize heat map data structure
        arrhythmia_types = [
            "Normal Sinus Rhythm",
            "Atrial Fibrillation",
            "Ventricular Tachycardia",
            "Premature Ventricular Contractions",
            "Sinus Bradycardia",
            "Sinus Tachycardia",
            "Irregular Rhythm"
        ]
        
        heat_map_data = {arr_type: [] for arr_type in arrhythmia_types}
        
        # Analyze in sliding windows
        window_samples = int(window_size * self.fs)
        num_windows = max(1, len(signal) // window_samples)
        
        for i in range(num_windows):
            start_idx = i * window_samples
            end_idx = min((i + 1) * window_samples, len(signal))
            window_signal = signal[start_idx:end_idx]
            window_time = (start_idx + end_idx) / (2 * self.fs)
            
            # Find R peaks in this window
            window_r_peaks = [r for r in r_peaks if start_idx <= r < end_idx]
            
            if len(window_r_peaks) < 2:
                # Insufficient data - assign low probabilities
                for arr_type in arrhythmia_types:
                    heat_map_data[arr_type].append((window_time, 0.0))
                continue
            
            window_rr = np.diff(window_r_peaks) / self.fs * 1000
            
            # Calculate probabilities for each arrhythmia type
            prob_nsr = self._prob_normal_sinus_rhythm(window_rr)
            prob_afib = self._prob_atrial_fibrillation(window_signal, window_r_peaks)
            prob_vt = self._prob_ventricular_tachycardia(window_rr)
            prob_pvc = self._prob_premature_ventricular_contractions(window_signal, window_r_peaks)
            prob_brady = self._prob_bradycardia(window_rr)
            prob_tachy = self._prob_tachycardia(window_rr)
            
            # Normalize probabilities so they sum to 1.0
            probs = [prob_nsr, prob_afib, prob_vt, prob_pvc, prob_brady, prob_tachy]
            total = sum(probs)
            if total > 0:
                probs = [p / total for p in probs]
            else:
                probs = [1.0/len(probs)] * len(probs)  # Equal probability if all zero
            
            # Store probabilities
            heat_map_data["Normal Sinus Rhythm"].append((window_time, probs[0]))
            heat_map_data["Atrial Fibrillation"].append((window_time, probs[1]))
            heat_map_data["Ventricular Tachycardia"].append((window_time, probs[2]))
            heat_map_data["Premature Ventricular Contractions"].append((window_time, probs[3]))
            heat_map_data["Sinus Bradycardia"].append((window_time, probs[4]))
            heat_map_data["Sinus Tachycardia"].append((window_time, probs[5]))
            heat_map_data["Irregular Rhythm"].append((window_time, 1.0 - prob_nsr))
        
        return heat_map_data
    
    def _prob_normal_sinus_rhythm(self, rr_intervals):
        """Calculate probability of normal sinus rhythm"""
        if len(rr_intervals) < 3:
            return 0.0
        mean_hr = 60000 / np.mean(rr_intervals)
        std_rr = np.std(rr_intervals)
        if 60 <= mean_hr <= 100 and std_rr < 120:
            return 0.9
        elif 50 <= mean_hr <= 110 and std_rr < 150:
            return 0.5
        return 0.1
    
    def _prob_atrial_fibrillation(self, signal, r_peaks):
        """Calculate probability of atrial fibrillation"""
        if len(r_peaks) < 10:
            return 0.0
        rr_intervals = np.diff(r_peaks)
        cv = np.std(rr_intervals) / np.mean(rr_intervals) if np.mean(rr_intervals) > 0 else 0
        if cv > 0.15:
            return min(0.95, 0.5 + (cv - 0.15) * 2.0)
        return max(0.0, 0.5 - cv * 2.0)
    
    def _prob_ventricular_tachycardia(self, rr_intervals):
        """Calculate probability of ventricular tachycardia"""
        if len(rr_intervals) < 3:
            return 0.0
        mean_hr = 60000 / np.mean(rr_intervals)
        std_rr = np.std(rr_intervals)
        if mean_hr > 120 and std_rr < 40:
            return min(0.95, 0.7 + (mean_hr - 120) / 200)
        return 0.1
    
    def _prob_premature_ventricular_contractions(self, signal, r_peaks):
        """Calculate probability of PVCs"""
        if len(r_peaks) < 5:
            return 0.0
        rr_intervals = np.diff(r_peaks) / self.fs
        mean_rr = np.mean(rr_intervals)
        pvc_count = 0
        for i in range(len(rr_intervals)):
            if rr_intervals[i] < 0.8 * mean_rr:
                if i + 1 < len(rr_intervals) and rr_intervals[i+1] > 1.2 * mean_rr:
                    pvc_count += 1
        return min(0.95, pvc_count / len(rr_intervals) * 2.0)
    
    def _prob_bradycardia(self, rr_intervals):
        """Calculate probability of bradycardia"""
        if len(rr_intervals) < 3:
            return 0.0
        mean_hr = 60000 / np.mean(rr_intervals)
        if mean_hr < 60:
            return min(0.95, 0.5 + (60 - mean_hr) / 60)
        return 0.1
    
    def _prob_tachycardia(self, rr_intervals):
        """Calculate probability of tachycardia"""
        if len(rr_intervals) < 3:
            return 0.0
        mean_hr = 60000 / np.mean(rr_intervals)
        if mean_hr > 100:
            return min(0.95, 0.5 + (mean_hr - 100) / 200)
        return 0.1
    
    def _is_normal_sinus_rhythm(self, rr_intervals):
        """Check if rhythm is normal sinus rhythm"""
        if len(rr_intervals) < 3: return False
        mean_hr = 60000 / np.mean(rr_intervals)
        std_rr = np.std(rr_intervals)
        return 60 <= mean_hr <= 100 and std_rr < 120 # Variation less than 120ms
    
    def _is_atrial_fibrillation(self, signal, r_peaks):
        """Detect atrial fibrillation"""
        if len(r_peaks) < 10: return False
        rr_intervals = np.diff(r_peaks)
        # AF is characterized by highly irregular RR intervals and no clear P waves
        cv = np.std(rr_intervals) / np.mean(rr_intervals) if np.mean(rr_intervals) > 0 else 0
        return cv > 0.15
    
    def _is_ventricular_tachycardia(self, rr_intervals):
        """Detect ventricular tachycardia"""
        if len(rr_intervals) < 3: return False
        mean_hr = 60000 / np.mean(rr_intervals)
        # VT is a run of 3 or more consecutive PVCs, typically wide QRS and fast rate
        return mean_hr > 120 and np.std(rr_intervals) < 40 # Fast and regular
    
    def _is_bradycardia(self, rr_intervals):
        """Detect bradycardia"""
        if len(rr_intervals) < 3: return False
        mean_hr = 60000 / np.mean(rr_intervals)
        return mean_hr < 60
    
    def _is_tachycardia(self, rr_intervals):
        """Detect tachycardia"""
        if len(rr_intervals) < 3: return False
        mean_hr = 60000 / np.mean(rr_intervals)
        return mean_hr > 100
    
    def _is_premature_ventricular_contractions(self, signal, r_peaks):
        """Detect PVCs"""
        if len(r_peaks) < 5: return False
        rr_intervals = np.diff(r_peaks) / self.fs
        mean_rr = np.mean(rr_intervals)
        for i in range(len(rr_intervals)):
            if rr_intervals[i] < 0.8 * mean_rr: # A beat is premature
                # Check for compensatory pause
                if i + 1 < len(rr_intervals) and rr_intervals[i+1] > 1.2 * mean_rr:
                    return True
        return False

class ExpandedLeadView(QDialog):
    """Expanded view for individual ECG leads with detailed analysis"""
    
    def __init__(self, lead_name, ecg_data, sampling_rate=500, parent=None):
        super().__init__(parent)
        self.lead_name = lead_name
        self.ecg_data = np.array(ecg_data) if ecg_data is not None and len(ecg_data) > 0 else np.array([])
        self.sampling_rate = sampling_rate
        # Keep a reference to parent ECG page for shared metrics
        self._parent = parent
        self.analyzer = PQRSTAnalyzer(sampling_rate)
        self.arrhythmia_detector = ArrhythmiaDetector(sampling_rate)
        # Display gain to make waves visually smaller (half-height)
        self.display_gain = 0.5

        self.amplification = 1.0  # Amplification factor
        self.min_amplification = 0.1  # Minimum 10% of original
        self.max_amplification = 10.0  # Maximum 10x amplification

        # Store original y-axis limits (will be set after first plot)
        self.fixed_ylim = None

        # Store the baseline (mean) of the signal for proper zooming
        self.signal_baseline = 0.0

        # Store detected arrhythmia events as (time_seconds, label)
        self.arrhythmia_events = []
        
        # Heat map + history view state
        self.heatmap_overlay = None
        self.heatmap_time_axis = None
        self.heatmap_window_step = 1.0

        # History view widgets (initialized later)
        self.history_slider = None
        self.history_slider_label = None
        self.history_slider_frame = None
        self.view_window_duration = 10.0  # seconds visible at once
        self.view_window_offset = 0.0
        self.manual_view = False
        self.history_slider_active = False

        # Live data update
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_live_data)
        self.is_live = False
        
        self.setWindowTitle(f"Detailed Analysis - {lead_name}")
        # Make dialog responsive from ~13\" laptops up to 27\" monitors
        try:
            from PyQt5.QtWidgets import QApplication
            screen = QApplication.primaryScreen()
            if screen is not None:
                geom = screen.availableGeometry()
                # Use 80% of screen size for initial window
                w = int(geom.width() * 0.8)
                h = int(geom.height() * 0.8)
                self.resize(max(960, w), max(600, h))
            else:
                # Fallback if screen info not available
                self.resize(1280, 720)
        except Exception:
            self.resize(1280, 720)
        # Reasonable minimum to keep layout usable on small screens
        self.setMinimumSize(960, 600)
        self.setStyleSheet("""
            QDialog {
                background-color: #f0f2f5;
            }
            QScrollArea {
                border: none;
            }
        """)
        
        self.setup_ui()
        self.analyze_ecg()
        
        # Start live updates if parent is available (hardware data)
        if parent is not None:
            self.start_live_mode()

            # Initialize button states based on parent acquisition status
            if hasattr(self, 'expanded_start_btn'):
                self.update_button_states()
    
    def setup_ui(self):
        """Setup the user interface"""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Header
        self.create_header(main_layout)
        
        # Main content area with proper proportions
        content_layout = QHBoxLayout()
        content_layout.setSpacing(10)
        
        # Left side - ECG plot (70% of width)
        self.create_ecg_plot(content_layout)
        
        # Right side - Metrics (30% of width)
        self.create_metrics_panel(content_layout)
        
        main_layout.addLayout(content_layout, 1)
        
        # Bottom - Arrhythmia analysis
        self.create_arrhythmia_panel(main_layout)
    
    def create_header(self, parent_layout):
        """Create the header section"""
        header_frame = QFrame()
        header_frame.setFixedHeight(60)
        header_frame.setStyleSheet("""
            QFrame {
                background: white;
                border-radius: 8px;
                padding: 10px;
                border: 1px solid #e0e0e0;
            }
        """)
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(15, 0, 5, 0)
        
        title_label = QLabel(f"Lead {self.lead_name} - Detailed Waveform Analysis")
        title_label.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title_label.setStyleSheet("color: #2c3e50; border: none; background: transparent;")
        title_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        title_label.setWordWrap(True)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.setMinimumHeight(35)
        close_btn.setStyleSheet("""
            QPushButton {
                background: #34495e; color: white; border-radius: 5px;
                padding: 8px 18px; font-weight: bold; font-size: 10pt;
            }
            QPushButton:hover { background: #5d6d7e; }
        """)
        close_btn.clicked.connect(self.close)
        header_layout.addWidget(close_btn)
        
        parent_layout.addWidget(header_frame)

    # Mouse wheel event for amplification

    def wheelEvent(self, event):
        """Handle mouse wheel scrolling for amplification"""
        try:
            # Get scroll direction
            delta = event.angleDelta().y()
            
            # Calculate amplification change
            if delta > 0:
                # Scroll up = amplify (zoom in)
                self.amplification *= 1.1
            else:
                # Scroll down = deamplify (zoom out)
                self.amplification /= 1.1
            
            # Clamp amplification to limits
            self.amplification = max(self.min_amplification, 
                                    min(self.max_amplification, self.amplification))
            
            # Update the plot
            self.update_plot()
            
            # Update amplification display if it exists
            if hasattr(self, 'amp_label'):
                self.amp_label.setText(f"{self.amplification:.2f}x")
            
            event.accept()
        except Exception as e:
            print(f"Error in wheel event: {e}")
    
    def create_ecg_plot(self, parent_layout):
        """Create the ECG plot area"""
        plot_frame = QFrame()
        plot_frame.setStyleSheet("""
            QFrame {
                background: white;
                border-radius: 8px;
                border: 1px solid #e0e0e0;
            }
        """)
        plot_layout = QVBoxLayout(plot_frame)
        plot_layout.setContentsMargins(8, 8, 8, 8)
        
        # Create matplotlib figure with better sizing
        # Use a moderate DPI, but allow canvas to expand with layout
        self.fig = Figure(figsize=(10, 6), facecolor='white', dpi=110)
        self.ax = self.fig.add_subplot(111)
        self.fig.tight_layout(pad=2.0)
        
        self.setup_ecg_plot()
        
        self.canvas = FigureCanvas(self.fig)
        # Let the canvas grow/shrink with the window instead of forcing a large minimum
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.canvas.setMinimumSize(500, 320)
        plot_layout.addWidget(self.canvas)

        # --- AMPLIFICATION CONTROLS ---
        control_frame = QFrame()
        control_frame.setStyleSheet("background: transparent; border: none;")
        control_layout = QHBoxLayout(control_frame)
        control_layout.setContentsMargins(10, 5, 10, 5)
        control_layout.setSpacing(10)
        
        # Amplification label
        amp_title = QLabel("Amplification:")
        amp_title.setStyleSheet("""
            color: #2c3e50; 
            font-weight: bold; 
            font-size: 11pt;
            background: transparent;
            border: none;
        """)
        control_layout.addWidget(amp_title)
        
        # - Button (Decrease amplification)
        minus_btn = QPushButton("−")
        minus_btn.setMinimumSize(40, 35)
        minus_btn.setMaximumSize(40, 35)
        minus_btn.setStyleSheet("""
            QPushButton {
                background: #3498db; 
                color: white; 
                border-radius: 6px;
                font-weight: bold; 
                font-size: 18pt;
                border: 2px solid #2980b9;
            }
            QPushButton:hover { 
                background: #2980b9; 
            }
            QPushButton:pressed {
                background: #21618c;
            }
        """)
        minus_btn.clicked.connect(self.decrease_amplification)
        control_layout.addWidget(minus_btn)
        
        # Amplification display
        self.amp_label = QLabel(f"{self.amplification:.2f}x")
        self.amp_label.setMinimumWidth(60)
        self.amp_label.setAlignment(Qt.AlignCenter)
        self.amp_label.setStyleSheet("""
            color: #2c3e50; 
            font-weight: bold; 
            font-size: 12pt;
            background: #f8f9fa;
            border: 2px solid #dee2e6;
            border-radius: 6px;
            padding: 5px;
        """)
        control_layout.addWidget(self.amp_label)
        
        # + Button (Increase amplification)
        plus_btn = QPushButton("+")
        plus_btn.setMinimumSize(40, 35)
        plus_btn.setMaximumSize(40, 35)
        plus_btn.setStyleSheet("""
            QPushButton {
                background: #3498db; 
                color: white; 
                border-radius: 6px;
                font-weight: bold; 
                font-size: 18pt;
                border: 2px solid #2980b9;
            }
            QPushButton:hover { 
                background: #2980b9; 
            }
            QPushButton:pressed {
                background: #21618c;
            }
        """)
        plus_btn.clicked.connect(self.increase_amplification)
        control_layout.addWidget(plus_btn)
        
        # Reset Button
        reset_btn = QPushButton("Reset")
        reset_btn.setMinimumSize(60, 35)
        reset_btn.setStyleSheet("""
            QPushButton {
                background: #95a5a6; 
                color: white; 
                border-radius: 6px;
                padding: 5px 10px;
                font-weight: bold; 
                font-size: 10pt;
                border: 2px solid #7f8c8d;
            }
            QPushButton:hover { 
                background: #7f8c8d; 
            }
        """)
        reset_btn.clicked.connect(self.reset_amplification)
        control_layout.addWidget(reset_btn)
        
        # Info label
        info_label = QLabel("💡 Use mouse scroll to zoom")
        info_label.setStyleSheet("""
            color: #7f8c8d; 
            font-size: 9pt;
            font-style: italic;
            background: transparent;
            border: none;
        """)
        control_layout.addWidget(info_label)
        
        control_layout.addStretch()

        startstop_layout = QHBoxLayout()
        startstop_layout.addStretch()
        
        # Use the same green button style as the main ECG test page for visual consistency
        green_btn_style = """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #4CAF50, stop:1 #45a049);
                color: white;
                border: 2px solid #4CAF50;
                border-radius: 6px;
                padding: 4px 12px;
                font-size: 10px;
                font-weight: bold;
                text-align: center;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #45a049, stop:1 #4CAF50);
                border: 2px solid #45a049;
                color: white;
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #3d8b40, stop:1 #357a38);
                border: 2px solid #3d8b40;
                color: white;
            }
            QPushButton:disabled {
                background: #6c757d;
                border: 2px solid #6c757d;
                color: #eeeeee;
            }
        """

        # Start Button for Expanded Lead View
        self.expanded_start_btn = QPushButton("Start")
        self.expanded_start_btn.setMinimumSize(90, 34)
        self.expanded_start_btn.setMaximumHeight(36)
        self.expanded_start_btn.setStyleSheet(green_btn_style)
        self.expanded_start_btn.clicked.connect(self.start_parent_acquisition)
        startstop_layout.addWidget(self.expanded_start_btn)
        
        # Stop Button for Expanded Lead View (same style and size)
        self.expanded_stop_btn = QPushButton("Stop")
        self.expanded_stop_btn.setMinimumSize(90, 34)
        self.expanded_stop_btn.setMaximumHeight(36)
        self.expanded_stop_btn.setStyleSheet(green_btn_style)
        self.expanded_stop_btn.clicked.connect(self.stop_parent_acquisition)
        startstop_layout.addWidget(self.expanded_stop_btn)
        
        plot_layout.addLayout(startstop_layout)
        
        # History slider container (initially hidden until acquisition stops)
        history_frame = QFrame()
        history_frame.setStyleSheet("""
            QFrame {
                background: transparent;
                border: none;
            }
        """)
        history_layout = QHBoxLayout(history_frame)
        history_layout.setContentsMargins(0, 5, 0, 5)
        history_layout.setSpacing(10)

        history_label = QLabel("History View:")
        history_label.setStyleSheet("color: #2c3e50; font-weight: bold; font-size: 11pt;")
        history_layout.addWidget(history_label)

        slider = QSlider(Qt.Horizontal)
        slider.setRange(0, 0)
        slider.setSingleStep(10)
        slider.setPageStep(100)
        slider.setTickPosition(QSlider.TicksBelow)
        slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #bbb;
                background: #f5f5f5;
                height: 6px;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #3498db;
                border: 1px solid #1f78b4;
                width: 14px;
                margin: -6px 0;
                border-radius: 7px;
            }
        """)
        slider.valueChanged.connect(self.on_history_slider_changed)
        history_layout.addWidget(slider, 1)

        history_value = QLabel("LIVE")
        history_value.setStyleSheet("color: #7f8c8d; font-size: 10pt; font-weight: bold;")
        history_layout.addWidget(history_value)

        history_frame.setVisible(False)
        plot_layout.addWidget(history_frame)

        self.history_slider = slider
        self.history_slider_label = history_value
        self.history_slider_frame = history_frame

        plot_layout.addWidget(control_frame)
        
        parent_layout.addWidget(plot_frame, 7) # Plot takes ~70% of horizontal space

    # Amplification functions

    def increase_amplification(self):
        """Increase amplification by 20%"""
        self.amplification *= 1.2
        self.amplification = min(self.max_amplification, self.amplification)
        if hasattr(self, 'amp_label'):
            self.amp_label.setText(f"{self.amplification:.2f}x")
        self.update_plot()
        print(f"✅ Amplification increased to {self.amplification:.2f}x")

    def decrease_amplification(self):
        """Decrease amplification by 20%"""
        self.amplification /= 1.2
        self.amplification = max(self.min_amplification, self.amplification)
        if hasattr(self, 'amp_label'):
            self.amp_label.setText(f"{self.amplification:.2f}x")
        self.update_plot()
        print(f"✅ Amplification decreased to {self.amplification:.2f}x")

    def reset_amplification(self):
        """Reset amplification to default (1.0x)"""
        self.amplification = 1.0
        if hasattr(self, 'amp_label'):
            self.amp_label.setText(f"{self.amplification:.2f}x")
        self.update_plot()
        print("✅ Amplification reset to 1.00x")
    
    def setup_ecg_plot(self):
        """Setup the ECG plot with proper styling"""
        if len(self.ecg_data) == 0:
            self.ax.text(0.5, 0.5, 'No ECG Data Available', 
                        transform=self.ax.transAxes, ha='center', va='center',
                        fontsize=16, color='gray')
            return
        
        time = np.arange(len(self.ecg_data)) / self.sampling_rate
        # Plot at 1.0x to establish baseline
        scaled = self.ecg_data * self.display_gain * 1.0  # Use 1.0x for baseline
        
        # Calculate and store the baseline (mean) for proper zooming
        self.signal_baseline = np.mean(scaled)
        
        self.ax.plot(time, scaled, color='#0984e3', linewidth=1.0, label='ECG Signal')
        
        # self.ax.set_xlabel('Time (seconds)', fontsize=14, fontweight='bold', color='#34495e')
        self.ax.set_ylabel('Amplitude (mV)', fontsize=14, fontweight='bold', color='#34495e')
        self.ax.set_title(f'Lead {self.lead_name} - PQRST Analysis', fontsize=18, fontweight='bold', color='#2c3e50')
        
        self.ax.grid(True, which='both', linestyle='--', linewidth=0.5, color='#bdc3c7')
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)
        
        self.ax.set_xlim(0, max(time) if len(time) > 0 else 1)
        
        # Store fixed y-limits based on original data (1.0x amplification)
        if len(self.ecg_data) > 0:
            y_margin = (np.max(scaled) - np.min(scaled)) * 0.1
            y_min = np.min(scaled) - y_margin
            y_max = np.max(scaled) + y_margin
            self.fixed_ylim = (y_min, y_max)
            self.ax.set_ylim(y_min, y_max)

        if hasattr(self, 'canvas'):
            self.canvas.draw()
    
    def create_metrics_panel(self, parent_layout):
        """Create the metrics panel"""
        # A container frame for the entire right-side panel
        metrics_frame = QFrame()
        metrics_frame.setStyleSheet("""
            QFrame {
                background: white;
                border-radius: 8px;
                border: 1px solid #e0e0e0;
            }
        """)
        # Let this panel be responsive; width controlled by stretch factors
        metrics_frame.setMinimumWidth(300)
        metrics_frame.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        
        # The scroll area allows content to overflow vertically
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea { 
                background: transparent; 
                border: none; 
            }
            QScrollBar:vertical {
                border: none;
                background: #f0f2f5;
                width: 8px;
                margin: 0px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #bdc3c7;
                min-height: 25px;
                border-radius: 4px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

        # A widget that will sit inside the scroll area and hold the layout
        metrics_container_widget = QWidget()
        metrics_container_widget.setStyleSheet("background: transparent;")

        # A vertical layout for a single column of cards
        self.metrics_vbox = QVBoxLayout(metrics_container_widget)
        self.metrics_vbox.setContentsMargins(10, 10, 5, 10)
        self.metrics_vbox.setSpacing(12)

        self.metrics_cards = {}
        self.create_metrics_cards()

        scroll_area.setWidget(metrics_container_widget)

        # The main layout for the right panel
        main_metrics_layout = QVBoxLayout(metrics_frame)
        main_metrics_layout.setContentsMargins(0, 0, 0, 0)
        main_metrics_layout.addWidget(scroll_area)

        parent_layout.addWidget(metrics_frame, 3) # Metrics panel takes 30% of horizontal space
    
    def create_metrics_cards(self):
        """Create individual metric cards"""
        # Metrics displayed in expanded view (Heart Rate is not shown here)
        metrics = [
            ("RR Interval", 0, "ms", "#2980b9"),
            ("PR Interval", 0, "ms", "#8e44ad"),
            ("QRS Duration", 0, "ms", "#27ae60"),
            ("P Duration", 0, "ms", "#16a085"),
        ]
        
        for i, (title, value, unit, color) in enumerate(metrics):
            card = MetricsCard(title, value, unit, color)
            self.metrics_cards[title.lower().replace(" ", "_")] = card
            self.metrics_vbox.addWidget(card)
        
        # Add a stretch at the end
        self.metrics_vbox.addStretch(1)
        
        # Initialize with some default values for testing (only for visible metrics)
        self.update_metric('rr_interval', 0)
        self.update_metric('pr_interval', 0)
        self.update_metric('qrs_duration', 0)
        self.update_metric('p_duration', 0)
    
    def start_live_mode(self):
        """Start live data updates"""
        self.is_live = True
        self.timer.start(100)  # Update every 100ms

    def resizeEvent(self, event):
        """Respond to window resizing by scaling fonts and components."""
        try:
            # Baseline matches initial size above
            base_w, base_h = 1400.0, 900.0
            cur_w, cur_h = max(1, self.width()), max(1, self.height())
            scale = min(cur_w / base_w, cur_h / base_h)

            # Scale metric cards
            for card in getattr(self, 'metrics_cards', {}).values():
                if hasattr(card, 'set_scale'):
                    card.set_scale(scale)
        except Exception:
            pass
        super().resizeEvent(event)
    
    def stop_live_mode(self):
        """Stop live data updates"""
        self.is_live = False
        self.timer.stop()
    
    def update_live_data(self):
        """Update ECG data from parent (hardware)"""
        if not self.is_live or not hasattr(self, 'parent') or self.parent() is None:
            return
        
        try:
            # Get current data from parent ECG test page
            parent = self.parent()
            # Align sampling rate with parent so HR/RR match dashboard
            try:
                if hasattr(parent, 'sampler') and getattr(parent.sampler, 'sampling_rate', 0):
                    self.sampling_rate = float(parent.sampler.sampling_rate)
                    self.analyzer.fs = self.sampling_rate
                    self.arrhythmia_detector.fs = self.sampling_rate
                elif hasattr(parent, 'sampling_rate') and parent.sampling_rate:
                    self.sampling_rate = float(parent.sampling_rate)
                    self.analyzer.fs = self.sampling_rate
                    self.arrhythmia_detector.fs = self.sampling_rate
            except Exception:
                pass
            if hasattr(parent, 'data') and len(parent.data) > 0:
                # Find the lead index for this lead
                lead_index = self.get_lead_index()
                if lead_index is not None and lead_index < len(parent.data):
                    new_data = parent.data[lead_index]
                    if len(new_data) > 0:
                        self.ecg_data = np.array(new_data)
                        if not self.manual_view:
                            total_duration = len(self.ecg_data) / max(1.0, self.sampling_rate)
                            self.view_window_offset = max(0.0, total_duration - self.view_window_duration)
                        self.analyze_ecg()
                        self.update_plot()
                        self.update_history_slider()

                        # Update button states to reflect parent's status
                        if hasattr(self, 'expanded_start_btn'):
                            self.update_button_states()

        except Exception as e:
            print(f"Error updating live data: {e}")
    
    def get_lead_index(self):
        """Get the lead index for this lead name"""
        lead_mapping = {
            'I': 0, 'II': 1, 'III': 2, 'aVR': 3, 'aVL': 4, 'aVF': 5,
            'V1': 6, 'V2': 7, 'V3': 8, 'V4': 9, 'V5': 10, 'V6': 11
        }
        return lead_mapping.get(self.lead_name)
    
    def update_plot(self):
        """Update the ECG plot with new data"""
        if len(self.ecg_data) == 0:
            return
        
        try:
            total_samples = len(self.ecg_data)
            window_samples = max(1, int(self.view_window_duration * self.sampling_rate))
            if window_samples > total_samples:
                window_samples = total_samples

            total_duration = total_samples / max(1.0, self.sampling_rate)
            max_offset = max(0.0, total_duration - self.view_window_duration)
            if not self.manual_view:
                self.view_window_offset = max_offset
            else:
                self.view_window_offset = min(self.view_window_offset, max_offset)

            start_idx = int(self.view_window_offset * self.sampling_rate)
            end_idx = min(total_samples, start_idx + window_samples)
            if end_idx - start_idx <= 1:
                return

            window_signal = self.ecg_data[start_idx:end_idx]
            time = np.arange(start_idx, end_idx) / self.sampling_rate
            base_scaled = window_signal * self.display_gain
            self.signal_baseline = np.mean(base_scaled)
            scaled = self.signal_baseline + (base_scaled - self.signal_baseline) * self.amplification

            # Determine y-limits once based on entire dataset for consistent scaling
            if self.fixed_ylim is None and len(self.ecg_data) > 0:
                baseline_full = self.ecg_data * self.display_gain
                y_margin = (np.max(baseline_full) - np.min(baseline_full)) * 0.15 if np.max(baseline_full) != np.min(baseline_full) else 1.0
                y_min = np.min(baseline_full) - y_margin
                y_max = np.max(baseline_full) + y_margin
                self.fixed_ylim = (y_min, y_max)

            self.ax.clear()

            # Heat map overlay behind waveform
            if (
                self.heatmap_overlay is not None
                and self.heatmap_time_axis is not None
                and len(self.heatmap_time_axis) > 0
                and self.fixed_ylim is not None
            ):
                window_half = max(0.001, self.heatmap_window_step / 2.0)
                extent = [
                    self.heatmap_time_axis[0] - window_half,
                    self.heatmap_time_axis[-1] + window_half,
                    self.fixed_ylim[0],
                    self.fixed_ylim[1]
                ]
                self.ax.imshow(
                    self.heatmap_overlay,
                    extent=extent,
                    aspect='auto',
                    origin='lower',
                    interpolation='nearest',
                    zorder=0,
                )

            self.ax.plot(time, scaled, color='#0984e3', linewidth=1.0, label='ECG Signal', zorder=1)

            # Overlay vertical markers at detected arrhythmia event times within the visible window
            if hasattr(self, "arrhythmia_events") and self.arrhythmia_events:
                t_start, t_end = time[0], time[-1]
                for evt_time, evt_label in self.arrhythmia_events:
                    if t_start <= evt_time <= t_end:
                        # Vertical dashed red line
                        self.ax.axvline(evt_time, color="#e74c3c", linestyle="--", linewidth=1.0, alpha=0.9, zorder=2)
                        # Small label at the top of the plot
                        try:
                            ylim = self.fixed_ylim if self.fixed_ylim is not None else self.ax.get_ylim()
                            y_top = ylim[1]
                            self.ax.text(
                                evt_time,
                                y_top,
                                "★",
                                color="#e74c3c",
                                fontsize=10,
                                fontweight="bold",
                                ha="center",
                                va="bottom",
                                zorder=3,
                            )
                        except Exception:
                            pass

            # Remove explicit X-axis label ("Time (seconds)") to match dashboard style
            self.ax.set_ylabel('Amplitude (mV)', fontsize=14, fontweight='bold', color='#34495e')
            amp_text = f" (Zoom: {self.amplification:.2f}x)" if self.amplification != 1.0 else ""
            self.ax.set_title(
                f'Lead {self.lead_name} - Live PQRST Analysis{amp_text}',
                fontsize=18,
                fontweight='bold',
                color='#2c3e50'
            )

            self.ax.grid(True, which='both', linestyle='--', linewidth=0.5, color='#bdc3c7')
            self.ax.spines['top'].set_visible(False)
            self.ax.spines['right'].set_visible(False)
            self.ax.set_xlim(time[0], time[-1])

            if self.fixed_ylim is not None:
                self.ax.set_ylim(self.fixed_ylim[0], self.fixed_ylim[1])

            self.canvas.draw()
        except Exception as e:
            print(f"Error updating plot: {e}")
    
    def closeEvent(self, event):
        """Handle window close event"""
        self.stop_live_mode()
        event.accept()

    # Start/Stop Acquisition from Expanded Lead View

    def start_parent_acquisition(self):
        """Start serial data acquisition from parent ECG test page"""
        try:
            parent = self.parent()
            
            # Check if demo mode is active - prevent starting if it is
            if parent and hasattr(parent, 'demo_toggle') and parent.demo_toggle.isChecked():
                QMessageBox.warning(self, "Demo Mode Active", 
                    "Cannot start serial acquisition while Demo mode is ON.\n\n"
                    "Please turn off Demo mode first to use real serial data.")
                print("Cannot start acquisition - Demo mode is active")
                return
            
            if parent and hasattr(parent, 'start_acquisition'):
                print("Starting acquisition from expanded lead view...")
                parent.start_acquisition()
                
                # Update button states
                self.expanded_start_btn.setEnabled(False)
                self.expanded_stop_btn.setEnabled(True)
                
                # Ensure live mode is active for this view
                if not self.is_live:
                    self.start_live_mode()
                self.history_slider_active = False
                self.manual_view = False
                if self.history_slider_frame:
                    self.history_slider_frame.setVisible(False)
                    
                print("✅ Acquisition started successfully from expanded view")
            else:
                QMessageBox.warning(self, "Error", 
                    "Cannot start acquisition. Parent ECG page not found.")
                print("Parent ECG test page not available")
        except Exception as e:
            print(f"Error starting acquisition from expanded view: {e}")
            QMessageBox.warning(self, "Error", 
                f"Failed to start acquisition: {str(e)}")
    
    def stop_parent_acquisition(self):
        """Stop serial data acquisition from parent ECG test page"""
        try:
            parent = self.parent()
            if parent and hasattr(parent, 'stop_acquisition'):
                print("⏹️ Stopping acquisition from expanded lead view...")
                parent.stop_acquisition()
                self.stop_live_mode()
                self.history_slider_active = True
                self.manual_view = False
                if self.history_slider_frame:
                    self.history_slider_frame.setVisible(True)
                self.update_history_slider()
                
                # Update button states
                self.expanded_start_btn.setEnabled(True)
                self.expanded_stop_btn.setEnabled(False)
                
                print("✅ Acquisition stopped successfully from expanded view")
            else:
                QMessageBox.warning(self, "Error", 
                    "Cannot stop acquisition. Parent ECG page not found.")
                print("❌ Parent ECG test page not available")
        except Exception as e:
            print(f"❌ Error stopping acquisition from expanded view: {e}")
            QMessageBox.warning(self, "Error", 
                f"Failed to stop acquisition: {str(e)}")
    
    def update_button_states(self):
        """Update start/stop button states based on parent acquisition status"""
        try:
            parent = self.parent()
            
            # Check if demo mode is active
            is_demo_mode = False
            if parent and hasattr(parent, 'demo_toggle'):
                is_demo_mode = parent.demo_toggle.isChecked()
            
            # Hide buttons if demo mode is ON, show if OFF
            if hasattr(self, 'expanded_start_btn') and hasattr(self, 'expanded_stop_btn'):
                if is_demo_mode:
                    # Demo mode is ON - hide the buttons
                    self.expanded_start_btn.setVisible(False)
                    self.expanded_stop_btn.setVisible(False)
                    print("Demo mode ON - Start/Stop buttons hidden in expanded view")
                else:
                    # Demo mode is OFF - show the buttons and update their states
                    self.expanded_start_btn.setVisible(True)
                    self.expanded_stop_btn.setVisible(True)
                    
                    # Update enabled/disabled state based on acquisition status
                    if parent and hasattr(parent, 'timer'):
                        is_running = parent.timer.isActive()
                        self.expanded_start_btn.setEnabled(not is_running)
                        self.expanded_stop_btn.setEnabled(is_running)
                    else:
                        # Default state if parent not available
                        self.expanded_start_btn.setEnabled(True)
                        self.expanded_stop_btn.setEnabled(False)
                    
                    print("Demo mode OFF - Start/Stop buttons visible in expanded view")
        except Exception as e:
            print(f"Error updating button states: {e}")
    
    def create_arrhythmia_panel(self, parent_layout):
        """Create the arrhythmia analysis panel"""
        arrhythmia_frame = QFrame()
        arrhythmia_frame.setFixedHeight(70)
        arrhythmia_frame.setStyleSheet("""
            QFrame {
                background: white;
                border-radius: 8px;
                border: 1px solid #e0e0e0;
            }
        """)
        arrhythmia_layout = QHBoxLayout(arrhythmia_frame)
        arrhythmia_layout.setContentsMargins(15, 10, 15, 10)
        arrhythmia_layout.setSpacing(15)
        
        title = QLabel("Rhythm Interpretation:")
        title.setFont(QFont("Segoe UI", 13, QFont.Bold))
        title.setStyleSheet("color: #2c3e50; border: none; background: transparent;")
        arrhythmia_layout.addWidget(title)
        
        self.arrhythmia_list = QLabel("Analyzing...")
        self.arrhythmia_list.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.arrhythmia_list.setStyleSheet("color: #34495e; border: none; background: transparent;")
        self.arrhythmia_list.setWordWrap(True)
        self.arrhythmia_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        arrhythmia_layout.addWidget(self.arrhythmia_list, 1)
        
        parent_layout.addWidget(arrhythmia_frame)
    
    def analyze_ecg(self):
        """Analyze the ECG signal and update metrics"""
        if self.ecg_data.size == 0:
            self.arrhythmia_list.setText("No data to analyze.")
            return
        
        try:
            analysis = self.analyzer.analyze_signal(self.ecg_data)
            self.calculate_metrics(analysis)
            
            arrhythmias = self.arrhythmia_detector.detect_arrhythmias(self.ecg_data, analysis['r_peaks'])
            self.update_arrhythmia_display(arrhythmias)
            
            # Generate heat map data
            heat_map_data = self.arrhythmia_detector.detect_arrhythmias_with_probabilities(
                self.ecg_data, analysis['r_peaks'], window_size=2.0
            )
            self.prepare_heatmap_overlay(heat_map_data)
            
            self.update_plot_with_markers(analysis)
        except Exception as e:
            print(f"Error in ECG analysis: {e}")
            self.arrhythmia_list.setText("An error occurred during analysis.")
            import traceback
            traceback.print_exc()
    
    def calculate_metrics(self, analysis):
        """Calculate ECG metrics from analysis results"""
        try:
            # Check if demo mode is active from parent
            parent = self._parent if hasattr(self, '_parent') else None
            is_demo_mode = False
            if parent is not None and hasattr(parent, 'demo_toggle'):
                is_demo_mode = parent.demo_toggle.isChecked()
            
            # If demo mode is active, use fixed demo values
            if is_demo_mode:
                self.update_metric('heart_rate', 60)
                self.update_metric('rr_interval', 1000)
                self.update_metric('pr_interval', 160)
                self.update_metric('qrs_duration', 85)
                self.update_metric('p_duration', 80)
                return
            
            # Otherwise, calculate from real data
            r_peaks, p_peaks, q_peaks, s_peaks, t_peaks = (
                analysis['r_peaks'], analysis['p_peaks'], analysis['q_peaks'],
                analysis['s_peaks'], analysis['t_peaks']
            )
            
            # Heart Rate & RR Interval - use same calculation as 12-lead page if available
            heart_rate = 0
            if parent is not None and hasattr(parent, 'calculate_heart_rate'):
                try:
                    heart_rate = int(parent.calculate_heart_rate(self.ecg_data))
                    self.update_metric('heart_rate', max(0, heart_rate))
                    self.update_metric('rr_interval', int(60000 / heart_rate) if heart_rate > 0 else 0)
                except Exception:
                    heart_rate = 0
            else:
                if len(r_peaks) > 1:
                    rr_intervals = np.diff(r_peaks) / self.sampling_rate * 1000
                    mean_rr = np.mean(rr_intervals)
                    heart_rate = 60000 / mean_rr if mean_rr > 0 else 0
                    self.update_metric('heart_rate', int(heart_rate))
                    self.update_metric('rr_interval', int(mean_rr))
            
            # PR Interval
            if len(p_peaks) > 0 and len(q_peaks) > 0:
                # A more robust PR interval is P-onset to Q-onset
                # Simplified: p_peak to q_peak
                pr_intervals = [(q - p) / self.sampling_rate * 1000 for p, q in zip(p_peaks, q_peaks) if q > p]
                if pr_intervals:
                    self.update_metric('pr_interval', int(np.mean(pr_intervals)))
            
            # QRS Duration
            if len(q_peaks) > 0 and len(s_peaks) > 0:
                qrs_durations = [(s - q) / self.sampling_rate * 1000 for q, s in zip(q_peaks, s_peaks) if s > q]
                if qrs_durations:
                    self.update_metric('qrs_duration', int(np.mean(qrs_durations)))
            
            # QTc Interval (Bazett's formula) using measured QT (if available)
            if 'rr_interval' in self.metrics_cards and self.metrics_cards['rr_interval'].value > 0:
                rr_sec = self.metrics_cards['rr_interval'].value / 1000.0
                # Estimate QT as mean (T − Q) over detected beats
                qt_intervals = []
                for q_idx, t_idx in zip(q_peaks, t_peaks):
                    if t_idx > q_idx:
                        qt_ms = (t_idx - q_idx) / self.sampling_rate * 1000.0
                        # Accept only physiologic QT (e.g., 240–520 ms)
                        if 240.0 <= qt_ms <= 520.0:
                            qt_intervals.append(qt_ms)
                if qt_intervals and rr_sec > 0:
                    qt_interval_ms = float(np.median(qt_intervals))
                    qtc = qt_interval_ms / np.sqrt(rr_sec)
                    self.update_metric('qtc_interval', int(round(qtc)))

            # P Duration (estimate from P-wave width around detected P peaks)
            try:
                if len(p_peaks) > 0:
                    filtered = self.analyzer._filter_signal(self.ecg_data)
                    p_durations = []
                    for p_idx in p_peaks:
                        # Examine a window of ±80 ms around the P-peak
                        half_win = int(0.08 * self.sampling_rate)
                        start = max(0, p_idx - half_win)
                        end = min(len(filtered) - 1, p_idx + half_win)
                        if end <= start + 2:
                            continue
                        segment = filtered[start:end]
                        # Local baseline and peak amplitude
                        baseline = np.median(segment)
                        peak_rel = int(np.argmax(np.abs(segment - baseline)))
                        peak_val = segment[peak_rel]
                        amp = np.abs(peak_val - baseline)
                        if amp <= 0:
                            continue
                        # Threshold at 20% of peak above baseline
                        thresh = 0.2 * amp
                        # Search left for onset
                        left = peak_rel
                        while left > 0 and np.abs(segment[left] - baseline) > thresh:
                            left -= 1
                        # Search right for offset
                        right = peak_rel
                        while right < len(segment) - 1 and np.abs(segment[right] - baseline) > thresh:
                            right += 1
                        dur_samples = max(1, right - left)
                        p_durations.append(dur_samples * 1000.0 / self.sampling_rate)
                    if p_durations:
                        self.update_metric('p_duration', int(round(np.median(p_durations))))
            except Exception as _:
                # Fallback if anything fails; do not block other metrics
                pass
            
        except Exception as e:
            print(f"Error calculating metrics: {e}")
    
    def update_metric(self, metric_name, value):
        """Update a specific metric card"""
        if metric_name in self.metrics_cards:
            self.metrics_cards[metric_name].update_value(value)
    
    def update_arrhythmia_display(self, arrhythmias):
        """Update the arrhythmia display"""
        arrhythmia_text = ", ".join(arrhythmias) if arrhythmias else "No specific arrhythmia detected."
        self.arrhythmia_list.setText(arrhythmia_text)
        
        # Color code based on severity
        is_normal = "Normal Sinus Rhythm" in arrhythmia_text
        self.arrhythmia_list.setStyleSheet(f"""
            color: {'#2ecc71' if is_normal else '#e74c3c'};
            font-weight: bold;
            border: none;
        """)
    
    def update_plot_with_markers(self, analysis):
        """Update the plot without PQRST labels/markers (as requested)"""
        if self.ecg_data.size == 0:
            return

        try:
            # Remove any previously drawn markers/labels and do not add new ones
            while len(self.ax.collections) > 0:
                self.ax.collections.pop()
            while len(self.ax.texts) > 0:
                self.ax.texts.pop()

            # Ensure no legend is shown
            leg = self.ax.get_legend()
            if leg is not None:
                leg.remove()

            self.canvas.draw()

        except Exception as e:
            print(f"Error updating plot markers: {e}")

    def prepare_heatmap_overlay(self, heat_map_data):
        """Convert arrhythmia probabilities into a background overlay and record event times."""
        # Clear previous events each time we recompute the heatmap
        self.arrhythmia_events = []

        colors = {
            "Normal Sinus Rhythm": "#2ecc71",
            "Atrial Fibrillation": "#e74c3c",
            "Ventricular Tachycardia": "#8e44ad",
            "Premature Ventricular Contractions": "#f39c12",
            "Sinus Bradycardia": "#3498db",
            "Sinus Tachycardia": "#e67e22",
            "Irregular Rhythm": "#95a5a6"
        }
        arrhythmia_types = list(colors.keys())

        if not heat_map_data:
            self.heatmap_overlay = None
            self.heatmap_time_axis = None
            return

        base_series = None
        for arr_type in arrhythmia_types:
            if arr_type in heat_map_data and heat_map_data[arr_type]:
                base_series = heat_map_data[arr_type]
                break

        if not base_series:
            self.heatmap_overlay = None
            self.heatmap_time_axis = None
            return

        num_windows = len(base_series)
        overlay = np.ones((120, num_windows, 4))
        time_axis = []

        for idx in range(num_windows):
            time_value = base_series[idx][0] if idx < len(base_series) else idx * 2.0
            time_axis.append(time_value)
            
            best_type = "Irregular Rhythm"
            best_prob = 0.0
            for arr_type in arrhythmia_types:
                arr_list = heat_map_data.get(arr_type, [])
                if idx < len(arr_list):
                    _, prob = arr_list[idx]
                    if prob > best_prob:
                        best_prob = prob
                        best_type = arr_type

            color_hex = colors.get(best_type, "#95a5a6")
            rgb = tuple(int(color_hex[i:i+2], 16) / 255.0 for i in (1, 3, 5))
            opacity = 0.2 + 0.8 * max(0.0, min(1.0, best_prob))
            overlay[:, idx, 0] = rgb[0]
            overlay[:, idx, 1] = rgb[1]
            overlay[:, idx, 2] = rgb[2]
            overlay[:, idx, 3] = opacity

            # Record an arrhythmia event when a non-normal rhythm dominates this window
            if best_type != "Normal Sinus Rhythm" and best_prob >= 0.7:
                self.arrhythmia_events.append((float(time_value), best_type))

        self.heatmap_overlay = overlay
        self.heatmap_time_axis = np.array(time_axis)
        if len(self.heatmap_time_axis) > 1:
            diffs = np.diff(self.heatmap_time_axis)
            self.heatmap_window_step = max(0.1, float(np.median(diffs)))
        else:
            self.heatmap_window_step = 2.0

    def update_history_slider(self):
        """Adjust slider bounds to match available history"""
        if not hasattr(self, 'history_slider'):
            return
        total_duration = len(self.ecg_data) / max(1.0, self.sampling_rate)
        max_offset = max(0.0, total_duration - self.view_window_duration)
        slider_max = int(max_offset * 1000)
        current_val = int(min(self.view_window_offset, max_offset) * 1000)
        self.history_slider.blockSignals(True)
        self.history_slider.setMaximum(slider_max)
        self.history_slider.setValue(current_val)
        self.history_slider.blockSignals(False)

        if self.history_slider_label:
            if not self.history_slider_active:
                self.history_slider_label.setText("LIVE")
            else:
                start_time = min(self.view_window_offset, max_offset)
                end_time = min(start_time + self.view_window_duration, total_duration)
                self.history_slider_label.setText(f"{start_time:0.1f}s – {end_time:0.1f}s")

    def on_history_slider_changed(self, value):
        """Scroll through historical data when acquisition is stopped"""
        if not self.history_slider_active:
            return
        self.manual_view = True
        self.view_window_offset = value / 1000.0
        self.update_plot()
        if self.history_slider_label:
            total_duration = len(self.ecg_data) / max(1.0, self.sampling_rate)
            start_time = max(0.0, min(self.view_window_offset, total_duration))
            end_time = min(start_time + self.view_window_duration, total_duration)
            self.history_slider_label.setText(f"{start_time:0.1f}s – {end_time:0.1f}s")

def show_expanded_lead_view(lead_name, ecg_data, sampling_rate=500, parent=None):
    """Show the expanded lead view dialog"""
    dialog = ExpandedLeadView(lead_name, ecg_data, sampling_rate, parent)
    # Open maximized by default for best visibility on any monitor
    dialog.showMaximized()
    dialog.exec_()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Create more realistic sample ECG data
    fs = 500
    duration = 5 # seconds
    t = np.linspace(0, duration, duration * fs, endpoint=False)
    
    # P wave
    p_wave = 0.1 * np.exp(-((t % 1 - 0.25)**2) / 0.005)
    # QRS complex
    qrs_complex = 1.0 * np.exp(-((t % 1 - 0.4)**2) / 0.002) - 0.3 * np.exp(-((t % 1 - 0.37)**2) / 0.001) - 0.2 * np.exp(-((t % 1 - 0.43)**2) / 0.001)
    # T wave
    t_wave = 0.3 * np.exp(-((t % 1 - 0.6)**2) / 0.01)
    # Noise
    noise = 0.03 * np.random.randn(len(t))
    
    sample_ecg = p_wave + qrs_complex + t_wave + noise
    
    dialog = ExpandedLeadView("Lead II", sample_ecg, fs)
    dialog.showMaximized()
    
    sys.exit(app.exec_())
