from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFrame, 
    QLineEdit, QComboBox, QSlider, QGroupBox, QListWidget, QDialog,
    QGridLayout, QFormLayout, QSizePolicy, QMessageBox, QApplication, QRadioButton, QScrollArea
)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np
from PyQt5.QtCore import QTimer, Qt, QPropertyAnimation, QEasingCurve, QTimer, pyqtProperty, QRect
from PyQt5.QtGui import QIntValidator
from utils.settings_manager import SettingsManager
import os
import matplotlib.pyplot as plt
import pandas as pd 
import json 
import sys

# NOTE: ECGRecording class removed (was never used in codebase)
# Recording functionality is handled by SessionRecorder in utils/session_recorder.py
        
class Lead12BlackPage(QWidget):
    def __init__(self, parent=None, dashboard=None):
        super().__init__(parent)
        self.dashboard = dashboard
        self.setStyleSheet("background: black;")
        layout = QVBoxLayout(self)
        self.canvases = []
        self.lines = []
        self.ecg_buffers = [np.zeros(5000) for _ in range(12)]
        self.ptrs = [0 for _ in range(12)]
        self.window_size = 1000
        self.lead_names = ["I", "II", "III", "aVR", "aVL", "aVF", "V1", "V2", "V3", "V4", "V5", "V6"]
        for i in range(12):
            label = QLabel(self.lead_names[i])
            label.setStyleSheet("color: white; font-size: 14px; font-weight: bold; margin-bottom: 2px;")
            label.setFixedWidth(70)
            layout.addWidget(label, alignment=Qt.AlignLeft)
            fig = Figure(figsize=(2, 2), facecolor='black')
            ax = fig.add_subplot(111)
            ax.set_facecolor('black')
            ax.set_xticks([])
            ax.set_yticks([])
            ax.set_ylim(-3, 3)
            ax.axvline(x=0, color='white', linestyle='--', linewidth=1)
            ax.set_title("", color='white', fontsize=12, loc='left')
            line, = ax.plot(np.zeros(self.window_size), color='lime', lw=1)
            canvas = FigureCanvas(fig)
            layout.addWidget(canvas)
            self.canvases.append(canvas)
            self.lines.append(line)
        self.setLayout(layout)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_data)
        self.timer.start(30)  # ~33 FPS
    
    def closeEvent(self, event):
        """Clean up resources when widget is closed"""
        if hasattr(self, 'timer') and self.timer:
            self.timer.stop()
            self.timer.deleteLater()
        super().closeEvent(event)

    def update_data(self):
        for i in range(12):
            # Slide a window over the simulated ECG for animation
            self.ptrs[i] = (self.ptrs[i] + 1) % (len(self.ecg_buffers[i]) - self.window_size)
            window = self.ecg_buffers[i][self.ptrs[i]:self.ptrs[i]+self.window_size]
            self.lines[i].set_ydata(window)
            # --- P peak detection and labeling for each lead ---
            if len(window) >= 1000:
                try:
                    # Placeholder for PQRST detection logic
                    p_peaks = np.array([100, 200, 300])  # Dummy values for illustration
                    ax = self.canvases[i].figure.axes[0]
                    main_line = ax.lines[0]
                    ax.lines = [main_line]
                    # Remove old text labels
                    for txt in ax.texts:
                        txt.remove()
                    # Plot green markers and labels for P peaks only
                    if len(p_peaks) > 0:
                        ax.plot(p_peaks, window[p_peaks], 'o', color='green', label='P', markersize=8, zorder=10)
                        for idx in p_peaks:
                            ax.text(idx, window[idx]+0.3, 'P', color='green', fontsize=10, ha='center', va='bottom', zorder=11)
                    # Optional: update legend
                    handles, labels = ax.get_legend_handles_labels()
                    by_label = dict(zip(labels, handles))
                    ax.legend(by_label.values(), by_label.keys(), loc='upper right', fontsize=8)
                except Exception as e:
                    print(f"ECG analysis error in lead {self.lead_names[i]}:", e)
            self.canvases[i].draw()
        # --- Lead II metrics and dashboard update (as before) ---
        lead_ii_signal = self.ecg_buffers[1][self.ptrs[1]:self.ptrs[1]+self.window_size]
        if len(lead_ii_signal) >= 1000:
            try:
                # TODO: Replace with real metric calculations from twelve_lead_test.py
                # These are placeholder/dummy values for testing visualization only
                pr_interval = 0.2  # TODO: Calculate from real P-R wave detection
                qrs_duration = 0.08  # TODO: Calculate from real QRS complex
                qt_interval = 0.4  # TODO: Calculate from real Q-T interval
                qtc_interval = 0.42  # TODO: Calculate corrected QT (Bazett's formula)
                qrs_axis = "--"  # TODO: Calculate from lead I and aVF
                st_segment = "--"  # TODO: Calculate ST elevation/depression
                with open("ecg_metrics_output.txt", "w") as f:
                    f.write("# ECG Metrics Output (TEST/DEBUG ONLY)\n")
                    f.write("# WARNING: These are placeholder values, not real calculations!\n")
                    f.write("# Format: PR_interval(ms), QRS_duration(ms), QTc_interval(ms), QRS_axis, ST_segment\n")
                    f.write(f"{pr_interval*1000}, {qrs_duration*1000}, {qtc_interval*1000}, {qrs_axis}, {st_segment}\n")
                    # TODO: Replace with real peak detection from Pan-Tompkins algorithm
                    f.write(f"P_peaks: {list(np.array([100, 200, 300]))}  # PLACEHOLDER\n")
                    f.write(f"Q_peaks: {list(np.array([150, 250, 350]))}  # PLACEHOLDER\n")
                    f.write(f"R_peaks: {list(np.array([180, 280, 380]))}  # PLACEHOLDER\n")
                    f.write(f"S_peaks: {list(np.array([210, 310, 410]))}  # PLACEHOLDER\n")
                    f.write(f"T_peaks: {list(np.array([240, 340, 440]))}  # PLACEHOLDER\n")
                if self.dashboard and hasattr(self.dashboard, "update_ecg_metrics"):
                    self.dashboard.update_ecg_metrics(pr_interval, qrs_duration, qtc_interval, qrs_axis, st_segment)
                    QTimer.singleShot(0, self.dashboard.repaint)
            except Exception as e:
                print("ECG analysis error:", e)

class SlidingPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        
        # Responsive sizing based on parent size
        if parent:
            parent_width = parent.width()
            parent_height = parent.height()
            
            # Calculate responsive panel size (25-35% of parent width, max 900px)
            panel_width = min(max(int(parent_width * 0.30), 400), 900)
            panel_height = min(max(int(parent_height * 0.85), 500), 1000)
        else:
            panel_width, panel_height = 600, 800
        
        self.panel_width = panel_width
        self.panel_height = panel_height
        
        # Set size policy for responsiveness
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setFixedSize(panel_width, panel_height)
        
        # Responsive styling with dynamic sizing
        self.setStyleSheet(f"""
            QWidget {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #ffffff, stop:1 #f8f9fa);
                border: 3px solid #e0e0e0;
                border-radius: 15px;
            }}
        """)
        
        # Initialize position off-screen to the right
        if parent:
            self.setGeometry(parent.width(), (parent.height() - self.height()) // 2, 
                           panel_width, panel_height)
        else:
            self.setGeometry(1200, 200, panel_width, panel_height)
        
        # Create responsive layout with dynamic margins
        self.layout = QVBoxLayout(self)
        margin_size = max(12, min(30, int(panel_width * 0.04)))  # Responsive margins
        spacing_size = max(10, min(25, int(panel_height * 0.03)))  # Responsive spacing
        
        self.layout.setContentsMargins(margin_size, margin_size, margin_size, margin_size)
        self.layout.setSpacing(spacing_size)
        
        # Content area with scroll support
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.layout.addWidget(self.content_widget)
        
        # Animation setup
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(300)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
        
        self.is_visible = False
        self.is_animating = False
        
        # Store responsive parameters
        self.margin_size = margin_size
        self.spacing_size = spacing_size
        
        # Add resize event handler for responsiveness
        if parent:
            parent.resizeEvent = self.parent_resize_handler
        
    def parent_resize_handler(self, event):
        """Handle parent resize events for responsive behavior"""
        if hasattr(event, 'size'):
            self.update_responsive_sizing()
        if hasattr(event, 'oldSize'):
            event.oldSize = event.size()
        event.accept()
        
    def update_responsive_sizing(self):
        if self.parent:
            parent_width = self.parent.width()
            parent_height = self.parent.height()
            
            # Recalculate responsive sizes
            new_width = min(max(int(parent_width * 0.30), 400), 900)
            new_height = min(max(int(parent_height * 0.85), 500), 1000)
            
            if new_width != self.panel_width or new_height != self.panel_height:
                self.panel_width = new_width
                self.panel_height = new_height
                
                # Update margins and spacing
                self.margin_size = max(12, min(30, int(new_width * 0.04)))
                self.spacing_size = max(10, min(25, int(new_height * 0.03)))
                
                # Update layout
                self.layout.setContentsMargins(self.margin_size, self.margin_size, 
                                            self.margin_size, self.margin_size)
                self.layout.setSpacing(self.spacing_size)
                
                # Resize panel
                self.setFixedSize(new_width, new_height)
                
                # Reposition if visible
                if self.is_visible:
                    self.reposition_panel()
        
    def reposition_panel(self):
        if self.parent and self.is_visible:
            target_x = self.parent.width() - self.width() - 15  # Reduced margin
            target_y = (self.parent.height() - self.height()) // 2
            self.move(target_x, target_y)
        
    def set_title(self, title):
        pass
        
    def clear_content(self):
        # Clear existing content
        while self.content_layout.count():
            child = self.content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
                
    def slide_in(self, content_widget=None, title="Settings Panel"):
        
        if self.parent and not self.is_animating:
            self.is_animating = True
            self.clear_content()
            
            # Update responsive sizing before showing
            self.update_responsive_sizing()
            
            if content_widget:
                # Make content widget responsive
                self.make_content_responsive(content_widget)
                self.content_layout.addWidget(content_widget)

            # Force Layout so first-open renders correctly
            try:
                self.content_widget.adjustSize()
                self.layout.activate()
                QApplication.processEvents()
                self.update()
            except:
                pass
            
            # Calculate target position (centered on the right side with proper margins)
            # Ensure panel doesn't go off-screen on small devices
            target_x = max(10, self.parent.width() - self.width() - 10)  # At least 10px from right edge
            target_y = max(10, (self.parent.height() - self.height()) // 2)  # At least 10px from top/bottom
            
            # Ensure panel doesn't exceed parent bounds
            if target_y + self.height() > self.parent.height() - 10:
                target_y = self.parent.height() - self.height() - 10

            start_rect = QRect(self.parent.width(), target_y, self.width(), self.height())
            end_rect = QRect(target_x, target_y, self.width(), self.height())

            # Set up animation using Local QRect
            self.setGeometry(start_rect)

            self.animation.setStartValue(start_rect)
            self.animation.setEndValue(end_rect)

            # Disconnect any existing connections
            try:
                self.animation.finished.disconnect()
            except:
                pass
            
            # Connect animation finished signal
            self.animation.finished.connect(self.on_slide_in_finished)
            
            self.show()
            self.raise_()
            self.animation.start()

    def make_content_responsive(self, content_widget):
        if hasattr(content_widget, 'layout'):
            layout = content_widget.layout()
            if layout:
                # Adjust margins and spacing based on panel size
                content_margin = max(15, min(35, int(self.panel_width * 0.04)))
                content_spacing = max(10, min(20, int(self.panel_height * 0.025)))
                
                layout.setContentsMargins(content_margin, content_margin, 
                                       content_margin, content_margin)
                layout.setSpacing(content_spacing)
                
                # Make child widgets responsive
                self.make_children_responsive(content_widget)
    
    def make_children_responsive(self, parent_widget):
        for child in parent_widget.findChildren(QWidget):
            if hasattr(child, 'setFixedSize'):
                # Adjust fixed sizes for smaller panels
                if self.panel_width < 500:
                    # Scale down fixed sizes for small panels
                    if hasattr(child, 'width') and hasattr(child, 'height'):
                        current_width = child.width()
                        current_height = child.height()
                        if current_width > 0 and current_height > 0:
                            scale_factor = min(self.panel_width / 600, 1.0)
                            new_width = max(int(current_width * scale_factor), 60)
                            new_height = max(int(current_height * scale_factor), 25)
                            child.setFixedSize(new_width, new_height)
            
            # Recursively process children
            self.make_children_responsive(child)

    def on_slide_in_finished(self):
        self.is_visible = True
        self.is_animating = False
            
    def slide_out(self):
        if self.parent and self.is_visible and not self.is_animating:
            self.is_animating = True

            # Calculate end position (off-screen to the right)
            end_x = self.parent.width()
            end_y = (self.parent.height() - self.height()) // 2

            # Set up animation using Local QRect
            start_rect = QRect(self.x(), self.y(), self.width(), self.height())
            end_rect = QRect(end_x, end_y, self.width(), self.height())
            self.animation.setStartValue(start_rect)
            self.animation.setEndValue(end_rect)
            
            # Disconnect any existing connections
            try:
                self.animation.finished.disconnect()
            except:
                pass
            
            # Connect animation finished signal
            self.animation.finished.connect(self.on_slide_out_finished)
            self.animation.start()

    def on_slide_out_finished(self):
        self.hide()
        self.is_visible = False
        self.is_animating = False

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.parent and self.is_visible:
            self.reposition_panel()

class ECGMenu(QGroupBox):
    def __init__(self, parent=None, dashboard=None):
        super().__init__("", parent)
        self.dashboard = dashboard
        # Reference to ECG test page for cross-component communication
        self.ecg_test_page = None
        self.settings_manager = None
        self.sliding_panel = None
        self.settings_changed_callback = None

        self.setStyleSheet("QGroupBox { font: bold 14pt Arial; background-color: #fff; border-radius: 10px; }")
        layout = QVBoxLayout(self)
        self.buttons = {}
        menu_buttons = [
            ("Save ECG", self.on_save_ecg),
            ("Open ECG", self.on_open_ecg),
            ("Working Mode", self.on_working_mode),
            ("Printer Setup", self.on_printer_setup),
            ("Set Filter", self.on_set_filter),
            ("System Setup", self.on_system_setup),
            ("Load Default", self.on_load_default),
            ("Version", self.on_version_info),
            ("Factory Maintain", self.on_factory_maintain),
            ("Exit", self.on_exit)
        ]
        for text, handler in menu_buttons:
            btn = QPushButton(text)
            btn.setFixedHeight(36)
            btn.clicked.connect(handler)
            layout.addWidget(btn)
            self.buttons[text] = btn
        layout.addStretch(1)
    
        # Initialize sliding panel
        self.sliding_panel = None
        self.current_panel_content = None
        self.current_open_panel = None
        self.panel_buttons = {}
        
        # Store parent reference for responsive updates
        self.parent_widget = None
        
        # Connect to parent resize events
        if parent:
            self.setup_parent_monitoring(parent)
        
        # Setup global resize monitoring
        QTimer.singleShot(100, self.setup_global_resize_monitoring)

    def set_ecg_test_page(self, ecg_test_page):
        """Attach the active ECG test page so menu actions can interact with it."""
        self.ecg_test_page = ecg_test_page

    def setup_parent_monitoring(self, parent):
        """Setup monitoring for parent widget changes"""
        if parent and hasattr(parent, 'resizeEvent'):
            # Store original resize event
            original_resize = parent.resizeEvent
            
            def enhanced_resize_event(event):
                # Call original resize event
                if hasattr(original_resize, '__call__'):
                    original_resize(event)
                
                # Update sliding panel if it exists
                if hasattr(self, 'sliding_panel') and self.sliding_panel:
                    self.sliding_panel.update_responsive_sizing()
                    if self.sliding_panel.is_visible:
                        self.sliding_panel.reposition_panel()
                
                event.accept()
            
            # Replace the resize event handler
            parent.resizeEvent = enhanced_resize_event

    def create_resize_handler(self, original_resize_event):
        def resize_handler(event):
            # Call original resize event
            if original_resize_event:
                original_resize_event(event)
            
            # Update sliding panel if it exists
            if self.sliding_panel and hasattr(self.sliding_panel, 'update_responsive_sizing'):
                self.sliding_panel.update_responsive_sizing()
                
        return resize_handler

    def setup_global_resize_monitoring(self):
        app = QApplication.instance()
        if app:
            # Monitor all top-level windows
            for widget in app.topLevelWidgets():
                if hasattr(widget, 'resizeEvent'):
                    original_resize = widget.resizeEvent
                    widget.resizeEvent = self.create_global_resize_handler(original_resize)
    
    def create_global_resize_handler(self, original_resize_event):
        def global_resize_handler(event):
            # Call original resize event
            if original_resize_event:
                original_resize_event(event)
            
            # Update sliding panel if it exists
            if self.sliding_panel and hasattr(self.sliding_panel, 'update_responsive_sizing'):
                self.sliding_panel.update_responsive_sizing()
                
        return global_resize_handler

    # Placeholder methods to be connected externally
    def on_save_ecg(self):
        self.show_save_ecg()
    def on_open_ecg(self):
        self.show_open_ecg()
    def on_working_mode(self):
        self.show_working_mode()
    def on_printer_setup(self):
        self.show_printer_setup()
    def on_set_filter(self):
        self.show_set_filter()
    def on_system_setup(self):
        self.show_system_setup()
    def on_load_default(self):
        self.show_load_default()
    def on_version_info(self):
        self.show_version_info()
    def on_factory_maintain(self):
        self.show_factory_maintain()
    def on_exit(self):
        self.show_exit()

    def create_scrollable_content(self, content_widget):
        from PyQt5.QtWidgets import QScrollArea
        
        scroll_area = QScrollArea()
        scroll_area.setWidget(content_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Responsive scroll area styling
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                background: #f0f0f0;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: #c0c0c0;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #a0a0a0;
            }
            QScrollBar:horizontal {
                background: #f0f0f0;
                height: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:horizontal {
                background: #c0c0c0;
                border-radius: 6px;
                min-width: 20px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #a0a0a0;
            }
        """)
        
        return scroll_area

    def show_sliding_panel(self, content_widget, title, button_name):
        
        # If same button clicked while visible → toggle close
        if self.sliding_panel and self.sliding_panel.is_visible and self.current_open_panel == button_name:
            self.hide_sliding_panel()
            self.current_open_panel = None
            return

        # If panel exists and is visible but a different button was clicked → IMMEDIATE SWAP (no slide-out/in)
        if self.sliding_panel and self.sliding_panel.is_visible and self.current_open_panel != button_name:
            try:
                self.sliding_panel.animation.stop()
            except:
                pass
            self.sliding_panel.is_animating = False

            # Prepare content (wrap in scroll area for short panels)
            target = self.create_scrollable_content(content_widget) if (content_widget and self.sliding_panel.panel_height < 700) else content_widget

            # Replace content immediately
            self.sliding_panel.clear_content()
            if target:
                # Make responsive and add
                try:
                    self.sliding_panel.make_content_responsive(target)
                except:
                    pass
                self.sliding_panel.content_layout.addWidget(target)

            # Ensure sizing/position and keep it visible
            self.sliding_panel.update_responsive_sizing()
            self.sliding_panel.reposition_panel()
            self.sliding_panel.show()
            self.sliding_panel.raise_()

            self.current_open_panel = button_name
            return

        # Create sliding panel if it doesn't exist
        if not self.sliding_panel:
            parent = self.parent_widget
            if not parent:
                parent = self.parent()
                while parent and not hasattr(parent, 'grid_widget'):
                    parent = parent.parent()
            if parent:
                self.sliding_panel = SlidingPanel(parent)
                self.setup_parent_monitoring(parent)
                if hasattr(parent, 'grid_widget') and parent.grid_widget.layout():
                    parent.grid_widget.layout().addWidget(self.sliding_panel)
                else:
                    print("Could not add sliding panel to layout")
            else:
                print("Could not find parent widget")

        # First open → slide in
        if self.sliding_panel:
            target = self.create_scrollable_content(content_widget) if (content_widget and self.sliding_panel.panel_height < 700) else content_widget
            self.sliding_panel.slide_in(target, title)
            self.current_open_panel = button_name
        else:
            print("Sliding panel is None") 

    def hide_sliding_panel(self):
        if self.sliding_panel and self.sliding_panel.is_visible:
            self.sliding_panel.slide_out()
            self.current_open_panel = None

    # ----------------------------- Save ECG -----------------------------

    # Modified methods to use sliding panel
    def show_save_ecg(self):
        # Ensure we have access to the parent widget with ECG data
        if not hasattr(self, 'parent_widget') or not self.parent_widget:
            # Try to find the parent widget
            parent = self.parent()
            while parent and not hasattr(parent, 'data'):
                parent = parent.parent()
            if parent:
                self.parent_widget = parent

        # Ensure sliding panel exists BEFORE creating content (so margins/spacing are correct)
        if not self.sliding_panel:
            parent = self.parent_widget
            if not parent:
                parent = self.parent()
                while parent and not hasattr(parent, 'grid_widget'):
                    parent = parent.parent()
            if parent:
                self.sliding_panel = SlidingPanel(parent)
                self.setup_parent_monitoring(parent)
                if hasattr(parent, 'grid_widget') and parent.grid_widget.layout():
                    parent.grid_widget.layout().addWidget(self.sliding_panel)

        # Update responsive sizing so margin_size/spacing_size are current
        if self.sliding_panel:
            self.sliding_panel.update_responsive_sizing()
        
        content_widget = self.create_save_ecg_content()
        self.show_sliding_panel(content_widget, "Save ECG Details", "Save ECG")

    def get_user_specific_patient_file(self):
        """Get user-specific patient details file path"""
        username = "default"
        
        # Try to get username from dashboard
        if self.dashboard and hasattr(self.dashboard, 'username') and self.dashboard.username:
            username = self.dashboard.username
        
        # Sanitize username for file name (remove special characters)
        safe_username = "".join(c for c in username if c.isalnum() or c in ('_', '-')).lower()
        return f"patient_details_{safe_username}.json"

    def create_save_ecg_content(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Responsive margins and spacing
        margin_size = getattr(self.sliding_panel, 'margin_size', 30) if self.sliding_panel else 30
        spacing_size = getattr(self.sliding_panel, 'spacing_size', 20) if self.sliding_panel else 20
        
        layout.setContentsMargins(margin_size, margin_size, margin_size, margin_size)
        layout.setSpacing(spacing_size)

        # Responsive title with dynamic font size
        title = QLabel("Save ECG Details")
        title_font_size = max(16, min(24, int(margin_size * 0.8)))
        title.setStyleSheet(f"""
            QLabel {{
                font: bold {title_font_size}pt 'Arial';
                color: white;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #ff6600, stop:1 #ff8c42);
                border: 2px solid #343434;
                border-radius: 15px;
                padding: {max(15, margin_size-10)}px;
                margin: {max(5, margin_size-15)}px;
            }}
        """)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Main form container with responsive styling
        form_frame = QFrame()
        form_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #ffffff, stop:1 #f8f9fa);
                border: 2px solid #e0e0e0;
                border-radius: 15px;
                padding: 20px;
                margin: 10px;
            }
        """)
        form_layout = QGridLayout(form_frame)
        form_layout.setSpacing(max(8, spacing_size-5))
        # Make right column grow with window size
        try:
            form_layout.setColumnStretch(0, 1)
            form_layout.setColumnStretch(1, 3)
        except Exception:
            pass
        
        labels = ["Org.", "Doctor", "Patient Name"]
        entries = {}

        # Responsive form fields
        for i, label in enumerate(labels):
            lbl = QLabel(label)
            label_font_size = max(12, min(18, int(margin_size * 0.6)))
            lbl.setStyleSheet(f"""
                QLabel {{
                    font: bold {label_font_size}pt Arial;
                    color: #000000;
                    background: #ffffff;
                    padding: 6px;
                    min-width: {max(100, int(margin_size * 3.5))}px;
                    min-height: {max(30, int(margin_size * 1.0))}px;
                    border: 1px solid #e0e0e0;
                    border-radius: 5px;
                    margin: 2px;
                }}
            """)
            form_layout.addWidget(lbl, i, 0)

            entry = QLineEdit()
            entry_font_size = max(10, min(13, int(margin_size * 0.4)))
            entry.setStyleSheet(f"""
                QLineEdit {{
                    font: {entry_font_size}pt Arial;
                    padding: {max(6, int(margin_size * 0.25))}px;
                    border: 2px solid #e0e0e0;
                    border-radius: 8px;
                    background: white;
                    color: #2c3e50;
                }}
                QLineEdit:focus {{
                    border: 2px solid #343434;
                    background: #fff8f0;
                }}
                QLineEdit:hover {{
                    border: 2px solid #ffb347;
                    background: #fafafa;
                }}
            """)
            
            # Responsive entry field sizes (expand horizontally)
            entry_height = max(30, int(margin_size * 1.0))
            entry.setMinimumHeight(entry_height)
            entry.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            form_layout.addWidget(entry, i, 1)
            entries[label] = entry
        
        entries["Doctor"].setMaxLength(20)
        entries["Patient Name"].setMaxLength(20)

        # Age field with responsive sizing
        lbl_age = QLabel("Age")
        lbl_age.setStyleSheet(f"""
            QLabel {{
                font: bold {label_font_size}pt Arial;
                color: #000000;
                background: #ffffff;
                padding: 6px;
                min-width: {max(100, int(margin_size * 3.5))}px;
                min-height: {max(30, int(margin_size * 1.0))}px;
                border: 1px solid #e0e0e0;
                border-radius: 5px;
                margin: 2px;
            }}
        """)
        form_layout.addWidget(lbl_age, 3, 0)

        age_entry = QLineEdit()
        age_entry.setValidator(QIntValidator(0, 120, age_entry))
        age_entry.setStyleSheet(f"""
            QLineEdit {{
                font: {entry_font_size}pt Arial;
                padding: {max(6, int(margin_size * 0.25))}px;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                background: white;
                color: #2c3e50;
            }}
            QLineEdit:focus {{
                border: 2px solid #343434;
                background: #fff8f0;
            }}
            QLineEdit:hover {{
                border: 2px solid #ffb347;
                background: #fafafa;
            }}
        """)
        
        age_height = max(30, int(margin_size * 1.0))
        age_entry.setMinimumHeight(age_height)
        age_entry.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        form_layout.addWidget(age_entry, 3, 1)
        entries["Age"] = age_entry

        # Gender field with responsive sizing
        lbl_gender = QLabel("Gender")
        lbl_gender.setStyleSheet(f"""
            QLabel {{
                font: bold {label_font_size}pt Arial;
                color: #000000;
                background: #ffffff;
                padding: 6px;
                min-width: {max(100, int(margin_size * 3.5))}px;
                min-height: {max(30, int(margin_size * 1.0))}px;
                border: 1px solid #e0e0e0;
                border-radius: 5px;
                margin: 2px;
            }}
        """)
        form_layout.addWidget(lbl_gender, 4, 0)

        gender_menu = QComboBox()
        gender_menu.addItems(["Select", "Male", "Female", "Other"])
        gender_menu.setStyleSheet(f"""
            QComboBox {{
                font: {entry_font_size}pt Arial;
                padding: {max(6, int(margin_size * 0.25))}px;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                background: white;
                color: #2c3e50;
            }}
            QComboBox:focus {{
                border: 2px solid #343434;
                background: #fff8f0;
            }}
            QComboBox:hover {{
                border: 2px solid #ffb347;
                background: #fafafa;
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 4px solid #ff6600;
                margin-right: 8px;
            }}
            QComboBox QAbstractItemView {{
                background: white;
                border: 2px solid #ff6600;
                border-radius: 8px;
                selection-background-color: #ff6600;
                selection-color: white;
                outline: none;
                font: {entry_font_size}pt Arial;
                padding: 6px;
                margin-left: -15px;
                margin-right: -15px;
            }}
            QComboBox QAbstractItemView::item {{
                padding: 6px 10px;
                border-radius: 5px;
                margin: 2px;
                min-height: 20px;
            }}
            QComboBox QAbstractItemView::item:hover {{
                background: #fff0e0;
                color: #ff6600;
            }}
            QComboBox QAbstractItemView::item:selected {{
                background: #ff6600;
                color: white;
                font-weight: bold;
            }}
        """)
        
        gender_height = max(30, int(margin_size * 1.0))
        gender_menu.setMinimumHeight(gender_height)
        gender_menu.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        form_layout.addWidget(gender_menu, 4, 1)

        # Prefill previously saved values if available (user-specific)
        try:
            prefill = None
            user_file = self.get_user_specific_patient_file()
            
            # 1) Use in-memory cached details if present
            if hasattr(self, "patient_details") and isinstance(self.patient_details, dict):
                prefill = self.patient_details
            # 2) Else attempt to load from user-specific disk cache to persist across restarts
            if prefill is None:
                try:
                    with open(user_file, "r") as jf:
                        prefill = json.load(jf)
                        # Cache in memory for subsequent opens during this session
                        setattr(self, "patient_details", prefill)
                except Exception:
                    prefill = None

            if prefill:
                pd = prefill
                # Org. (optional in cached data)
                if "Org." in pd and pd["Org."]:
                    entries["Org."].setText(pd["Org."]) 
                # Doctor
                if "doctor" in pd and pd["doctor"]:
                    entries["Doctor"].setText(pd["doctor"]) 
                # Patient Name
                first = pd.get("first_name", "") or ""
                last = pd.get("last_name", "") or ""
                full_name = (first + (" " + last if last else "")).strip()
                if full_name:
                    entries["Patient Name"].setText(full_name)
                # Age
                if "age" in pd and pd["age"] is not None:
                    entries["Age"].setText(str(pd["age"]))
                # Gender
                if "gender" in pd and pd["gender"]:
                    idx = gender_menu.findText(str(pd["gender"]))
                    if idx != -1:
                        gender_menu.setCurrentIndex(idx)
        except Exception:
            pass

        layout.addWidget(form_frame)

        # Submit button
        submit_btn = QPushButton("Save ECG")
        submit_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #28a745, stop:1 #20c997);
                color: white;
                border: 2px solid #28a745;
                border-radius: 10px;
                padding: {max(10, int(margin_size * 0.4))}px;
                font: bold {max(12, int(margin_size * 0.4))}pt Arial;
                min-height: {max(35, int(margin_size * 1.2))}px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #20c997, stop:1 #28a745);
                border: 2px solid #20c997;
            }}
            QPushButton:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #1e7e34, stop:1 #1c7430);
                border: 2px solid #1e7e34;
            }}
        """)
        submit_btn.clicked.connect(lambda: self.submit_ecg_details(entries, gender_menu))
        submit_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(submit_btn)

        return widget

    def submit_ecg_details(self, entries, gender_menu):
        values = {label: entries[label].text().strip() for label in ["Org.", "Doctor", "Patient Name", "Age"]}
        values["Gender"] = gender_menu.currentText()

        if any(v == "" for v in values.values()) or values["Gender"] == "Select":
            QMessageBox.warning(self.parent(), "Missing Data", "Please fill all the fields and select gender.")
            return

        # Store patient details on the menu and dashboard for PDF generation
        try:
            from datetime import datetime
            name = values["Patient Name"]
            first, *rest = name.split()
            patient_details = {
                "first_name": first,
                "last_name": " ".join(rest),
                "age": values["Age"],
                "gender": values["Gender"],
                "doctor": values["Doctor"],
                "Org.": values.get("Org.", ""),
                "patient_name": values.get("Patient Name", ""),
                "date_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            setattr(self, "patient_details", patient_details)
            if self.dashboard:
                setattr(self.dashboard, "patient_details", patient_details)
            # Persist last details to user-specific disk file so they survive app restarts
            try:
                user_file = self.get_user_specific_patient_file()
                with open(user_file, "w") as jf:
                    json.dump(patient_details, jf, indent=2)
            except Exception as disk_err:
                print(f"⚠️ Could not persist patient details: {disk_err}")
        except Exception as e:
            print(f"⚠️ Could not cache patient details: {e}")

        try:
            with open("ecg_data.txt", "a") as file:
                file.write(f"{values['Org.']}, {values['Doctor']}, {values['Patient Name']}, {values['Age']}, {values['Gender']}\n")
            QMessageBox.information(self.parent(), "Saved", "ECG details saved successfully!")
            # Close the panel after successful save (values remain persisted for next open)
            self.hide_sliding_panel()
        except Exception as e:
            QMessageBox.critical(self.parent(), "Error", f"Failed to save: {e}")

    # ----------------------------- Open ECG -----------------------------

    def show_open_ecg(self):
        """Show open ECG file dialog"""
        content_widget = self.create_open_ecg_content()
        self.show_sliding_panel(content_widget, "Open ECG File", "Open ECG")

    def create_open_ecg_content(self):
        # Create a simple open ECG interface
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Responsive margins and spacing
        margin_size = getattr(self.sliding_panel, 'margin_size', 20) if self.sliding_panel else 20
        spacing_size = getattr(self.sliding_panel, 'spacing_size', 15) if self.sliding_panel else 15
        
        layout.setContentsMargins(margin_size, margin_size, margin_size, margin_size)
        layout.setSpacing(spacing_size)

        # Professional title
        title = QLabel("Open ECG File")
        title_font_size = max(16, min(22, int(margin_size * 0.8)))
        title.setStyleSheet(f"""
            QLabel {{
                font: bold {title_font_size}pt Arial;
                color: white;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #ff6600, stop:1 #ff8c42);
                border: 2px solid #ff6600;
                border-radius: 12px;
                padding: {max(12, int(margin_size * 0.6))}px;
                margin: {max(8, int(margin_size * 0.4))}px;
                min-height: {max(30, int(margin_size * 1.5))}px;
            }}
        """)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # File selection container
        file_frame = QFrame()
        file_frame.setStyleSheet("""
            QFrame {
                background: white;
                border: 2px solid #e0e0e0;
                border-radius: 10px;
                padding: 20px;
                margin: 10px;
            }
        """)
        file_layout = QVBoxLayout(file_frame)
        file_layout.setSpacing(15)

        # File path display
        path_label = QLabel("Selected File:")
        path_label.setStyleSheet(f"""
            QLabel {{
                font: bold {max(11, int(margin_size * 0.55))}pt Arial;
                color: #2c3e50;
                background: transparent;
                padding: 5px;
            }}
        """)
        file_layout.addWidget(path_label)
        
        self.file_path_display = QLabel("No file selected")
        self.file_path_display.setStyleSheet(f"""
            QLabel {{
                font: {max(10, int(margin_size * 0.5))}pt Arial;
                color: #666;
                background: #f8f9fa;
                padding: 10px;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                min-height: {max(25, int(margin_size * 1.2))}px;
            }}
        """)
        file_layout.addWidget(self.file_path_display)

        # File format selection
        format_label = QLabel("File Format:")
        format_label.setStyleSheet(f"""
            QLabel {{
                font: bold {max(11, int(margin_size * 0.55))}pt Arial;
                color: #2c3e50;
                background: transparent;
                padding: 5px;
            }}
        """)
        file_layout.addWidget(format_label)
        
        self.format_combo = QComboBox()
        self.format_combo.addItems(["Auto-detect", "CSV", "TXT", "JSON", "XML", "DICOM"])
        self.format_combo.setStyleSheet(f"""
            QComboBox {{
                font: {max(10, int(margin_size * 0.5))}pt Arial;
                color: #2c3e50;
                background: white;
                border: 2px solid #e0e0e0;
                border-radius: 6px;
                padding: 8px;
                min-height: {max(30, int(margin_size * 1.5))}px;
            }}
            QComboBox:hover {{
                border: 2px solid #ffb347;
            }}
            QComboBox:focus {{
                border: 2px solid #ff6600;
            }}
        """)
        file_layout.addWidget(self.format_combo)

        layout.addWidget(file_frame)

        # Buttons
        btn_frame = QFrame()
        btn_frame.setStyleSheet("""
            QFrame {
                background: transparent;
                margin: 10px;
            }
        """)
        btn_layout = QHBoxLayout(btn_frame)
        btn_layout.setSpacing(max(10, int(margin_size * 0.5)))

        # Responsive button sizing
        button_width = max(100, min(140, int(margin_size * 5)))
        button_height = max(35, min(45, int(margin_size * 1.8)))

        # Browse button
        browse_btn = QPushButton("Browse")
        browse_btn.setFixedSize(button_width, button_height)
        browse_btn.setStyleSheet(f"""
            QPushButton {{
                font: bold {max(11, int(margin_size * 0.55))}pt Arial;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #17a2b8, stop:0.5 #138496, stop:1 #17a2b8);
                color: white;
                border: 2px solid #17a2b8;
                border-radius: 8px;
                padding: 8px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #138496, stop:0.5 #17a2b8, stop:1 #138496);
                border: 2px solid #138496;
            }}
        """)
        browse_btn.clicked.connect(self.browse_ecg_file)
        btn_layout.addWidget(browse_btn)

        # Open button
        open_btn = QPushButton("Open")
        open_btn.setFixedSize(button_width, button_height)
        open_btn.setStyleSheet(f"""
            QPushButton {{
                font: bold {max(11, int(margin_size * 0.55))}pt Arial;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #4CAF50, stop:0.5 #45a049, stop:1 #4CAF50);
                color: white;
                border: 2px solid #4CAF50;
                border-radius: 8px;
                padding: 8px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #45a049, stop:0.5 #4CAF50, stop:1 #45a049);
                border: 2px solid #45a049;
            }}
        """)
        open_btn.clicked.connect(self.open_ecg_file)
        btn_layout.addWidget(open_btn)

        # Cancel button
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedSize(button_width, button_height)
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                font: bold {max(11, int(margin_size * 0.55))}pt Arial;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #f44336, stop:0.5 #d32f2f, stop:1 #f44336);
                color: white;
                border: 2px solid #f44336;
                border-radius: 8px;
                padding: 8px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #d32f2f, stop:0.5 #f44336, stop:1 #d32f2f);
                border: 2px solid #d32f2f;
            }}
        """)
        cancel_btn.clicked.connect(self.hide_sliding_panel)
        btn_layout.addWidget(cancel_btn)

        layout.addWidget(btn_frame)
        
        return widget

    def browse_ecg_file(self):
        """Browse for ECG file"""
        from PyQt5.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getOpenFileName(
            self.parent(),
            "Select ECG File",
            "",
            "ECG Files (*.csv *.txt *.json *.xml *.dcm);;All Files (*.*)"
        )
        if file_path:
            self.file_path_display.setText(file_path)
            self.file_path_display.setStyleSheet(f"""
                QLabel {{
                    font: {max(10, int(getattr(self.sliding_panel, 'margin_size', 20) * 0.5))}pt Arial;
                    color: #2c3e50;
                    background: #e8f5e8;
                    padding: 10px;
                    border: 1px solid #4CAF50;
                    border-radius: 6px;
                    min-height: {max(25, int(getattr(self.sliding_panel, 'margin_size', 20) * 1.2))}px;
                }}
            """)

    def open_ecg_file(self):
        """Open the selected ECG file"""
        file_path = self.file_path_display.text()
        if file_path == "No file selected":
            QMessageBox.warning(self.parent(), "No File", "Please select a file first!")
            return
        
        try:
            # Here you would implement the actual file opening logic
            QMessageBox.information(self.parent(), "Success", f"ECG file opened successfully!\nFile: {file_path}")
            self.hide_sliding_panel()
        except Exception as e:
            QMessageBox.critical(self.parent(), "Error", f"Failed to open file: {str(e)}")

    # ----------------------------- Working Mode -----------------------------

    def show_working_mode(self):
        content_widget = self.create_working_mode_content()
        self.show_sliding_panel(content_widget, "Working Mode Settings", "Working Mode")

    def create_working_mode_content(self):
        # Get current settings from settings manager
        if not self.settings_manager:
            self.settings_manager = SettingsManager()
        
        # Define sections for working mode
        sections = [
            {
                'title': 'Wave Speed',
                'options': [("12.5mm/s", "12.5"), ("25.0mm/s", "25"), ("50.0mm/s", "50")],
                'setting_key': 'wave_speed'
            },
            {
                'title': 'Wave Gain',
                'options': [("2.5mm/mV", "2.5"), ("5mm/mV", "5"), ("10mm/mV", "10"), ("20mm/mV", "20")],
                'setting_key': 'wave_gain'
            },
            {
                'title': 'Sampling Mode',
                'options': [("Simultaneous", "Simultaneous"), ("Sequence", "Sequence")],
                'setting_key': 'sampling_mode'
            },
            {
                'title': 'Priority Storage',
                'options': [("U Disk", "U"), ("SD Card", "SD")],
                'setting_key': 'storage'
            }
        ]
        
        # Define buttons
        buttons = [
            {
                'text': 'OK',
                'action': self.save_working_mode_settings,
                'style': 'primary'
            },
            {
                'text': 'Exit',
                'action': self.hide_sliding_panel,
                'style': 'danger'
            }
        ]
        
        return self.create_unified_control_panel("Working Mode Settings", sections, buttons)

    def on_setting_changed(self, key, value):
    
        print(f"ECG Menu: Setting {key} changed to {value}")
    
        # Save to settings manager
        self.settings_manager.set_setting(key, value)
        
        if hasattr(self, 'settings_changed_callback') and self.settings_changed_callback:
            print(f"Calling settings callback for {key}={value}")
            self.settings_changed_callback(key, value)
        else:
            print("No settings callback found!")
        
        # Also notify parent ECG test page if available
        if hasattr(self.parent(), 'on_settings_changed'):
            print(f"Calling parent on_settings_changed for {key}={value}")
            self.parent().on_settings_changed(key, value)
        else:
            print("No parent on_settings_changed found!")
        
        # For wave speed and gain, apply immediate visual feedback
        if key in ["wave_speed", "wave_gain"]:
            print(f"Applied {key}: {value}")
            try:
                if hasattr(self.parent(), 'ecg_test_page') and self.parent().ecg_test_page:
                    self.parent().ecg_test_page.update_plots()
            except Exception as e:
                print(f"Immediate refresh error: {e}")

    def save_working_mode_settings(self):
        
        QMessageBox.information(self.parent(), "Saved", "Working mode settings saved and applied to ECG display")
        self.hide_sliding_panel()

    # ----------------------------- Printer Setup -----------------------------

    def show_printer_setup(self):
        content_widget = self.create_printer_setup_content()
        self.show_sliding_panel(content_widget, "Printer Setup", "Printer Setup")

    def create_printer_setup_content(self):

        # Get current settings from settings manager
        if not self.settings_manager:
            self.settings_manager = SettingsManager()

        # Define sections for printer setup
        sections = [
            {
                'title': 'Analysis Result',
                'options': [("On", "on"), ("Off", "off")],
                'setting_key': 'printer_analysis_result'
            },
            {
                'title': 'Average Wave',
                'options': [("On", "on"), ("Off", "off")],
                'setting_key': 'printer_average_wave'
            },
            {
                'title': 'Lead Sequence',
                'options': [("Standard", "Standard"), ("Cabrera", "Cabrera")],
                'setting_key': 'lead_sequence'
            },
            {
                'title': 'Selected Rhythm Lead',
                'options': [("On", "on"), ("Off", "off")],
                'setting_key': 'printer_rhythm_lead'
            },
            {
                'title': 'Sensitivity',
                'options': [("High", "High"), ("Medium", "Medium"), ("Low", "Low")],
                'setting_key': 'printer_sensitivity'
            }
        ]
        
        # Define buttons
        buttons = [
            {
                'text': 'Save',
                'action': self.save_printer_settings,
                'style': 'primary'
            },
            {
                'text': 'Exit',
                'action': self.hide_sliding_panel,
                'style': 'danger'
            }
        ]
        
        return self.create_unified_control_panel("Printer Setup", sections, buttons)

    def on_printer_setting_changed(self, value):
        print(f"Printer setting changed to: {value}")

    def save_printer_settings(self):
        QMessageBox.information(self.parent(), "Saved", "Printer settings saved successfully!")
        self.hide_sliding_panel()

    # ----------------------------- Set Filter -----------------------------

    def show_set_filter(self):
        """Show filter settings panel"""
        content_widget = self.create_filter_content()
        self.show_sliding_panel(content_widget, "Filter Settings", "Set Filter")

    def create_filter_content(self):

        # Get current settings from settings manager
        if not self.settings_manager:
            self.settings_manager = SettingsManager()

        # Define sections for filter settings
        sections = [
            {
                'title': 'Low Pass Filter',
                'options': [("Off", "off"), ("25Hz", "25"), ("50Hz", "50"), ("100Hz", "100")],
                'setting_key': 'filter_low_pass'
            },
            {
                'title': 'High Pass Filter',
                'options': [("Off", "off"), ("0.05Hz", "0.05"), ("0.5Hz", "0.5"), ("1Hz", "1")],
                'setting_key': 'filter_high_pass'
            },
            {
                'title': 'Notch Filter',
                'options': [("Off", "off"), ("50Hz", "50"), ("60Hz", "60")],
                'setting_key': 'filter_notch'
            },
            {
                'title': 'Smoothing',
                'options': [("Off", "off"), ("Low", "low"), ("Medium", "medium"), ("High", "high")],
                'setting_key': 'filter_smoothing'
            }
        ]
        
        # Define buttons
        buttons = [
            {
                'text': 'Apply',
                'action': self.apply_filter_settings,
                'style': 'primary'
            },
            {
                'text': 'Cancel',
                'action': self.hide_sliding_panel,
                'style': 'danger'
            }
        ]
        
        return self.create_unified_control_panel("Filter Settings", sections, buttons)

    def apply_filter_settings(self):
        QMessageBox.information(self.parent(), "Applied", "Filter settings applied successfully!")
        self.hide_sliding_panel()

    def show_system_setup(self):
        
        content_widget = self.create_system_setup_content()
        self.show_sliding_panel(content_widget, "System Setup", "System Setup")

    def show_load_default(self):
        
        content_widget = self.create_load_default_content()
        self.show_sliding_panel(content_widget, "Load Default Settings", "Load Default")

    def show_version_info(self):
        
        content_widget = self.create_version_info_content()
        self.show_sliding_panel(content_widget, "Version Information", "Version")

    def show_factory_maintain(self):
        
        content_widget = self.create_factory_maintain_content()
        self.show_sliding_panel(content_widget, "Factory Maintenance", "Factory Maintain")

    # ----------------------------- System Setup -----------------------------

    def create_system_setup_content(self):

        # Get current settings from settings manager
        if not self.settings_manager:
            self.settings_manager = SettingsManager()

        # Define sections for system setup
        sections = [
            {
                'title': 'BEAT VOL',
                'options': [("On", "on"), ("Off", "off")],
                'setting_key': 'system_beat_vol'
            },
            {
                'title': 'ALARM VOL',
                'options': [("On", "on"), ("Off", "off")],
                'setting_key': 'system_alarm_vol'
            },
            {
                'title': 'KEY TONE',
                'options': [("On", "on"), ("Off", "off")],
                'setting_key': 'system_key_tone'
            },
            {
                'title': 'AUTO POWER OFF',
                'options': [("5min", "5"), ("10min", "10"), ("15min", "15"), ("Off", "off")],
                'setting_key': 'system_auto_power_off'
            },
            {
                'title': 'LANGUAGE',
                'options': [("English", "en"), ("Spanish", "es"), ("French", "fr")],
                'setting_key': 'system_language'
            },
            {
                'title': 'DATE FORMAT',
                'options': [("MM/DD/YYYY", "mmdd"), ("DD/MM/YYYY", "ddmm"), ("YYYY/MM/DD", "yyyymm")],
                'setting_key': 'system_date_format'
            }
        ]
        
        # Define buttons
        buttons = [
            {
                'text': 'Save',
                'action': self.save_system_settings,
                'style': 'primary'
            },
            {
                'text': 'Exit',
                'action': self.hide_sliding_panel,
                'style': 'danger'
            }
        ]
        
        return self.create_unified_control_panel("System Setup", sections, buttons)

    def save_system_settings(self):
        QMessageBox.information(self.parent(), "Saved", "System settings saved successfully!")
        self.hide_sliding_panel()

    # ----------------------------- Load Default -----------------------------

    def create_load_default_content(self):

        # Get current settings from settings manager
        if not self.settings_manager:
            self.settings_manager = SettingsManager()

        # Define sections for load default
        sections = [
            {
                'title': 'ECG Settings',
                'options': [("Load Defaults", "ecg"), ("Keep Current", "keep")],
                'setting_key': 'load_default_ecg'
            },
            {
                'title': 'Display Settings',
                'options': [("Load Defaults", "display"), ("Keep Current", "keep")],
                'setting_key': 'load_default_display'
            },
            {
                'title': 'System Settings',
                'options': [("Load Defaults", "system"), ("Keep Current", "keep")],
                'setting_key': 'load_default_system'
            },
            {
                'title': 'All Settings',
                'options': [("Load All Defaults", "all"), ("Keep All Current", "keep")],
                'setting_key': 'load_default_all'
            }
        ]
        
        # Define buttons
        buttons = [
            {
                'text': 'Select',
                'action': self.load_default_settings,
                'style': 'primary'
            },
            {
                'text': 'Cancel',
                'action': self.hide_sliding_panel,
                'style': 'danger'
            }
        ]
        
        return self.create_unified_control_panel("Load Default Settings", sections, buttons)

    def load_default_settings(self):
        QMessageBox.information(self.parent(), "Loaded", "Default settings loaded successfully!")
        self.hide_sliding_panel()

    # ----------------------------- Version Info -----------------------------

    def create_version_info_content(self):
        # Create a simple version info display
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Responsive margins and spacing
        margin_size = getattr(self.sliding_panel, 'margin_size', 20) if self.sliding_panel else 20
        spacing_size = getattr(self.sliding_panel, 'spacing_size', 15) if self.sliding_panel else 15
        
        layout.setContentsMargins(margin_size, margin_size, margin_size, margin_size)
        layout.setSpacing(spacing_size)

        # Professional title
        title = QLabel("Version Information")
        title_font_size = max(16, min(22, int(margin_size * 0.8)))
        title.setStyleSheet(f"""
            QLabel {{
                font: bold {title_font_size}pt Arial;
                color: white;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #ff6600, stop:1 #ff8c42);
                border: 2px solid #ff6600;
                border-radius: 12px;
                padding: {max(12, int(margin_size * 0.6))}px;
                margin: {max(8, int(margin_size * 0.4))}px;
                min-height: {max(30, int(margin_size * 1.5))}px;
            }}
        """)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Version info container with scroll area for better handling
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                background: #f0f0f0;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: #ff6600;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #ff8800;
            }
        """)
        
        info_frame = QFrame()
        info_frame.setStyleSheet("""
            QFrame {
                background: white;
                border: 2px solid #e0e0e0;
                border-radius: 10px;
                padding: 20px;
                margin: 10px;
            }
        """)
        info_layout = QVBoxLayout(info_frame)
        info_layout.setSpacing(15)

        # Version details
        version_info = [
            ("Software Version", "V 1.1.1"),
            ("Hardware Version", "V 1.5.2"),
            ("Firmware Version", "V.3.0.1"),
            ("Build Date", "2024-08-26"),
            ("Manufacturer", "Modular ECG Systems"),
            ("Model", "ECG-121 Pro"),
            ("Serial Number", "MF-2024-001"),
            ("License", "Professional Edition")
        ]

        # Calculate better minimum widths based on content
        max_label_width = max(len(label) for label, _ in version_info) * 8 + 20  # 8 pixels per char + padding
        max_value_width = max(len(value) for _, value in version_info) * 8 + 20

        for label, value in version_info:
            row = QHBoxLayout()
            row.setSpacing(10)  # Consistent spacing between label and value
            
            # Label with better sizing
            lbl = QLabel(label)
            lbl.setWordWrap(True)
            lbl.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred)
            lbl.setStyleSheet(f"""
                QLabel {{
                    font: bold {max(11, int(margin_size * 0.55))}pt Arial;
                    color: #2c3e50;
                    background: #f8f9fa;
                    padding: {max(8, int(margin_size * 0.4))}px;
                    border: 1px solid #e0e0e0;
                    border-radius: 6px;
                    min-width: {max(max_label_width, 140)}px;
                    max-width: 200px;
                }}
            """)
            
            # Value with better sizing
            val = QLabel(value)
            val.setWordWrap(True)
            val.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred)
            val.setStyleSheet(f"""
                QLabel {{
                    font: {max(10, int(margin_size * 0.5))}pt Arial;
                    color: #ff6600;
                    background: white;
                    padding: {max(8, int(margin_size * 0.4))}px;
                    border: 1px solid #e0e0e0;
                    border-radius: 6px;
                    min-width: {max(max_value_width, 120)}px;
                    max-width: 250px;
                }}
            """)
            
            row.addWidget(lbl, 0, Qt.AlignLeft)
            row.addWidget(val, 0, Qt.AlignLeft)
            row.addStretch()
            info_layout.addLayout(row)

        scroll_area.setWidget(info_frame)
        layout.addWidget(scroll_area)

        # Exit button
        exit_btn = QPushButton("Close")
        exit_btn.setStyleSheet(f"""
            QPushButton {{
                font: bold {max(11, int(margin_size * 0.55))}pt Arial;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #6c757d, stop:0.5 #495057, stop:1 #6c757d);
                color: white;
                border: 2px solid #6c757d;
                border-radius: 8px;
                padding: {max(10, int(margin_size * 0.5))}px;
                min-height: {max(35, int(margin_size * 1.8))}px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #495057, stop:0.5 #6c757d, stop:1 #495057);
                border: 2px solid #495057;
            }}
        """)
        exit_btn.clicked.connect(self.hide_sliding_panel)
        layout.addWidget(exit_btn, alignment=Qt.AlignCenter)
        
        return widget
    
    # ----------------------------- Factory Maintain -----------------------------

    def create_factory_maintain_content(self):

        # Get current settings from settings manager
        if not self.settings_manager:
            self.settings_manager = SettingsManager()

        # Define sections for factory maintenance
        sections = [
            {
                'title': 'Calibration',
                'options': [("Calibrate Now", "calibrate"), ("Skip", "skip")],
                'setting_key': 'factory_calibration'
            },
            {
                'title': 'Self Test',
                'options': [("Run Test", "test"), ("Skip", "skip")],
                'setting_key': 'factory_self_test'
            },
            {
                'title': 'Memory Reset',
                'options': [("Reset All", "reset"), ("Keep Data", "keep")],
                'setting_key': 'factory_memory_reset'
            },
            {
                'title': 'Factory Reset',
                'options': [("Reset to Factory", "factory"), ("Cancel", "cancel")],
                'setting_key': 'factory_reset'
            }
        ]
        
        # Define buttons
        buttons = [
            {
                'text': 'Select',
                'action': self.execute_factory_maintenance,
                'style': 'primary'
            },
            {
                'text': 'Cancel',
                'action': self.hide_sliding_panel,
                'style': 'danger'
            }
        ]
        
        return self.create_unified_control_panel("Factory Maintenance", sections, buttons)

    def execute_factory_maintenance(self):
        QMessageBox.information(self.parent(), "Maintenance", "Factory maintenance completed successfully!")
        self.hide_sliding_panel()

    # ----------------------------- Exit -----------------------------

    def show_exit(self):
        """Show exit confirmation dialog"""
        content_widget = self.create_exit_content()
        self.show_sliding_panel(content_widget, "Exit Application", "Exit")

    def create_exit_content(self):
        # Create a simple exit confirmation
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Responsive margins and spacing
        margin_size = getattr(self.sliding_panel, 'margin_size', 20) if self.sliding_panel else 20
        spacing_size = getattr(self.sliding_panel, 'spacing_size', 15) if self.sliding_panel else 15
        
        layout.setContentsMargins(margin_size, margin_size, margin_size, margin_size)
        layout.setSpacing(spacing_size)

        # Professional title
        title = QLabel("Exit Application")
        title_font_size = max(16, min(22, int(margin_size * 0.8)))
        title.setStyleSheet(f"""
            QLabel {{
                font: bold {title_font_size}pt Arial;
                color: white;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #ff6600, stop:1 #ff8c42);
                border: 2px solid #ff6600;
                border-radius: 12px;
                padding: {max(12, int(margin_size * 0.6))}px;
                margin: {max(8, int(margin_size * 0.4))}px;
                min-height: {max(30, int(margin_size * 1.5))}px;
            }}
        """)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Confirmation message
        msg_frame = QFrame()
        msg_frame.setStyleSheet("""
            QFrame {
                background: white;
                border: 2px solid #e0e0e0;
                border-radius: 10px;
                padding: 20px;
                margin: 10px;
            }
        """)
        msg_layout = QVBoxLayout(msg_frame)
        
        confirm_msg = QLabel("Do you want to quit?")
        confirm_msg.setStyleSheet(f"""
            QLabel {{
                font: bold {max(12, int(margin_size * 0.6))}pt Arial;
                color: #2c3e50;
                background: transparent;
                padding: 10px;
                text-align: center;
            }}
        """)
        confirm_msg.setAlignment(Qt.AlignCenter)
        msg_layout.addWidget(confirm_msg)
        
        warning_msg = QLabel("⚠️ Any unsaved data will be lost!")
        warning_msg.setStyleSheet(f"""
            QLabel {{
                font: {max(10, int(margin_size * 0.5))}pt Arial;
                color: #e74c3c;
                background: #fdf2f2;
                padding: 8px;
                border: 1px solid #f5c6cb;
                border-radius: 6px;
                text-align: center;
            }}
        """)
        warning_msg.setAlignment(Qt.AlignCenter)
        msg_layout.addWidget(warning_msg)
        
        layout.addWidget(msg_frame)

        # Buttons
        btn_frame = QFrame()
        btn_frame.setStyleSheet("""
            QFrame {
                background: transparent;
                margin: 10px;
            }
        """)
        btn_layout = QHBoxLayout(btn_frame)
        btn_layout.setSpacing(max(10, int(margin_size * 0.5)))

        # Responsive button sizing
        button_width = max(100, min(140, int(margin_size * 5)))
        button_height = max(35, min(45, int(margin_size * 1.8)))

        # Cancel button
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedSize(button_width, button_height)
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                font: bold {max(11, int(margin_size * 0.55))}pt Arial;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #6c757d, stop:0.5 #495057, stop:1 #6c757d);
                color: white;
                border: 2px solid #6c757d;
                border-radius: 8px;
                padding: 8px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #495057, stop:0.5 #6c757d, stop:1 #495057);
                border: 2px solid #495057;
            }}
        """)
        cancel_btn.clicked.connect(self.hide_sliding_panel)
        btn_layout.addWidget(cancel_btn)

        # Exit button
        exit_btn = QPushButton("Exit")
        exit_btn.setFixedSize(button_width, button_height)
        exit_btn.setStyleSheet(f"""
            QPushButton {{
                font: bold {max(11, int(margin_size * 0.55))}pt Arial;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #f44336, stop:0.5 #d32f2f, stop:1 #f44336);
                color: white;
                border: 2px solid #f44336;
                border-radius: 8px;
                padding: 8px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #d32f2f, stop:0.5 #f44336, stop:1 #d32f2f);
                border: 2px solid #d32f2f;
            }}
        """)
        exit_btn.clicked.connect(self.confirm_exit)
        btn_layout.addWidget(exit_btn)

        layout.addWidget(btn_frame)
        
        return widget

    def confirm_exit(self):
        """Confirm and exit the application"""
        reply = QMessageBox.question(
            self.parent(), 
            'Exit Application', 
            'Are you absolutely sure you want to exit?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Set flag to indicate application exit
            if hasattr(self.parent(), 'parent') and hasattr(self.parent().parent(), '_exited_application'):
                self.parent().parent()._exited_application = True
            
            # Close main windows and exit application
            try:
                # Close the dashboard and all its child windows
                if hasattr(self.parent(), 'parent'):
                    dashboard = self.parent().parent()
                    if hasattr(dashboard, 'ecg_test_page') and dashboard.ecg_test_page:
                        dashboard.ecg_test_page.close()
                    dashboard.close()
                
                # Force exit the application
                QApplication.quit()
                sys.exit(0)
            except Exception as e:
                print(f"Error during exit: {e}")
                QApplication.quit()
                sys.exit(0)
        else:
            self.hide_sliding_panel()

    def refresh_ecg_graphs(self):
        """Refresh ECG graphs with latest data"""
        if not hasattr(self, 'ecg_graphs'):
            return
            
        # Get latest ECG data
        ecg_data = {}
        if hasattr(self, 'parent_widget') and self.parent_widget:
            if hasattr(self.parent_widget, 'data'):
                ecg_data = self.parent_widget.data
        else:
            # Try to find ECG data from the current parent
            current_parent = self.parent()
            while current_parent:
                if hasattr(current_parent, 'data') and current_parent.data:
                    ecg_data = current_parent.data
                    break
                current_parent = current_parent.parent()
        
        # Update each graph
        for lead, graph_info in self.ecg_graphs.items():
            if lead in ecg_data and len(ecg_data[lead]) > 0:
                # Get latest data
                data = ecg_data[lead][-500:] if len(ecg_data[lead]) > 500 else ecg_data[lead]
                x = np.arange(len(data))
                
                # Update the line data
                graph_info['line'].set_xdata(x)
                graph_info['line'].set_ydata(data)
                
                # Update canvas if available
                if graph_info['canvas']:
                    graph_info['canvas'].draw_idle()
        
        QMessageBox.information(self.parent(), "Updated", "ECG graphs refreshed with latest data!")

    def create_unified_control_panel(self, title, sections, buttons=None):
        """
        Create a unified, responsive control panel with consistent design
        sections: list of dicts with 'title', 'options', 'variable', 'setting_key'
        buttons: list of dicts with 'text', 'action', 'style' (optional)
        """
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Responsive margins and spacing
        margin_size = getattr(self.sliding_panel, 'margin_size', 20) if self.sliding_panel else 20
        spacing_size = getattr(self.sliding_panel, 'spacing_size', 15) if self.sliding_panel else 15
        
        layout.setContentsMargins(margin_size, margin_size, margin_size, margin_size)
        layout.setSpacing(spacing_size)

        # Professional title
        title_label = QLabel(title)
        title_font_size = max(16, min(22, int(margin_size * 0.8)))
        title_label.setStyleSheet(f"""
            QLabel {{
                font: bold {title_font_size}pt Arial;
                color: white;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #ff6600, stop:1 #ff8c42);
                border: 2px solid #ff6600;
                border-radius: 12px;
                padding: {max(12, int(margin_size * 0.6))}px;
                margin: {max(8, int(margin_size * 0.4))}px;
                min-height: {max(30, int(margin_size * 1.5))}px;
            }}
        """)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # Create scrollable area for content
        from PyQt5.QtWidgets import QScrollArea
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setMaximumHeight(500)  # Limit height for smaller screens
        
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(spacing_size)
        content_layout.setContentsMargins(5, 5, 5, 5)

        def add_section(section_data):
            group_box = QGroupBox(section_data['title'])
            group_box.setStyleSheet(f"""
                QGroupBox {{
                    font: bold {max(12, int(margin_size * 0.6))}pt Arial;
                    color: #2c3e50;
                    background: white;
                    border: 2px solid #ff6600;
                    border-radius: 10px;
                    padding: {max(8, int(margin_size * 0.4))}px;
                    margin: {max(5, int(margin_size * 0.25))}px;
                    margin-top: {max(18, int(margin_size * 1.0))}px;
                }}
                QGroupBox:title {{
                    subcontrol-origin: margin;
                    subcontrol-position: top left;
                    left: 12px;
                    top: 0px;
                    padding: 0 8px 0 8px;
                    color: #ff6600;
                    font-weight: bold;
                    background: white;
                    font-size: {max(11, int(margin_size * 0.55))}pt;
                }}
            """)
            
            # Use grid layout for better organization
            grid_layout = QGridLayout(group_box)
            grid_layout.setSpacing(8)
            grid_layout.setContentsMargins(8, 8, 8, 8)
            
            # Calculate optimal button size
            button_width = max(70, min(120, int(margin_size * 3.5)))
            button_height = max(25, min(35, int(margin_size * 1.3)))
            
            for i, (text, val) in enumerate(section_data['options']):
                btn = QRadioButton(text)
                btn.setStyleSheet(f"""
                    QRadioButton {{
                        font: bold {max(9, int(margin_size * 0.45))}pt Arial;
                        color: #2c3e50;
                        background: white;
                        padding: {max(4, int(margin_size * 0.2))}px;
                        border: 1px solid #e0e0e0;
                        border-radius: 6px;
                        min-width: {button_width}px;
                        min-height: {button_height}px;
                    }}
                    QRadioButton:hover {{
                        border: 2px solid #ffb347;
                        background: #fff8f0;
                    }}
                    QRadioButton:checked {{
                        border: 2px solid #ff6600;
                        background: #fff0e0;
                        color: #ff6600;
                        font-weight: bold;
                    }}
                    QRadioButton::indicator {{
                        width: {max(10, int(margin_size * 0.5))}px;
                        height: {max(10, int(margin_size * 0.5))}px;
                        border: 2px solid #e0e0e0;
                        border-radius: {max(5, int(margin_size * 0.25))}px;
                        background: white;
                        margin-left: 6px;
                        margin-right: 8px;
                    }}
                    QRadioButton::indicator:checked {{
                        border: 1px solid #ff6600;
                        background: #ff6600;
                    }}
                """)
                
                # Set checked state if variable exists
                if 'variable' in section_data and section_data['variable']:
                    btn.setChecked(section_data['variable'].get('value') == val)
                elif 'setting_key' in section_data and self.settings_manager:
                    # Load saved setting value
                    saved_value = self.settings_manager.get_setting(section_data['setting_key'])
                    btn.setChecked(saved_value == val)
                
                # Connect to appropriate handler
                if 'setting_key' in section_data:
                    btn.toggled.connect(lambda checked, v=val, key=section_data['setting_key']: 
                                     self.on_setting_changed(key, v) if checked else None)
                elif 'variable' in section_data:
                    btn.toggled.connect(lambda checked, v=val, var=section_data['variable']: 
                                     var.update({'value': v}) if checked else None)
                
                # Arrange in grid (2 columns for better space usage)
                row, col = divmod(i, 2)
                grid_layout.addWidget(btn, row, col)
            
            content_layout.addWidget(group_box)

        # Add all sections
        for section in sections:
            add_section(section)

        scroll_area.setWidget(content_widget)
        layout.addWidget(scroll_area)

        # Add buttons if provided
        if buttons:
            btn_frame = QFrame()
            btn_frame.setStyleSheet("""
                QFrame {
                    background: transparent;
                    margin: 10px;
                }
            """)
            btn_layout = QHBoxLayout(btn_frame)
            btn_layout.setSpacing(max(10, int(margin_size * 0.5)))

            # Responsive button sizing
            button_width = max(100, min(140, int(margin_size * 5)))
            button_height = max(35, min(45, int(margin_size * 1.8)))

            for btn_data in buttons:
                btn = QPushButton(btn_data['text'])
                btn.setFixedSize(button_width, button_height)
                
                # Default style if not specified
                style = btn_data.get('style', 'primary')
                if style == 'primary':
                    btn.setStyleSheet(f"""
                        QPushButton {{
                            font: bold {max(11, int(margin_size * 0.55))}pt Arial;
                            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                stop:0 #4CAF50, stop:0.5 #45a049, stop:1 #4CAF50);
                            color: white;
                            border: 2px solid #4CAF50;
                            border-radius: 8px;
                            padding: 8px;
                        }}
                        QPushButton:hover {{
                            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                stop:0 #45a049, stop:0.5 #4CAF50, stop:1 #45a049);
                            border: 2px solid #45a049;
                        }}
                    """)
                elif style == 'danger':
                    btn.setStyleSheet(f"""
                        QPushButton {{
                            font: bold {max(11, int(margin_size * 0.55))}pt Arial;
                            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                stop:0 #f44336, stop:0.5 #d32f2f, stop:1 #f44336);
                            color: white;
                            border: 2px solid #f44336;
                            border-radius: 8px;
                            padding: 8px;
                        }}
                        QPushButton:hover {{
                            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                stop:0 #d32f2f, stop:0.5 #f44336, stop:1 #d32f2f);
                            border: 2px solid #d32f2f;
                        }}
                    """)
                elif style == 'info':
                    btn.setStyleSheet(f"""
                        QPushButton {{
                            font: bold {max(11, int(margin_size * 0.55))}pt Arial;
                            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                stop:0 #17a2b8, stop:0.5 #138496, stop:1 #17a2b8);
                            color: white;
                            border: 2px solid #17a2b8;
                            border-radius: 8px;
                            padding: 8px;
                        }}
                        QPushButton:hover {{
                            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                stop:0 #138496, stop:0.5 #17a2b8, stop:1 #138496);
                            border: 2px solid #138496;
                        }}
                    """)
                
                btn.clicked.connect(btn_data['action'])
                btn_layout.addWidget(btn)

            layout.addWidget(btn_frame)
        
        return widget
    
    def show_dummy(self):
        import threading
        import time
        
        base_dir = os.path.dirname(__file__)
        csv_path = os.path.join(base_dir, "dummydata.csv")
        
        leads = ["I", "II", "III", "aVR", "aVL", "aVF",
                 "V1", "V2", "V3", "V4", "V5", "V6"]

        # --- Start dummy data writer in background ---
        
        # --- Create dialog with matplotlib canvas ---
        dialog = QDialog(self.dashboard if self.dashboard else self)
        dialog.setWindowTitle("Live Dummy ECG")
        layout = QVBoxLayout(dialog)
        
        # Create matplotlib figure
        fig, axes = plt.subplots(3, 4, figsize=(16, 10), sharex=True)
        axes = axes.flatten()
        
        # Create canvas and add to layout
        canvas = FigureCanvas(fig)
        layout.addWidget(canvas)
        
        # Load the existing CSV data once
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path, sep='\t')  # Tab-separated file ke liye
            print(f"Loaded {len(df)} rows of data")
            print(f"Columns: {list(df.columns)}")
        else:
            print(f"CSV file {csv_path} not found!")
            return
        
        # Get the number of samples
        num_samples = len(df)
        window_size = 120  
        current_index = 0
        
        # Set up plots with compact styling
        for idx, lead in enumerate(leads):
            axes[idx].set_ylabel(lead, fontsize=9, fontweight='bold') 
            axes[idx].grid(True, alpha=0.2) 
            axes[idx].set_ylim(df[lead].min() - 50, df[lead].max() + 50)  
            
            # Remove unnecessary elements for cleaner look
            axes[idx].spines['top'].set_visible(False)
            axes[idx].spines['right'].set_visible(False)
            axes[idx].set_xticks([])
            axes[idx].set_yticks([])  
        
        # Compact title
        fig.suptitle('12-Lead ECG Monitor', fontsize=14, fontweight='bold', y=0.95)
        
        def update_plot():
            nonlocal current_index
            
            # Calculate start and end indices for sliding window
            start_idx = max(0, current_index - window_size)
            end_idx = current_index + 1
            
            # Update each lead plot
            for idx, lead in enumerate(leads):
                axes[idx].cla()
                
                # Plot the data in sliding window
                x_data = range(start_idx, end_idx)
                y_data = df[lead].iloc[start_idx:end_idx]
                axes[idx].plot(x_data, y_data, linewidth=1.2, color='#1f77b4') 
                
                # Add current position indicator
                if current_index < len(df):
                    current_value = df[lead].iloc[current_index]
                    axes[idx].plot(current_index, current_value, 'ro', markersize=4, alpha=0.8) 
                    axes[idx].axvline(x=current_index, color='red', linestyle='--', alpha=0.6, linewidth=0.8)  
                
                # Compact styling
                axes[idx].set_ylabel(lead, fontsize=9, fontweight='bold')
                axes[idx].grid(True, alpha=0.2)
                axes[idx].set_ylim(df[lead].min() - 50, df[lead].max() + 50)
                
                # Remove all unnecessary elements
                axes[idx].set_xticks([])
                axes[idx].set_yticks([])
                axes[idx].spines['top'].set_visible(False)
                axes[idx].spines['right'].set_visible(False)
            
            # Compact title with sample info
            fig.suptitle(f'ECG Monitor - Sample: {current_index}/{num_samples-1}', 
                         fontsize=12, fontweight='bold', y=0.95)
            
            # Tighter layout - less wasted space
            fig.tight_layout(pad=0.5)
            canvas.draw()
            
            # Move to next sample (loop back to start)
            current_index = (current_index + 1) % num_samples

        # --- Timer for live update ---
        timer = QTimer(dialog)
        timer.timeout.connect(update_plot)
        timer.start(100)  # 10 FPS for smooth animation

        dialog.setMinimumSize(1600, 1000)
        dialog.showMaximized() 
        dialog.exec_()
