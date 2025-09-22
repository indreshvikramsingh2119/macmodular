"""
Expanded Lead View - Detailed ECG lead analysis with PQRST labeling and metrics
This module provides an expanded view of individual ECG leads with comprehensive analysis.
"""

import sys
import numpy as np
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QGridLayout,
    QSizePolicy, QScrollArea, QGroupBox, QFormLayout, QLineEdit, QComboBox,
    QMessageBox, QApplication, QDialog, QGraphicsDropShadowEffect
)
from PyQt5.QtGui import QFont, QColor, QPalette, QPixmap, QPainter, QPen
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QRect
import pyqtgraph as pg
from scipy.signal import find_peaks, butter, filtfilt
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.patches as patches

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
        # Base sizes used for responsive scaling
        self._base_title_pt = 14
        self._base_value_pt = 28
        self._base_status_pt = 12
        
        # Increase card vertical room to prevent value text cropping on macOS/Windows
        self.setMinimumHeight(200)
        self.setMaximumHeight(240)
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
        self.value_label.setStyleSheet("color: #2c3e50; border: none; margin: 8px 0; font-weight: bold; background: transparent;")
        self.value_label.setAlignment(Qt.AlignLeft)
        # Ensure enough label height for larger fonts to avoid clipping
        self.value_label.setMinimumHeight(56)
        self.value_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
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
        self.analyzer = PQRSTAnalyzer(sampling_rate)
        self.arrhythmia_detector = ArrhythmiaDetector(sampling_rate)
        
        # Live data update
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_live_data)
        self.is_live = False
        
        self.setWindowTitle(f"Detailed Analysis - {lead_name}")
        self.setMinimumSize(1100, 700)
        self.resize(1400, 900)
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
        title_label.setFont(QFont("Segoe UI", 22, QFont.Bold))
        title_label.setStyleSheet("color: #2c3e50; border: none; background: transparent;")
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
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.canvas.setMinimumSize(700, 420)
        plot_layout.addWidget(self.canvas)
        
        parent_layout.addWidget(plot_frame, 7) # Plot takes ~70% of horizontal space
    
    def setup_ecg_plot(self):
        """Setup the ECG plot with proper styling"""
        if len(self.ecg_data) == 0:
            self.ax.text(0.5, 0.5, 'No ECG Data Available', 
                         transform=self.ax.transAxes, ha='center', va='center',
                         fontsize=16, color='gray')
            return
        
        time = np.arange(len(self.ecg_data)) / self.sampling_rate
        
        self.ax.plot(time, self.ecg_data, color='#0984e3', linewidth=1.5, label='ECG Signal')
        
        self.ax.set_xlabel('Time (seconds)', fontsize=14, fontweight='bold', color='#34495e')
        self.ax.set_ylabel('Amplitude (mV)', fontsize=14, fontweight='bold', color='#34495e')
        self.ax.set_title(f'Lead {self.lead_name} - PQRST Analysis', fontsize=18, fontweight='bold', color='#2c3e50')
        
        self.ax.grid(True, which='both', linestyle='--', linewidth=0.5, color='#bdc3c7')
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)
        
        self.ax.set_xlim(0, max(time) if len(time) > 0 else 1)
        if len(self.ecg_data) > 0:
            y_margin = (np.max(self.ecg_data) - np.min(self.ecg_data)) * 0.1
            self.ax.set_ylim(np.min(self.ecg_data) - y_margin, np.max(self.ecg_data) + y_margin)
    
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
        metrics = [
            ("Heart Rate", 0, "BPM", "#d35400"),
            ("RR Interval", 0, "ms", "#2980b9"),
            ("PR Interval", 0, "ms", "#8e44ad"),
            ("QRS Duration", 0, "ms", "#27ae60"),
            ("QTc Interval", 0, "ms", "#c0392b"),
            ("P Duration", 0, "ms", "#16a085"),
        ]
        
        for i, (title, value, unit, color) in enumerate(metrics):
            card = MetricsCard(title, value, unit, color)
            self.metrics_cards[title.lower().replace(" ", "_")] = card
            self.metrics_vbox.addWidget(card)
        
        # Add a stretch at the end
        self.metrics_vbox.addStretch(1)
        
        # Initialize with some default values for testing
        self.update_metric('heart_rate', 0)
        self.update_metric('rr_interval', 0)
        self.update_metric('pr_interval', 0)
        self.update_metric('qrs_duration', 0)
        self.update_metric('qtc_interval', 0)
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
            if hasattr(parent, 'data') and len(parent.data) > 0:
                # Find the lead index for this lead
                lead_index = self.get_lead_index()
                if lead_index is not None and lead_index < len(parent.data):
                    new_data = parent.data[lead_index]
                    if len(new_data) > 0:
                        self.ecg_data = np.array(new_data)
                        self.update_plot()
                        self.analyze_ecg()
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
            # Clear the plot
            self.ax.clear()
            
            # Plot new data
            time = np.arange(len(self.ecg_data)) / self.sampling_rate
            self.ax.plot(time, self.ecg_data, color='#0984e3', linewidth=1.5, label='ECG Signal')
            
            # Update labels and styling
            self.ax.set_xlabel('Time (seconds)', fontsize=14, fontweight='bold', color='#34495e')
            self.ax.set_ylabel('Amplitude (mV)', fontsize=14, fontweight='bold', color='#34495e')
            self.ax.set_title(f'Lead {self.lead_name} - Live PQRST Analysis', fontsize=18, fontweight='bold', color='#2c3e50')
            
            # Grid and styling
            self.ax.grid(True, which='both', linestyle='--', linewidth=0.5, color='#bdc3c7')
            self.ax.spines['top'].set_visible(False)
            self.ax.spines['right'].set_visible(False)
            
            # Set limits
            self.ax.set_xlim(0, max(time) if len(time) > 0 else 1)
            if len(self.ecg_data) > 0:
                y_margin = (np.max(self.ecg_data) - np.min(self.ecg_data)) * 0.1
                self.ax.set_ylim(np.min(self.ecg_data) - y_margin, np.max(self.ecg_data) + y_margin)
            
            # Redraw
            self.canvas.draw()
            
        except Exception as e:
            print(f"Error updating plot: {e}")
    
    def closeEvent(self, event):
        """Handle window close event"""
        self.stop_live_mode()
        event.accept()
    
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
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title.setStyleSheet("color: #2c3e50; border: none; background: transparent;")
        arrhythmia_layout.addWidget(title)
        
        self.arrhythmia_list = QLabel("Analyzing...")
        self.arrhythmia_list.setFont(QFont("Segoe UI", 16, QFont.Bold))
        self.arrhythmia_list.setStyleSheet("color: #34495e; border: none; background: transparent;")
        self.arrhythmia_list.setWordWrap(True)
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
            
            self.update_plot_with_markers(analysis)
        except Exception as e:
            print(f"Error in ECG analysis: {e}")
            self.arrhythmia_list.setText("An error occurred during analysis.")
    
    def calculate_metrics(self, analysis):
        """Calculate ECG metrics from analysis results"""
        try:
            r_peaks, p_peaks, q_peaks, s_peaks, t_peaks = (
                analysis['r_peaks'], analysis['p_peaks'], analysis['q_peaks'],
                analysis['s_peaks'], analysis['t_peaks']
            )
            
            # Heart Rate & RR Interval
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
            
            # QTc Interval (Bazett's formula)
            if 'rr_interval' in self.metrics_cards and self.metrics_cards['rr_interval'].value > 0:
                rr_sec = self.metrics_cards['rr_interval'].value / 1000.0
                # Simplified QT, actual QT needs T-wave end detection
                qt_interval_ms = 380 # Assuming a typical QT
                qtc = qt_interval_ms / np.sqrt(rr_sec) if rr_sec > 0 else 0
                self.update_metric('qtc_interval', int(qtc))

            # P Duration (simplified)
            self.update_metric('p_duration', 80) # Typical duration
            
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
        """Update the plot with PQRST markers"""
        if self.ecg_data.size == 0: return
        
        try:
            # Clear previous markers except for the main line
            while len(self.ax.collections) > 0: self.ax.collections.pop()
            while len(self.ax.texts) > 0: self.ax.texts.pop()
            
            time = np.arange(len(self.ecg_data)) / self.sampling_rate
            
            markers = {
                'p_peaks': ('P', '#16a085'), 'q_peaks': ('Q', '#2980b9'),
                'r_peaks': ('R', '#c0392b'), 's_peaks': ('S', '#f39c12'),
                't_peaks': ('T', '#8e44ad')
            }
            
            for wave_type, (label, color) in markers.items():
                peaks = analysis.get(wave_type, [])
                if len(peaks) > 0:
                    peak_times = np.array(peaks) / self.sampling_rate
                    peak_values = self.ecg_data[peaks]
                    
                    self.ax.scatter(peak_times, peak_values, 
                                    color=color, s=50, alpha=0.9, 
                                    label=f'{label} Waves', zorder=5)
                    # Add text labels above markers
                    for i in range(len(peaks)):
                        self.ax.text(peak_times[i], peak_values[i] + 0.05, label, 
                                     color=color, fontsize=11, fontweight='bold')
            
            handles, labels = self.ax.get_legend_handles_labels()
            by_label = dict(zip(labels, handles))
            self.ax.legend(by_label.values(), by_label.keys(), loc='upper right', fontsize=12)
            
            self.canvas.draw()
            
        except Exception as e:
            print(f"Error updating plot markers: {e}")

def show_expanded_lead_view(lead_name, ecg_data, sampling_rate=500, parent=None):
    """Show the expanded lead view dialog"""
    dialog = ExpandedLeadView(lead_name, ecg_data, sampling_rate, parent)
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
    dialog.show()
    
    sys.exit(app.exec_())