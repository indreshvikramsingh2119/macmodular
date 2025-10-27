from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QFrame, QGridLayout, QCalendarWidget, QTextEdit,
    QDialog, QLineEdit, QComboBox, QFormLayout, QMessageBox, QSizePolicy, QStackedWidget, QScrollArea, QSpacerItem
)
from PyQt5.QtGui import QFont, QPixmap, QMovie
from PyQt5.QtCore import Qt, QTimer, QSize
try:
    from PyQt5.QtMultimedia import QSound
except ImportError:
    print("⚠️ QSound not available - heartbeat sound will be disabled")
    QSound = None
import sys
import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.animation import FuncAnimation
import math
import os
import json
import matplotlib.image as mpimg
import time
from dashboard.chatbot_dialog import ChatbotDialog
from utils.settings_manager import SettingsManager
from utils.crash_logger import get_crash_logger, CrashLogDialog

# Try to import configuration, fallback to defaults if not available
try:
    import sys
    # Add the src directory to the path
    src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)
    
    try:
        from config.settings import get_config
        config = get_config()
        def get_background_config():
            return config.get('ui.background', {"background": "none", "gif": False})
        print("✓ Dashboard configuration loaded successfully")
    except ImportError as e:
        print(f"⚠️ Dashboard config import warning: {e}")
        def get_background_config():
            return {"background": "none", "gif": False}
except ImportError:
    print("⚠ Dashboard configuration not found, using default settings")
    def get_background_config():
        return {
            "use_gif_background": False,
            "preferred_background": "none"
        }

def get_asset_path(asset_name):
    """
    Get the absolute path to an asset file in a portable way.
    This function will work regardless of where the script is run from.
    
    Args:
        asset_name (str): Name of the asset file (e.g., 'her.png', 'v.gif')
    
    Returns:
        str: Absolute path to the asset file
    """
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Try multiple possible locations for the assets folder
    possible_paths = [
        # Standard project structure: src/dashboard/dashboard.py -> assets/
        os.path.join(os.path.dirname(os.path.dirname(script_dir)), "assets"),
        # Alternative: if running from project root
        os.path.join(script_dir, "assets"),
        # Alternative: if running from src/
        os.path.join(os.path.dirname(script_dir), "assets"),
        # Alternative: if running from dashboard/
        os.path.join(script_dir, "..", "assets"),
    ]
    
    # Find the first valid assets directory
    assets_dir = None
    for path in possible_paths:
        if os.path.exists(path) and os.path.isdir(path):
            assets_dir = path
            break
    
    if assets_dir is None:
        print(f"Warning: Could not find assets directory. Tried paths: {possible_paths}")
        # Return a default path as fallback
        return os.path.join(os.path.dirname(script_dir), "..", "assets", asset_name)
    
    # Return the full path to the asset
    asset_path = os.path.join(assets_dir, asset_name)
    
    return asset_path

class MplCanvas(FigureCanvas):
    def __init__(self, width=4, height=2, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super().__init__(fig)

class SignInDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Sign In")
        self.setFixedSize(340, 240)
        self.setStyleSheet("""
            QDialog { background: #fff; border-radius: 18px; }
            QLabel { font-size: 15px; color: #222; }
            QLineEdit, QComboBox { border: 2px solid #ff6600; border-radius: 8px; padding: 6px 10px; font-size: 15px; background: #f7f7f7; }
            QPushButton { background: #ff6600; color: white; border-radius: 10px; padding: 8px 0; font-size: 16px; font-weight: bold; }
            QPushButton:hover { background: #ff8800; }
        """)
        layout = QVBoxLayout(self)
        layout.setSpacing(18)
        layout.setContentsMargins(28, 24, 28, 24)
        title = QLabel("Sign In to PulseMonitor")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignLeft)
        form.setFormAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.role_combo = QComboBox()
        self.role_combo.addItems(["Doctor", "Patient"])
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Enter your name")
        self.pass_edit = QLineEdit()
        self.pass_edit.setPlaceholderText("Password")
        self.pass_edit.setEchoMode(QLineEdit.Password)
        form.addRow("Role:", self.role_combo)
        form.addRow("Name:", self.name_edit)
        form.addRow("Password:", self.pass_edit)
        layout.addLayout(form)
        self.signin_btn = QPushButton("Sign In")
        self.signin_btn.clicked.connect(self.accept)
        layout.addWidget(self.signin_btn)
    def get_user_info(self):
        return self.role_combo.currentText(), self.name_edit.text()
    
class DashboardHomeWidget(QWidget):
    def __init__(self):
        super().__init__()

class Dashboard(QWidget):
    def __init__(self, username=None, role=None, user_details=None):
        super().__init__()
        # Settings for wave speed/gain
        self.settings_manager = SettingsManager()
        
        # Initialize crash logger
        self.crash_logger = get_crash_logger()
        self.crash_logger.log_info("Dashboard initialized", "DASHBOARD_START")
        
        # Triple-click counter for heart rate metric
        self.heart_rate_click_count = 0
        self.last_heart_rate_click_time = 0
        
        # Set responsive size policy
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(800, 600)  # Minimum size for usability

        # Reports filter date
        self.reports_filter_date = None
        
        # Store username, role, and full user details
        self.username = username
        self.role = role
        self.user_details = user_details or {}
        
        # Initialize mode flags
        self.dark_mode = False
        self.medical_mode = False
        
        self.setWindowTitle("ECG Monitor Dashboard")
        self.setGeometry(100, 100, 1300, 900)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint | Qt.WindowCloseButtonHint)
        self.setWindowState(Qt.WindowMaximized)
        self.center_on_screen()
        
        # Test asset paths at startup for debugging
        self.test_asset_paths()
        
        # Load background settings from configuration file
        config = get_background_config()
        self.use_gif_background = config.get("use_gif_background", False)
        self.preferred_background = config.get("preferred_background", "none")
        
        print(f"Dashboard background: {self.preferred_background} (GIF: {self.use_gif_background})")
        
        # --- Plasma GIF background ---
        self.bg_label = QLabel(self)
        self.bg_label.setGeometry(0, 0, self.width(), self.height())
        self.bg_label.lower()
        
        # Try to load background GIFs using portable paths
        if not self.use_gif_background:
            # Use solid color background
            self.bg_label.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #f8f9fa, stop:1 #e9ecef);")
            print("Using solid color background (GIF background disabled)")
        else:
            # Priority order based on user preference
            movie = None
            if self.preferred_background == "plasma.gif":
                plasma_path = get_asset_path("plasma.gif")
                if os.path.exists(plasma_path):
                    movie = QMovie(plasma_path)
                    print("Using plasma.gif as background")
                else:
                    print("plasma.gif not found, trying alternatives...")
                    self.preferred_background = "tenor.gif"  # Fallback
            
            if self.preferred_background == "tenor.gif" and not movie:
                tenor_gif_path = get_asset_path("tenor.gif")
                if os.path.exists(tenor_gif_path):
                    movie = QMovie(tenor_gif_path)
                    print("Using tenor.gif as background")
                else:
                    print("tenor.gif not found, trying alternatives...")
                    self.preferred_background = "v.gif"  # Fallback
            
            if self.preferred_background == "v.gif" and not movie:
                v_gif_path = get_asset_path("v.gif")
                if os.path.exists(v_gif_path):
                    movie = QMovie(v_gif_path)
                    print("Using v.gif as background")
                else:
                    print("v.gif not found, using solid color background")
            
            if movie:
                self.bg_label.setMovie(movie)
                movie.start()
            else:
                # If no GIF found, create a solid color background
                self.bg_label.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #f8f9fa, stop:1 #e9ecef);")
                print("Using solid color background (no GIFs found)")
        # --- Central stacked widget for in-place navigation ---
        self.page_stack = QStackedWidget(self)
        
        # --- Dashboard main page widget ---
        self.dashboard_page = DashboardHomeWidget()
        dashboard_layout = QVBoxLayout(self.dashboard_page)
        dashboard_layout.setSpacing(20)
        dashboard_layout.setContentsMargins(20, 20, 20, 20)
        
        # --- Header ---
        header = QHBoxLayout()
        logo = QLabel("ECG Monitor")
        logo.setFont(QFont("Arial", 24, QFont.Bold))
        logo.setStyleSheet("color: #ff6600;")
        logo.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        header.addWidget(logo)
        
        self.status_dot = QLabel()
        self.status_dot.setFixedSize(18, 18)
        self.status_dot.setStyleSheet("border-radius: 9px; background: gray; border: 2px solid #fff;")
        header.addWidget(self.status_dot)
        
        self.update_internet_status()
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self.update_internet_status)
        self.status_timer.start(3000)
        
        self.medical_btn = QPushButton("Medical Mode")
        self.medical_btn.setCheckable(True)
        self.medical_btn.setStyleSheet("background: #00b894; color: white; border-radius: 10px; padding: 4px 18px;")
        self.medical_btn.clicked.connect(self.toggle_medical_mode)
        self.medical_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        # Hide button per request while preserving logic
        self.medical_btn.setVisible(False)
        
        self.dark_btn = QPushButton("Dark Mode")
        self.dark_btn.setCheckable(True)
        self.dark_btn.setStyleSheet("background: #222; color: #fff; border-radius: 10px; padding: 4px 18px;")
        self.dark_btn.clicked.connect(self.toggle_dark_mode)
        self.dark_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        # Hide button per request while preserving logic
        self.dark_btn.setVisible(False)
        
        # Removed background control button per request
        
        header.addStretch()
        
        # User label removed per request
        # self.user_label = QLabel(f"{username or 'User'}\n{role or ''}")
        # self.user_label.setFont(QFont("Arial", 12))
        # self.user_label.setAlignment(Qt.AlignRight)
        # self.user_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        # header.addWidget(self.user_label)
        
        self.sign_btn = QPushButton("Sign Out")
        self.sign_btn.setStyleSheet("background: #e74c3c; color: white; border-radius: 10px; padding: 4px 18px;")
        self.sign_btn.clicked.connect(self.handle_sign_out)
        self.sign_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        header.addWidget(self.sign_btn)
        
        dashboard_layout.addLayout(header)
        
        # --- Greeting and Date Row ---
        greet_row = QHBoxLayout()
        from datetime import datetime
        hour = datetime.now().hour
        if hour < 12:
            greeting = "Good Morning"
        elif hour < 18:
            greeting = "Good Afternoon"
        else:
            greeting = "Good Evening"
        
        # Show full name if available, otherwise username
        display_name = self.user_details.get('full_name', username) or username or 'User'
        user_info_lines = [f"<span style='font-size:18pt;font-weight:bold;'>{greeting}, {display_name}</span>"]
        
        # Add user details if available
        if self.user_details:
            details = []
            if self.user_details.get('age'):
                details.append(f"Age: {self.user_details.get('age')}")
            if self.user_details.get('gender'):
                details.append(f"Gender: {self.user_details.get('gender')}")
            if details:
                user_info_lines.append(f"<span style='color:#666; font-size:11pt;'>{' | '.join(details)}</span>")
        
        user_info_lines.append("<span style='color:#888;'>Welcome to your ECG dashboard</span>")
        
        greet = QLabel("<br>".join(user_info_lines))
        greet.setFont(QFont("Arial", 16))
        greet.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        greet_row.addWidget(greet)
        greet_row.addStretch()
        
        date_btn = QPushButton("ECG Lead Test 12")
        date_btn.setStyleSheet("background: #ff6600; color: white; border-radius: 16px; padding: 8px 24px;")
        date_btn.clicked.connect(self.go_to_lead_test)
        date_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        greet_row.addWidget(date_btn)

        # --- Add Chatbot Button ---
        chatbot_btn = QPushButton("AI Chatbot")
        chatbot_btn.setStyleSheet("background: #2453ff; color: white; border-radius: 16px; padding: 8px 24px;")
        chatbot_btn.clicked.connect(self.open_chatbot_dialog)
        chatbot_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        greet_row.addWidget(chatbot_btn)

        dashboard_layout.addLayout(greet_row)

        # --- Main Grid ---
        # Create a scroll area for responsive design
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        grid_widget = QWidget()
        grid = QGridLayout(grid_widget)
        grid.setSpacing(20)
        
        # --- Heart Rate Card ---
        heart_card = QFrame()
        heart_card.setStyleSheet("background: white; border-radius: 16px;")
        heart_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        heart_layout = QVBoxLayout(heart_card)
        
        heart_label = QLabel("Live Heart Rate Overview")
        heart_label.setFont(QFont("Arial", 16, QFont.Bold))
        heart_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        heart_layout.addWidget(heart_label)
        
        heart_img = QLabel()
        # Use portable path for the heart image asset
        heart_img_path = get_asset_path("her.png")
        print(f"Heart image path: {heart_img_path}")  # Debugging line to check the path
        # Ensure os module is available
        import os
        print(f"Heart image exists: {os.path.exists(heart_img_path)}")  # Check if the file exists
        
        # Load the heart image with error handling
        if os.path.exists(heart_img_path):
            self.heart_pixmap = QPixmap(heart_img_path)
            if self.heart_pixmap.isNull():
                print(f"Error: Failed to load heart image from {heart_img_path}")
                # Create a placeholder pixmap
                self.heart_pixmap = QPixmap(220, 220)
                self.heart_pixmap.fill(Qt.lightGray)
        else:
            print(f"Error: Heart image not found at {heart_img_path}")
            # Create a placeholder pixmap
            self.heart_pixmap = QPixmap(220, 220)
            self.heart_pixmap.fill(Qt.lightGray)
        self.heart_base_size = 220
        heart_img.setFixedSize(self.heart_base_size + 20, self.heart_base_size + 20)
        heart_img.setAlignment(Qt.AlignCenter)
        heart_img.setPixmap(self.heart_pixmap.scaled(self.heart_base_size, self.heart_base_size, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        heart_img.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        heart_layout.addWidget(heart_img)
        
        # Live stress and HRV labels
        self.stress_label = QLabel("Stress Level: --")
        self.stress_label.setStyleSheet("font-size: 13px; color: #666;")
        self.stress_label.setAlignment(Qt.AlignCenter)
        heart_layout.addWidget(self.stress_label)
        
        self.hrv_label = QLabel("Average Variability: --")
        self.hrv_label.setStyleSheet("font-size: 13px; color: #666;")
        self.hrv_label.setAlignment(Qt.AlignCenter)
        heart_layout.addWidget(self.hrv_label)
        
        grid.addWidget(heart_card, 0, 0, 2, 1)
        
        # --- Heartbeat Animation ---
        self.heart_img = heart_img
        self.heartbeat_phase = 0
        self.current_heart_rate = 60  # Default heart rate
        self.last_beat_time = 0
        self.beat_interval = 1000  # Default 1 second between beats (60 BPM)
        self.heartbeat_timer = QTimer(self)
        self.heartbeat_timer.timeout.connect(self.animate_heartbeat)
        self.heartbeat_timer.start(30)  # ~33 FPS
        
        # --- Heartbeat Sound ---
        try:
            if QSound is not None:
                # Try to load heartbeat sound file
                heartbeat_sound_path = get_asset_path("heartbeat.wav")
                if os.path.exists(heartbeat_sound_path):
                    self.heartbeat_sound = QSound(heartbeat_sound_path)
                    print(f"✅ Heartbeat sound loaded: {heartbeat_sound_path}")
                else:
                    print(f"⚠️ Heartbeat sound not found at: {heartbeat_sound_path}")
                    # Create a synthetic heartbeat sound
                    self.create_heartbeat_sound()
            else:
                print("⚠️ QSound not available - heartbeat sound disabled")
                self.heartbeat_sound = None
        except Exception as e:
            print(f"⚠️ Could not load heartbeat sound: {e}")
            self.heartbeat_sound = None
        
        # --- ECG Recording (Animated Chart) ---
        ecg_card = QFrame()
        ecg_card.setStyleSheet("background: white; border-radius: 16px;")
        ecg_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        ecg_layout = QVBoxLayout(ecg_card)
        
        ecg_label = QLabel("ECG Recording")
        ecg_label.setFont(QFont("Arial", 14, QFont.Bold))
        ecg_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        ecg_layout.addWidget(ecg_label)
        
        self.ecg_canvas = MplCanvas(width=4, height=2)
        self.ecg_canvas.axes.set_facecolor("#eee")
        self.ecg_canvas.axes.set_xticks([])
        self.ecg_canvas.axes.set_yticks([])
        self.ecg_canvas.axes.set_title("Lead II", fontsize=10)
        # Set fixed Y-axis limits to center the ECG wave properly with more range
        self.ecg_canvas.axes.set_ylim(-300, 300)
        self.ecg_canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        ecg_layout.addWidget(self.ecg_canvas)
        
        grid.addWidget(ecg_card, 1, 1)
        
        # --- Total Visitors (Pie Chart) ---
        visitors_card = QFrame()
        visitors_card.setStyleSheet("background: white; border-radius: 16px;")
        visitors_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        visitors_layout = QVBoxLayout(visitors_card)
        
        from datetime import datetime
        current_month = datetime.now().month
        current_year = datetime.now().year
        
        visitors_label = QLabel(f"Visitors - Last 6 Months ({current_year})")
        visitors_label.setFont(QFont("Arial", 14, QFont.Bold))
        visitors_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        visitors_layout.addWidget(visitors_label)
        
        pie_canvas = MplCanvas(width=2.5, height=2.5)
        
        # Generate last 6 months dynamically with real session counts
        import calendar
        month_names = []
        month_data = []
        
        # Get session counts per month
        try:
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
            sessions_dir = os.path.join(base_dir, 'reports', 'sessions')
            
            for i in range(5, -1, -1):  # Last 6 months
                # Calculate target month/year
                target_month = ((current_month - i - 1) % 12) + 1
                target_year = current_year if (current_month - i) > 0 else current_year - 1
                
                month_names.append(calendar.month_name[target_month][:3])
                
                # Count session files for this month
                count = 0
                if os.path.exists(sessions_dir):
                    for filename in os.listdir(sessions_dir):
                        if filename.endswith('.jsonl'):
                            try:
                                # Parse date from filename: session_user_YYYYMMDD_HHMMSS.jsonl
                                parts = filename.split('_')
                                if len(parts) >= 3:
                                    date_str = parts[-2]  # YYYYMMDD
                                    if len(date_str) == 8:
                                        file_year = int(date_str[:4])
                                        file_month = int(date_str[4:6])
                                        if file_year == target_year and file_month == target_month:
                                            count += 1
                            except Exception:
                                continue
                
                # Use actual count, or show 1 if zero to keep chart visible
                month_data.append(max(1, count))
        except Exception as e:
            print(f"⚠️ Could not calculate visitor stats: {e}")
            month_data = [1, 1, 1, 1, 1, 1]  # Fallback to equal distribution
        
        pie_data = month_data
        pie_labels = month_names
        # Modern colors matching software orange theme
        pie_colors = ["#ff6600", "#ff8533", "#ffaa66", "#ffcc99", "#ffe6cc", "#fff3e6"]
        
        # Draw pie without labels to avoid overlap, use legend instead
        wedges, texts, autotexts = pie_canvas.axes.pie(
            pie_data, labels=None, autopct='%1.0f%%', colors=pie_colors, 
            startangle=90, pctdistance=0.7
        )
        
        # Percentage text - adaptive color for readability
        for i, autotext in enumerate(autotexts):
            if i < 3:
                autotext.set_color('white')
            else:
                autotext.set_color('#222')
            autotext.set_fontsize(10)
            autotext.set_weight('bold')
        
        # Add legend on the side instead of labels on pie
        pie_canvas.axes.legend(
            wedges, pie_labels,
            loc="center left",
            bbox_to_anchor=(1, 0, 0.5, 1),
            fontsize=9,
            frameon=False
        )
        
        pie_canvas.axes.set_aspect('equal')
        pie_canvas.figure.tight_layout(pad=0.3)
        pie_canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        visitors_layout.addWidget(pie_canvas)
        
        grid.addWidget(visitors_card, 1, 2)
        
        # --- Schedule Card ---
        schedule_card = QFrame()
        schedule_card.setStyleSheet("background: white; border-radius: 16px;")
        schedule_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        schedule_layout = QVBoxLayout(schedule_card)
        
        schedule_label = QLabel("Calendar")
        schedule_label.setFont(QFont("Arial", 14, QFont.Bold))
        schedule_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        schedule_layout.addWidget(schedule_label)
        self.schedule_calendar = QCalendarWidget()
        self.schedule_calendar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.schedule_calendar.setMinimumHeight(180)
        self.schedule_calendar.setMaximumHeight(250)

        self.schedule_calendar.setStyleSheet("""
        QCalendarWidget QWidget { 
            background: #ffffff; 
            color: #222; 
        }
        QCalendarWidget QAbstractItemView {
            background: #ffffff; 
            color: #222;
            selection-background-color: #ff6600; 
            selection-color: #fff;
        }
        QCalendarWidget QToolButton { 
            color: #222; 
            background: transparent;
            padding: 4px;
            margin: 2px;
        }
        QCalendarWidget QToolButton:hover {
            background: #ffe6cc;
            border-radius: 4px;
        }
        QCalendarWidget QSpinBox { 
            color: #222;
            background: #f7f7f7;
            border: 1px solid #ddd;
            padding: 2px;
        }
        QCalendarWidget QWidget#qt_calendar_navigationbar {
            background: #f7f7f7;
        }
        QCalendarWidget QWidget#qt_calendar_navigationbar QHBoxLayout {
            alignment: center;
        }
        QCalendarWidget QWidget#qt_calendar_navigationbar QToolButton {
            min-width: 30px;
            min-height: 30px;
        }
        /* Hide the navigation arrows */
        QCalendarWidget QWidget#qt_calendar_navigationbar QToolButton[text="◀"],
        QCalendarWidget QWidget#qt_calendar_navigationbar QToolButton[text="▶"] {
            display: none;
        }
    """)

        # Highlight last ECG usage date in red
        from PyQt5.QtGui import QTextCharFormat, QColor
        last_ecg_file = 'last_ecg_date.json'
        import datetime
        today = datetime.date.today()
        # Try to load last ECG date from file
        last_ecg_date = None
        if os.path.exists(last_ecg_file):
            with open(last_ecg_file, 'r') as f:
                try:
                    data = json.load(f)
                    last_ecg_date = data.get('last_ecg_date')
                except Exception:
                    last_ecg_date = None
        if last_ecg_date:
            try:
                y, m, d = map(int, last_ecg_date.split('-'))
                last_date = Qt.QDate(y, m, d)
                fmt = QTextCharFormat()
                fmt.setBackground(QColor('red'))
                fmt.setForeground(QColor('white'))
                self.schedule_calendar.setDateTextFormat(last_date, fmt)
            except Exception:
                pass

        # connect date click/selection to filter reports
        self.schedule_calendar.clicked.connect(self.on_calendar_date_selected)
        self.schedule_calendar.selectionChanged.connect(self.on_calendar_selection_changed)
        
        # Disabled: No longer connect month/year navigation to custom dropdowns
        # self.schedule_calendar.currentPageChanged.connect(self.on_calendar_page_changed)
        
        schedule_layout.addWidget(self.schedule_calendar)
        grid.addWidget(schedule_card, 2, 0)
        # --- Conclusion Card ---
        issue_card = QFrame()
        issue_card.setStyleSheet("background: white; border-radius: 16px;")
        issue_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        issue_layout = QVBoxLayout(issue_card)
        
        issue_label = QLabel("Conclusion")
        issue_label.setFont(QFont("Arial", 14, QFont.Bold))
        issue_label.setStyleSheet("color: #ff6600;")
        issue_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        issue_layout.addWidget(issue_label)
        
        # Live conclusion box that updates based on ECG analysis
        self.conclusion_box = QTextEdit()
        self.conclusion_box.setReadOnly(True)
        self.conclusion_box.setStyleSheet("background: #f7f7f7; border: none; font-size: 12px; padding: 10px;")
        self.conclusion_box.setMinimumHeight(180)
        self.conclusion_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Set initial placeholder text
        self.conclusion_box.setHtml("""
            <p style='color: #888; font-style: italic;'>
            No ECG data available yet.<br><br>
            Start an ECG test or enable demo mode to see your personalized analysis and recommendations.
            </p>
        """)
        
        issue_layout.addWidget(self.conclusion_box)
        
        grid.addWidget(issue_card, 2, 1, 1, 1)

        # --- Recent Reports Card ---
        reports_card = QFrame()
        reports_card.setStyleSheet(
            "background: white; border-radius: 16px;"
        )
        reports_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        reports_v = QVBoxLayout(reports_card)
        ttl = QLabel("Recent Reports")
        ttl.setFont(QFont("Arial", 14, QFont.Bold))
        ttl.setStyleSheet("color: #ff6600;")
        reports_v.addWidget(ttl)

        # Scroll area for list
        self.reports_list_widget = QWidget()
        self.reports_list_layout = QVBoxLayout(self.reports_list_widget)
        self.reports_list_layout.setContentsMargins(0,0,0,0)
        self.reports_list_layout.setSpacing(8)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumHeight(180)
        scroll.setWidget(self.reports_list_widget)
        reports_v.addWidget(scroll)

        self.refresh_recent_reports_ui()

        grid.addWidget(reports_card, 2, 2, 1, 1)
        
        # --- ECG Monitor Metrics Cards ---
        metrics_card = QFrame()
        metrics_card.setStyleSheet("background: white; border-radius: 16px;")
        metrics_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        metrics_layout = QHBoxLayout(metrics_card)
        
        # Store metric labels for live update
        self.metric_labels = {}
        metric_info = [
            ("HR", "00", "BPM", "heart_rate"),
            ("PR", "0", "ms", "pr_interval"),
            ("QRS Complex", "0", "ms", "qrs_duration"),
            ("QRS Axis", "0°", "", "qrs_axis"),
            ("ST", "0", "ms", "st_interval"),
            ("QT/Qtc", "0", "ms", "qtc_interval"),
            ("Time", "00:00", "", "time_elapsed"),  # Restore time for synchronization
        ]
        
        for title, value, unit, key in metric_info:
            box = QVBoxLayout()
            lbl = QLabel(title)
            lbl.setFont(QFont("Arial", 12, QFont.Bold))
            lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            val = QLabel(f"{value} {unit}")
            val.setFont(QFont("Arial", 18, QFont.Bold))
            val.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            
            # Add triple-click functionality to heart rate metric
            if key == "heart_rate":
                val.mousePressEvent = self.heart_rate_triple_click
            
            box.addWidget(lbl)
            box.addWidget(val)
            metrics_layout.addLayout(box)
            self.metric_labels[key] = val  # Store reference for live update
        
        grid.addWidget(metrics_card, 0, 1, 1, 2)
        
        # Add the grid widget to the scroll area
        scroll_area.setWidget(grid_widget)
        
        # Add scroll area to dashboard layout
        dashboard_layout.addWidget(scroll_area)
        
        # Generate Report button is on ECG 12 Lead Test page only (logic preserved in generate_pdf_report method)
        
        # --- ECG Animation Setup ---
        self.ecg_x = np.linspace(0, 2, 500)
        self.ecg_y = 150 * np.sin(2 * np.pi * 2 * self.ecg_x) + 30 * np.random.randn(500)  # Smaller amplitude to prevent cropping
        self.ecg_line, = self.ecg_canvas.axes.plot(self.ecg_x, self.ecg_y, color="#ff6600", linewidth=0.5, antialiased=False)
        # Reduce CPU/GPU usage: lower refresh rate slightly and disable frame caching
        self.anim = FuncAnimation(
            self.ecg_canvas.figure,
            self.update_ecg,
            interval=85,              # ~12 FPS for smoothness without lag
            blit=True,
            cache_frame_data=False,   # prevent unbounded cache growth
            save_count=100
        )
        
        # --- Dashboard Metrics Update Timer ---
        self.metrics_timer = QTimer(self)
        self.metrics_timer.timeout.connect(self.update_dashboard_metrics_from_ecg)
        self.metrics_timer.start(1000)  # Update every second
        
        # --- Live Session Timer ---
        self.session_start_time = None  # Will be set when demo/acquisition starts
        self.session_total_paused_time = 0  # Track total paused duration
        self.session_paused_at = None  # When current pause started
        self.session_last_elapsed = 0  # Frozen elapsed time during pause
        self.session_timer = QTimer(self)
        self.session_timer.timeout.connect(self.update_session_time)
        self.session_timer.start(1000)  # Update every second
        # Add dashboard_page to stack
        self.page_stack.addWidget(self.dashboard_page)
        # --- ECG Test Page ---
        try:
            # Add the src directory to the path for ECG imports
            src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if src_dir not in sys.path:
                sys.path.insert(0, src_dir)
                print(f"✅ Added src directory to path: {src_dir}")
            
            from ecg.twelve_lead_test import ECGTestPage
            print("✅ ECG Test Page imported successfully")
                    
        except ImportError as e:
            print(f"❌ ECG Test Page import error: {e}")
            print("💡 Creating fallback ECG Test Page")
            # Create a fallback ECG test page
            class ECGTestPage(QWidget):
                def __init__(self, title, parent):
                    super().__init__()
                    self.title = title
                    self.parent = parent
                    self.dashboard_callback = None
                    layout = QVBoxLayout()
                    label = QLabel("ECG Test Page - Import Error")
                    label.setAlignment(Qt.AlignCenter)
                    layout.addWidget(label)
                    self.setLayout(layout)
                    print("⚠️ Using fallback ECG Test Page")
        self.ecg_test_page = ECGTestPage("12 Lead ECG Test", self.page_stack)
        self.ecg_test_page.dashboard_callback = self.update_ecg_metrics

        if hasattr(self.ecg_test_page, 'update_metrics_frame_theme'):
            self.ecg_test_page.update_metrics_frame_theme(self.dark_mode, self.medical_mode)
        
        self.page_stack.addWidget(self.ecg_test_page)
        # --- Main layout ---
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.page_stack)
        self.setLayout(main_layout)
        self.page_stack.setCurrentWidget(self.dashboard_page)

        # Add a content_frame for ECGMenu to use
        self.content_frame = QFrame(self)
        self.content_frame.setStyleSheet("background: transparent; border: none;")
        main_layout.addWidget(self.content_frame)

        self.setLayout(main_layout)
        self.page_stack.setCurrentWidget(self.dashboard_page)

    # Calendar date selection

    def on_calendar_date_selected(self, qdate):
        try:
            self.reports_filter_date = qdate.toString("yyyy-MM-dd")
            self.refresh_recent_reports_ui(self.reports_filter_date)
        except Exception:
            self.refresh_recent_reports_ui()  # safe fallback

    def on_calendar_selection_changed(self):
        try:
            qdate = self.schedule_calendar.selectedDate()
            self.reports_filter_date = qdate.toString("yyyy-MM-dd")
            self.refresh_recent_reports_ui(self.reports_filter_date)
        except Exception:
            pass

    def on_calendar_page_changed(self, year, month):
        """Handle calendar page change - disabled dropdown functionality"""
        try:
            # Disabled: No longer show month dropdown when calendar arrows are clicked
            # self.show_month_dropdown(year, month)
            pass
        except Exception as e:
            print(f"Error in calendar page change: {e}")

    def show_month_dropdown(self, year, month):
        """Show month selection dropdown"""
        from PyQt5.QtWidgets import QComboBox, QDialog, QVBoxLayout, QPushButton, QLabel
        from PyQt5.QtCore import Qt
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Select Month")
        dialog.setModal(True)
        dialog.setFixedSize(200, 300)
        
        layout = QVBoxLayout(dialog)
        
        # Year selection
        year_label = QLabel("Year:")
        year_label.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(year_label)
        
        year_combo = QComboBox()
        current_year = year
        for y in range(current_year - 5, current_year + 6):
            year_combo.addItem(str(y))
        year_combo.setCurrentText(str(year))
        layout.addWidget(year_combo)
        
        # Month selection
        month_label = QLabel("Month:")
        month_label.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(month_label)
        
        month_combo = QComboBox()
        months = ["January", "February", "March", "April", "May", "June",
                 "July", "August", "September", "October", "November", "December"]
        for i, month_name in enumerate(months):
            month_combo.addItem(month_name)
        month_combo.setCurrentIndex(month - 1)
        layout.addWidget(month_combo)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        ok_button = QPushButton("OK")
        ok_button.setStyleSheet("background: #ff6600; color: white; border-radius: 5px; padding: 8px;")
        ok_button.clicked.connect(lambda: self.apply_calendar_selection(
            int(year_combo.currentText()), month_combo.currentIndex() + 1, dialog))
        
        cancel_button = QPushButton("Cancel")
        cancel_button.setStyleSheet("background: #666; color: white; border-radius: 5px; padding: 8px;")
        cancel_button.clicked.connect(dialog.reject)
        
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        
        dialog.exec_()

    def apply_calendar_selection(self, year, month, dialog):
        """Apply the selected year and month to the calendar"""
        try:
            from PyQt5.QtCore import QDate
            # Set the calendar to the selected month/year
            self.schedule_calendar.setCurrentPage(year, month)
            dialog.accept()
        except Exception as e:
            print(f"Error applying calendar selection: {e}")
            dialog.reject()

    def open_chatbot_dialog(self):
        dlg = ChatbotDialog(self)
        dlg.exec_()

    def refresh_recent_reports_ui(self, filter_date=None):
        import os, json
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        reports_dir = os.path.join(base_dir, "..", "reports")
        index_path = os.path.join(reports_dir, "index.json")

        # Clear list
        while self.reports_list_layout.count():
            item = self.reports_list_layout.takeAt(0)
            w = item.widget()
            if w: w.setParent(None)

        entries = []
        if os.path.exists(index_path):
            try:
                with open(index_path, 'r') as f:
                    entries = json.load(f) or []
            except Exception:
                entries = []

        # Use the calendar’s current filter if none explicitly provided
        if filter_date is None:
            filter_date = getattr(self, "reports_filter_date", None)

        if filter_date:
            fd = str(filter_date).strip()
            entries = [e for e in entries if str(e.get('date','')).strip() == fd]

        for e in entries[:10]:
            row = QHBoxLayout()
            meta = QLabel(f"{e.get('date','')} {e.get('time','')}  |  {e.get('patient','')}  |  {e.get('title','Report')}")
            meta.setStyleSheet("color: #333333; font-size: 12px;")
            row.addWidget(meta, 1)
            btn = QPushButton("Open")
            btn.setStyleSheet("background: #ff6600; color: white; border-radius: 8px; padding: 4px 10px; font-weight: bold;")
            path = os.path.join(reports_dir, e.get('filename',''))
            btn.clicked.connect(lambda _, p=path: self.open_report_file(p))
            row.addWidget(btn)
            cont = QWidget(); cont.setLayout(row)
            self.reports_list_layout.addWidget(cont)

        spacer = QWidget(); spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.reports_list_layout.addWidget(spacer)

    def open_report_file(self, path):
        import os, sys, subprocess
        if not os.path.exists(path):
            return
        if sys.platform == 'darwin':
            subprocess.call(['open', path])
        elif sys.platform.startswith('linux'):
            subprocess.call(['xdg-open', path])
        elif sys.platform.startswith('win'):
            os.startfile(path)

    def is_ecg_active(self):
        """Return True if demo is ON or serial acquisition is running."""
        try:
            if hasattr(self, 'ecg_test_page') and self.ecg_test_page:
                # Demo mode active?
                if hasattr(self.ecg_test_page, 'demo_toggle') and self.ecg_test_page.demo_toggle.isChecked():
                    return True
                # Serial acquisition running?
                reader = getattr(self.ecg_test_page, 'serial_reader', None)
                if reader and getattr(reader, 'running', False):
                    return True
        except Exception:
            pass
        return False

    def calculate_live_ecg_metrics(self, ecg_signal, sampling_rate=500):
        """Calculate live ECG metrics from Lead 2 data - Use EXACT same method as ECG test page"""
        try:
            from scipy.signal import butter, filtfilt, find_peaks
            
            # Ensure we have enough data
            if len(ecg_signal) < 200:
                return {}
            
            # Apply bandpass filter to enhance R-peaks (0.5-40 Hz) - SAME AS ECG TEST PAGE
            fs = sampling_rate  # Use same sampling rate as ECG test page
            nyquist = fs / 2
            low = 0.5 / nyquist
            high = 40 / nyquist
            b, a = butter(4, [low, high], btype='band')
            filtered_signal = filtfilt(b, a, ecg_signal)
            
            # Find R-peaks using scipy - SAME AS ECG TEST PAGE
            peaks, properties = find_peaks(
                filtered_signal,
                height=np.mean(filtered_signal) + 0.5 * np.std(filtered_signal),
                distance=int(0.4 * fs),  # Minimum 0.4 seconds between peaks (150 BPM max)
                prominence=np.std(filtered_signal) * 0.3
            )
            
            metrics = {}
            
            # Calculate Heart Rate - EXACT SAME METHOD AS ECG TEST PAGE
            if len(peaks) >= 2:
                # Calculate R-R intervals in milliseconds
                rr_intervals_ms = np.diff(peaks) * (1000 / fs)
                
                # Filter physiologically reasonable intervals (300-2000 ms)
                valid_intervals = rr_intervals_ms[(rr_intervals_ms >= 300) & (rr_intervals_ms <= 2000)]
                
                if len(valid_intervals) > 0:
                    # Calculate heart rate from median R-R interval - SAME AS ECG TEST PAGE
                    median_rr = np.median(valid_intervals)
                    heart_rate = 60000 / median_rr  # Convert to BPM
                    
                    # Ensure reasonable range (40-200 BPM) - SAME AS ECG TEST PAGE
                    heart_rate = max(40, min(200, heart_rate))
                    metrics['heart_rate'] = int(round(heart_rate))
            
            # Calculate QRS Axis - LIVE like ECG test page
            if hasattr(self, 'ecg_test_page') and self.ecg_test_page and hasattr(self.ecg_test_page, 'data') and len(self.ecg_test_page.data) >= 6:
                try:
                    # Get current values from leads I and aVF (same as ECG test page)
                    lead_i = self.ecg_test_page.data[0][-1] if len(self.ecg_test_page.data[0]) > 0 else 0
                    lead_avf = self.ecg_test_page.data[5][-1] if len(self.ecg_test_page.data[5]) > 0 else 0
                    
                    # Calculate QRS axis (same as ECG test page)
                    axis = int(np.arctan2(lead_avf, lead_i) * 180 / np.pi)
                    metrics['qrs_axis'] = f"{axis}°"
                except:
                    metrics['qrs_axis'] = "0°"
            else:
                metrics['qrs_axis'] = "0°"
            
            # Calculate PR Interval - LIVE
            if len(peaks) > 1:
                pr_intervals = []
                for i in range(min(3, len(peaks)-1)):
                    r_peak = peaks[i]
                    # Find P wave before R peak
                    p_start = max(0, r_peak - int(0.2 * fs))  # 200ms before R
                    p_segment = filtered_signal[p_start:r_peak]
                    if len(p_segment) > 0:
                        p_peak = p_start + np.argmax(p_segment)
                        pr_interval = (r_peak - p_peak) / fs * 1000  # Convert to ms
                        if 120 <= pr_interval <= 200:  # Reasonable PR interval
                            pr_intervals.append(pr_interval)
                
                if pr_intervals:
                    metrics['pr_interval'] = int(round(np.mean(pr_intervals)))
                else:
                    metrics['pr_interval'] = 160  # Fallback
            else:
                metrics['pr_interval'] = 160  # Fallback
            
            # Calculate QRS Duration - LIVE
            if len(peaks) > 0:
                qrs_durations = []
                for r_peak in peaks[:min(5, len(peaks))]:  # Analyze first 5 beats
                    # Find Q and S points around R peak
                    search_window = int(0.08 * fs)  # 80ms window
                    start_idx = max(0, r_peak - search_window)
                    end_idx = min(len(filtered_signal), r_peak + search_window)
                    
                    segment = filtered_signal[start_idx:end_idx]
                    if len(segment) > 0:
                        # Find Q point (minimum before R)
                        q_idx = start_idx + np.argmin(segment[:r_peak-start_idx]) if r_peak > start_idx else start_idx
                        # Find S point (minimum after R)
                        s_idx = r_peak + np.argmin(segment[r_peak-start_idx:]) if r_peak < end_idx else end_idx
                        
                        qrs_duration = (s_idx - q_idx) / fs * 1000  # Convert to ms
                        if 40 <= qrs_duration <= 200:  # Reasonable QRS duration
                            qrs_durations.append(qrs_duration)
                
                if qrs_durations:
                    metrics['qrs_duration'] = int(round(np.mean(qrs_durations)))
                else:
                    metrics['qrs_duration'] = 100  # Fallback
            else:
                metrics['qrs_duration'] = 100  # Fallback
            
            # Calculate ST Interval - LIVE
            if len(peaks) > 0:
                st_intervals = []
                for r_peak in peaks[:min(5, len(peaks))]:
                    # Find S point
                    s_start = r_peak
                    s_end = min(len(filtered_signal), r_peak + int(0.04 * fs))  # 40ms after R
                    if s_end > s_start:
                        s_point = s_start + np.argmin(filtered_signal[s_start:s_end])
                    else:
                        s_point = r_peak
                    
                    # Find T wave end (next R peak or end of signal)
                    next_r = r_peak + int(0.4 * fs)  # Expected next R in 400ms
                    if next_r < len(filtered_signal):
                        # Find T wave end by looking for return to baseline
                        t_segment = filtered_signal[r_peak:next_r]
                        if len(t_segment) > 0:
                            # Find where signal returns to baseline (mean of segment)
                            baseline = np.mean(t_segment)
                            t_end_candidates = np.where(np.abs(t_segment - baseline) < 0.1 * np.std(t_segment))[0]
                            if len(t_end_candidates) > 0:
                                t_end = r_peak + t_end_candidates[-1]
                                st_interval = (t_end - s_point) / fs * 1000  # Convert to ms
                                if 50 <= st_interval <= 300:  # Reasonable ST interval
                                    st_intervals.append(st_interval)
                
                if st_intervals:
                    metrics['st_interval'] = int(round(np.mean(st_intervals)))
                else:
                    metrics['st_interval'] = 100  # Fallback
            else:
                metrics['st_interval'] = 100  # Fallback
            
            # Calculate QTc (Corrected QT interval) - Set same as ST interval
            if 'st_interval' in metrics:
                metrics['qtc_interval'] = metrics['st_interval']  # Same value as ST
            else:
                metrics['qtc_interval'] = 0  # Fallback
            
            # metrics['sampling_rate'] = f"{sampling_rate} Hz"  # Commented out
            
            # Calculate Time Elapsed (synchronized with ECG test page)
            if len(ecg_signal) > 0:
                time_elapsed_sec = len(ecg_signal) / sampling_rate
                minutes = int(time_elapsed_sec // 60)
                seconds = int(time_elapsed_sec % 60)
                metrics['time_elapsed'] = f"{minutes:02d}:{seconds:02d}"
            
            return metrics
            
        except Exception:
            # Quietly fall back if metrics cannot be calculated
            return {}

    def update_dashboard_metrics_live(self, ecg_metrics):
        """Update dashboard metrics with live calculated values"""
        try:
            # Do not update metrics for first-time users until acquisition/demo starts
            if not self.is_ecg_active():
                return
            
            # Skip live calculations if demo mode is active (use fixed values instead)
            if hasattr(self, 'ecg_test_page') and hasattr(self.ecg_test_page, 'demo_toggle'):
                if self.ecg_test_page.demo_toggle.isChecked():
                    return  # Demo mode uses fixed metrics, don't overwrite with live calculations
            # Update Heart Rate
            if 'heart_rate' in ecg_metrics:
                self.metric_labels['heart_rate'].setText(f"{ecg_metrics['heart_rate']} BPM")
            
            # Update PR Interval
            if 'pr_interval' in ecg_metrics:
                self.metric_labels['pr_interval'].setText(f"{ecg_metrics['pr_interval']} ms")
            
            # Update QRS Duration
            if 'qrs_duration' in ecg_metrics:
                self.metric_labels['qrs_duration'].setText(f"{ecg_metrics['qrs_duration']} ms")
            
            # Update QRS Axis
            if 'qrs_axis' in ecg_metrics:
                self.metric_labels['qrs_axis'].setText(ecg_metrics['qrs_axis'])
            
            # Update ST Interval
            if 'st_interval' in ecg_metrics:
                self.metric_labels['st_interval'].setText(f"{ecg_metrics['st_interval']} ms")
            
            # Update QTc Interval (handles both single value and QT/QTc format)
            if 'qtc_interval' in ecg_metrics:
                qtc_text = ecg_metrics['qtc_interval']
                # If already formatted as QT/QTc, don't add " ms" suffix
                if '/' in str(qtc_text):
                    self.metric_labels['qtc_interval'].setText(str(qtc_text))
                else:
                    self.metric_labels['qtc_interval'].setText(f"{qtc_text} ms")
            
            # Update Sampling Rate - Commented out
            # if 'sampling_rate' in ecg_metrics:
            #     self.metric_labels['sampling_rate'].setText(ecg_metrics['sampling_rate'])
            
        except Exception as e:
            print(f"Error updating live dashboard metrics: {e}")




    def update_ecg(self, frame):
        try:
            # Try to get data from ECG test page if available
            if hasattr(self, 'ecg_test_page') and self.ecg_test_page:
                try:
                    # Validate ECG test page data structure
                    if not hasattr(self.ecg_test_page, 'data') or not self.ecg_test_page.data:
                        print("❌ ECG test page has no data")
                        return self._fallback_wave_update(frame)
                    
                    if len(self.ecg_test_page.data) <= 1:
                        print("❌ Insufficient ECG data (need Lead II)")
                        return self._fallback_wave_update(frame)
                    
                    # Get Lead II data from ECG test page (index 1 is Lead II)
                    lead_ii_data = self.ecg_test_page.data[1]
                    
                    # Validate Lead II data
                    if not isinstance(lead_ii_data, (list, np.ndarray)) or len(lead_ii_data) <= 10:
                        print("❌ Invalid Lead II data")
                        return self._fallback_wave_update(frame)
                    
                    # Convert to numpy array safely
                    try:
                        original_data = np.asarray(lead_ii_data, dtype=float)
                    except Exception as e:
                        print(f"❌ Error converting Lead II data to array: {e}")
                        return self._fallback_wave_update(frame)
                    
                    # Check for invalid values
                    if np.any(np.isnan(original_data)) or np.any(np.isinf(original_data)):
                        print("❌ Invalid values (NaN/Inf) in Lead II data")
                        return self._fallback_wave_update(frame)
                    
                    # Get actual sampling rate from ECG test page
                    actual_sampling_rate = 80  # Default to 80Hz
                    try:
                        if (hasattr(self.ecg_test_page, 'sampler') and 
                            hasattr(self.ecg_test_page.sampler, 'sampling_rate') and 
                            self.ecg_test_page.sampler.sampling_rate):
                            actual_sampling_rate = float(self.ecg_test_page.sampler.sampling_rate)
                            if actual_sampling_rate <= 0 or actual_sampling_rate > 1000:
                                actual_sampling_rate = 80
                    except Exception as e:
                        print(f"❌ Error getting sampling rate: {e}")
                        actual_sampling_rate = 80

                    # Determine visible window based on wave speed (display feature only)
                    try:
                        wave_speed = float(self.settings_manager.get_wave_speed())  # 12.5 / 25 / 50
                        if wave_speed <= 0:
                            wave_speed = 25.0
                    except Exception as e:
                        print(f"❌ Error getting wave speed: {e}")
                        wave_speed = 25.0
                    
                    # Baseline seconds at 25 mm/s
                    baseline_seconds = 10.0
                    # Scale time window: 12.5 => 20s, 25 => 10s, 50 => 5s
                    seconds_to_show = baseline_seconds * (25.0 / max(1e-6, wave_speed))
                    window_samples = int(max(50, min(len(original_data), seconds_to_show * actual_sampling_rate)))

                    # Slice last window and resample horizontally to fixed display length
                    try:
                        src = original_data[-window_samples:]
                        
                        # Detrend/center for display only
                        src_mean = np.mean(src)
                        if np.isnan(src_mean) or np.isinf(src_mean):
                            src_mean = 0
                        src_centered = src - src_mean
                        # Scale the signal to fit within the Y-axis range (-300 to 300)
                        if np.std(src_centered) > 0:
                            src_centered = src_centered * (200 / np.std(src_centered))  # Scale to fit in range
                        
                        display_len = len(self.ecg_x)
                        if src_centered.size <= 1:
                            display_y = np.full(display_len, 0.0)  # Center at 0
                        else:
                            x_src = np.linspace(0.0, 1.0, src_centered.size)
                            x_dst = np.linspace(0.0, 1.0, display_len)
                            display_y = np.interp(x_dst, x_src, src_centered)
                        
                        # Validate display data
                        if np.any(np.isnan(display_y)) or np.any(np.isinf(display_y)):
                            print("❌ Invalid display data generated")
                            return self._fallback_wave_update(frame)
                        
                        self.ecg_line.set_ydata(display_y)
                        
                    except Exception as e:
                        print(f"❌ Error processing display data: {e}")
                        return self._fallback_wave_update(frame)
                    
                    # Calculate and update live ECG metrics using ORIGINAL data with SAME sampling rate
                    try:
                        # Use ECG test page's own calculation methods for consistency
                        if hasattr(self.ecg_test_page, 'calculate_ecg_metrics'):
                            self.ecg_test_page.calculate_ecg_metrics()
                        
                        # Get metrics from ECG test page to ensure synchronization
                        if hasattr(self.ecg_test_page, 'get_current_metrics'):
                            ecg_metrics = self.ecg_test_page.get_current_metrics()
                            # Debug: Print metrics to see what's being calculated
                            if hasattr(self, '_debug_counter'):
                                self._debug_counter += 1
                            else:
                                self._debug_counter = 1
                            if self._debug_counter % 10 == 0:  # Print every 10 updates for more frequent debugging
                                print(f"🔍 Dashboard ECG metrics: {ecg_metrics}")
                            self.update_dashboard_metrics_from_ecg()
                        
                        # Calculate and update stress level and HRV (throttled to every 3 seconds for stability)
                        if not hasattr(self, '_last_stress_update'):
                            self._last_stress_update = 0
                        if time.time() - self._last_stress_update > 3:
                            self.update_stress_and_hrv(original_data, actual_sampling_rate)
                            self._last_stress_update = time.time()
                        
                        # Update live conclusion every 5 seconds
                        if not hasattr(self, '_last_conclusion_update'):
                            self._last_conclusion_update = 0
                        if time.time() - self._last_conclusion_update > 5:
                            self.update_live_conclusion()
                            self._last_conclusion_update = time.time()
                    except Exception as e:
                        print(f"❌ Error calculating ECG metrics: {e}")
                        # Continue with display even if metrics fail
                    
                    return [self.ecg_line]
                    
                except Exception as e:
                    print(f"❌ Error getting data from ECG test page: {e}")
                    return self._fallback_wave_update(frame)
            
            # No ECG test page available
            return self._fallback_wave_update(frame)
            
        except Exception as e:
            print(f"❌ Critical error in update_ecg: {e}")
            return self._fallback_wave_update(frame)
    
    def _fallback_wave_update(self, frame):
        """Fallback wave generation when ECG data is not available"""
        try:
            self.ecg_y = np.roll(self.ecg_y, -1)
            self.ecg_y[-1] = 150 * np.sin(2 * np.pi * 2 * self.ecg_x[-1] + frame/10) + 30 * np.random.randn()  # Smaller amplitude
            self.ecg_line.set_ydata(self.ecg_y)
            # Do not compute/update metrics from mock wave; keep zeros until user starts
            return [self.ecg_line]
        except Exception as e:
            print(f"❌ Error in fallback wave update: {e}")
            return [self.ecg_line]
    
    def heart_rate_triple_click(self, event):
        """Handle triple-click on heart rate metric to open crash log dialog"""
        # Only count left mouse button clicks
        try:
            if hasattr(event, 'button') and event.button() != Qt.LeftButton:
                return
        except Exception:
            pass
        current_time = time.time()
        
        # Check if this is within 1 second of the last click
        if current_time - self.last_heart_rate_click_time < 1.0:
            self.heart_rate_click_count += 1
        else:
            self.heart_rate_click_count = 1
        
        self.last_heart_rate_click_time = current_time
        
        # Show click count in terminal
        print(f"🖱️ Heart Rate Metric Click #{self.heart_rate_click_count}")
        
        # If triple-clicked, open crash log dialog
        if self.heart_rate_click_count >= 3:
            self.heart_rate_click_count = 0  # Reset counter
            print("🔧 Triple-click detected! Opening diagnostic dialog...")
            self.crash_logger.log_info("Triple-click detected on heart rate metric", "TRIPLE_CLICK")
            self.open_crash_log_dialog()
        
        # Call original mousePressEvent if it exists
        if hasattr(event, 'original_mousePressEvent'):
            event.original_mousePressEvent(event)
    
    def open_crash_log_dialog(self):
        """Open the crash log diagnostic dialog"""
        try:
            dialog = CrashLogDialog(self.crash_logger, self)
            dialog.exec_()
        except Exception as e:
            self.crash_logger.log_error(f"Failed to open crash log dialog: {str(e)}", e, "DIALOG_ERROR")
            QMessageBox.critical(self, "Error", f"Failed to open diagnostic dialog: {str(e)}")
    
    
    def update_ecg_metrics(self, intervals):
        if 'Heart_Rate' in intervals and intervals['Heart_Rate'] is not None:
            self.metric_labels['heart_rate'].setText(
                f"{int(round(intervals['Heart_Rate']))} bpm" if isinstance(intervals['Heart_Rate'], (int, float)) else str(intervals['Heart_Rate'])
            )
        if 'PR' in intervals and intervals['PR'] is not None:
            self.metric_labels['pr_interval'].setText(
                f"{int(round(intervals['PR']))} ms" if isinstance(intervals['PR'], (int, float)) else str(intervals['PR'])
            )
        if 'QRS' in intervals and intervals['QRS'] is not None:
            self.metric_labels['qrs_duration'].setText(
                f"{int(round(intervals['QRS']))} ms" if isinstance(intervals['QRS'], (int, float)) else str(intervals['QRS'])
            )
        # QTc label may not exist in current metrics card; update only if present
        # Check for 'QTc_interval' first (demo mode sends this as "400/430")
        if 'QTc_interval' in intervals and intervals['QTc_interval'] is not None and 'qtc_interval' in self.metric_labels:
            # QTc_interval is already in the correct format (e.g., "400/430")
            self.metric_labels['qtc_interval'].setText(f"{intervals['QTc_interval']} ms")
        elif 'QTc' in intervals and intervals['QTc'] is not None and 'qtc_interval' in self.metric_labels:
            if isinstance(intervals['QTc'], (int, float)) and intervals['QTc'] >= 0:
                self.metric_labels['qtc_interval'].setText(f"{int(round(intervals['QTc']))} ms")
            else:
                self.metric_labels['qtc_interval'].setText("-- ms")
        if 'QRS_axis' in intervals and intervals['QRS_axis'] is not None:
            self.metric_labels['qrs_axis'].setText(str(intervals['QRS_axis']))
        if 'ST' in intervals and intervals['ST'] is not None:
            # Current metrics card uses 'st_interval' key
            key = 'st_interval' if 'st_interval' in self.metric_labels else 'st_segment'
            self.metric_labels[key].setText(
                f"{int(round(intervals['ST']))} ms" if isinstance(intervals['ST'], (int, float)) else str(intervals['ST'])
            )
        # Also update the ECG test page theme if it exists
        if hasattr(self, 'ecg_test_page') and hasattr(self.ecg_test_page, 'update_metrics_frame_theme'):
            self.ecg_test_page.update_metrics_frame_theme(self.dark_mode, self.medical_mode)
    
    def sync_dashboard_metrics_to_ecg_page(self):
        """Sync dashboard's current metric values to ECG test page for consistency"""
        try:
            if not hasattr(self, 'ecg_test_page') or not self.ecg_test_page:
                return
                
            if not hasattr(self.ecg_test_page, 'metric_labels'):
                return
                
            # Sync metric values from dashboard to ECG test page
            # Extract numeric values from dashboard labels (e.g., "60 BPM" -> "60")
            if 'heart_rate' in self.metric_labels and 'heart_rate' in self.ecg_test_page.metric_labels:
                hr_text = self.metric_labels['heart_rate'].text()
                hr_value = hr_text.split()[0] if ' ' in hr_text else hr_text
                self.ecg_test_page.metric_labels['heart_rate'].setText(hr_value)
                
            if 'pr_interval' in self.metric_labels and 'pr_interval' in self.ecg_test_page.metric_labels:
                pr_text = self.metric_labels['pr_interval'].text()
                pr_value = pr_text.split()[0] if ' ' in pr_text else pr_text
                self.ecg_test_page.metric_labels['pr_interval'].setText(pr_value)
                
            if 'qrs_duration' in self.metric_labels and 'qrs_duration' in self.ecg_test_page.metric_labels:
                qrs_text = self.metric_labels['qrs_duration'].text()
                qrs_value = qrs_text.split()[0] if ' ' in qrs_text else qrs_text
                self.ecg_test_page.metric_labels['qrs_duration'].setText(qrs_value)
                
            if 'qrs_axis' in self.metric_labels and 'qrs_axis' in self.ecg_test_page.metric_labels:
                qrs_axis_text = self.metric_labels['qrs_axis'].text()
                qrs_axis_value = qrs_axis_text.replace('°', '') if '°' in qrs_axis_text else qrs_axis_text
                self.ecg_test_page.metric_labels['qrs_axis'].setText(f"{qrs_axis_value}°")
                
            if 'st_interval' in self.metric_labels and 'st_segment' in self.ecg_test_page.metric_labels:
                st_text = self.metric_labels['st_interval'].text()
                st_value = st_text.split()[0] if ' ' in st_text else st_text
                self.ecg_test_page.metric_labels['st_segment'].setText(st_value)
                
            # Handle qtc_interval - dashboard might have "400/430 ms" format
            if 'qtc_interval' in self.metric_labels and 'qtc_interval' in self.ecg_test_page.metric_labels:
                qtc_text = self.metric_labels['qtc_interval'].text()
                # Extract both QT and QTc values
                if '/' in qtc_text:
                    # Format: "400/430 ms" -> extract "400/430"
                    qtc_value = qtc_text.split()[0] if ' ' in qtc_text else qtc_text
                    self.ecg_test_page.metric_labels['qtc_interval'].setText(qtc_value)
                else:
                    # Single value
                    qtc_value = qtc_text.split()[0] if ' ' in qtc_text else qtc_text
                    self.ecg_test_page.metric_labels['qtc_interval'].setText(qtc_value)
                    
            print("✅ Synced dashboard metrics to ECG test page")
            
        except Exception as e:
            print(f"⚠️ Error syncing dashboard metrics to ECG test page: {e}")
    
    def update_dashboard_metrics_from_ecg(self):
        """Update dashboard metrics from ECG test page data"""
        try:
            # Block updates for first-time users until acquisition/demo starts
            if not self.is_ecg_active():
                return

            # In demo mode, use the fixed metrics values from demo_manager
            if hasattr(self, 'ecg_test_page') and hasattr(self.ecg_test_page, 'demo_toggle'):
                if self.ecg_test_page.demo_toggle.isChecked():
                    return

            if hasattr(self, 'ecg_test_page') and self.ecg_test_page:
                # Get current metrics from ECG test page
                if hasattr(self.ecg_test_page, 'get_current_metrics'):
                    ecg_metrics = self.ecg_test_page.get_current_metrics()
                    
                    # Update dashboard metrics with ECG test page data
                    if 'heart_rate' in ecg_metrics:
                        hr_text = ecg_metrics['heart_rate']
                        if hr_text and hr_text != '00' and hr_text != '--':
                            self.metric_labels['heart_rate'].setText(f"{hr_text} bpm")
                    
                    if 'pr_interval' in ecg_metrics:
                        pr_text = ecg_metrics['pr_interval']
                        if pr_text and pr_text != '--':
                            self.metric_labels['pr_interval'].setText(f"{pr_text} ms")
                    
                    if 'qrs_duration' in ecg_metrics:
                        qrs_text = ecg_metrics['qrs_duration']
                        if qrs_text and qrs_text != '--':
                            self.metric_labels['qrs_duration'].setText(f"{qrs_text} ms")
                    
                    if 'qrs_axis' in ecg_metrics:
                        qrs_axis_text = ecg_metrics['qrs_axis']
                        if qrs_axis_text and qrs_axis_text != '--':
                            self.metric_labels['qrs_axis'].setText(f"{qrs_axis_text}°")
                    
                    # if 'sampling_rate' in ecg_metrics:  # Commented out
                    #     sr_text = ecg_metrics['sampling_rate']
                    #     if sr_text and sr_text != '--':
                    #         self.metric_labels['sampling_rate'].setText(f"{sr_text}")
                    # Time Elapsed metric removed
                    
                    if 'st_interval' in ecg_metrics:
                        st_text = ecg_metrics['st_interval']
                        if st_text and st_text != '--':
                            self.metric_labels['st_interval'].setText(f"{st_text} ms")
                    
                    if 'qtc_interval' in ecg_metrics:
                        qtc_text = ecg_metrics['qtc_interval']
                        if qtc_text and qtc_text != '--':
                            self.metric_labels['qtc_interval'].setText(f"{qtc_text} ms")

                    # Record to session file if enabled
                    try:
                        recorder = getattr(self, '_session_recorder', None)
                        if recorder:
                            # Pack metrics in compact form
                            metrics_payload = {
                                'heart_rate': self.metric_labels['heart_rate'].text() if 'heart_rate' in self.metric_labels else None,
                                'pr_interval': self.metric_labels['pr_interval'].text() if 'pr_interval' in self.metric_labels else None,
                                'qrs_duration': self.metric_labels['qrs_duration'].text() if 'qrs_duration' in self.metric_labels else None,
                                'qrs_axis': self.metric_labels['qrs_axis'].text() if 'qrs_axis' in self.metric_labels else None,
                                'st_interval': self.metric_labels['st_interval'].text() if 'st_interval' in self.metric_labels else None,
                                # 'sampling_rate': self.metric_labels['sampling_rate'].text() if 'sampling_rate' in self.metric_labels else None,  # Commented out
                                'qtc_interval': self.metric_labels['qtc_interval'].text() if 'qtc_interval' in self.metric_labels else None,
                            }
                            # Update time elapsed for synchronization
                            if 'time_elapsed' in ecg_metrics and 'time_elapsed' in self.metric_labels:
                                self.metric_labels['time_elapsed'].setText(ecg_metrics['time_elapsed'])

                            # Snapshot last 5s per lead
                            from utils.session_recorder import SessionRecorder
                            ecg_snapshot = SessionRecorder.snapshot_from_ecg_page(self.ecg_test_page, seconds=5.0)
                            # Optional events hook: arrhythmia placeholder
                            events = {}
                            recorder.record(metrics_payload, ecg_snapshot, events)
                    except Exception as rec_err:
                        # Silent fail; never block UI
                        pass
                            
        except Exception as e:
            print(f"❌ Error updating dashboard metrics from ECG: {e}")
            
    def generate_pdf_report(self):
        from PyQt5.QtWidgets import QFileDialog, QMessageBox
        import datetime
        import os
        # Import the simple function from ecg_report_generator
        from ecg.ecg_report_generator import generate_ecg_report

        print(" Starting PDF report generation...")

        # Gather ECG data from dashboard metrics
        HR = self.metric_labels['heart_rate'].text().split()[0] if 'heart_rate' in self.metric_labels else "88"
        PR = self.metric_labels['pr_interval'].text().split()[0] if 'pr_interval' in self.metric_labels else "160"
        QRS = self.metric_labels['qrs_duration'].text().split()[0] if 'qrs_duration' in self.metric_labels else "90"
        
        # Extract QT and QTc from qtc_interval label (format: "QT/QTc" like "400/430")
        qtc_label_text = self.metric_labels['qtc_interval'].text() if 'qtc_interval' in self.metric_labels else "400/430 ms"
        # Remove " ms" suffix if present
        qtc_label_text = qtc_label_text.replace(" ms", "").strip()
        
        if '/' in qtc_label_text:
            # Split "400/430" format
            qt_qtc_parts = qtc_label_text.split('/')
            QT = qt_qtc_parts[0].strip() if len(qt_qtc_parts) > 0 else "400"
            QTc = qt_qtc_parts[1].strip() if len(qt_qtc_parts) > 1 else "430"
        else:
            # Fallback: if no "/" found, use the value as QTc and default QT
            QT = "400"
            QTc = qtc_label_text.strip()
        
        ST = self.metric_labels['st_segment'].text().split()[0] if 'st_segment' in self.metric_labels else "100"
        
        print(f"📊 PDF Report ECG Values - HR: {HR}, PR: {PR}, QRS: {QRS}, QT: {QT}, QTc: {QTc}, ST: {ST}")

        # Prepare data for the report generator
        ecg_data = {
            "HR": 4833,  # Total heartbeats
            "beat": int(HR) if HR.isdigit() else 88,  # Current heart rate
            "PR": int(PR) if PR.isdigit() else 160,
            "QRS": int(QRS) if QRS.isdigit() else 90,
            "QT": int(QT) if QT.isdigit() else 400,
            "QTc": int(QTc) if QTc.isdigit() else 400,
            "ST": int(ST) if ST.isdigit() else 100,
            "HR_max": 136,
            "HR_min": 74,
            "HR_avg": int(HR) if HR.isdigit() else 88,
        }

        # --- Capture last 10 seconds of live ECG data ---
        lead_img_paths = {}
        ordered_leads = ["I", "II", "III", "aVR", "aVL", "aVF", "V1", "V2", "V3", "V4", "V5", "V6"]
        
        print(" Capturing last 10 seconds of live ECG data...")
        
        # Get current directory for saving images
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(current_dir, '..'))
        
        # Capture live data from ECG test page
        if hasattr(self, 'ecg_test_page') and self.ecg_test_page and hasattr(self.ecg_test_page, 'data'):
            print(f" Found ECG test page with data: {len(self.ecg_test_page.data)} leads")
            
            # Calculate 10 seconds of data based on sampling rate
            sampling_rate = 250  # Default sampling rate
            if hasattr(self.ecg_test_page, 'sampler') and hasattr(self.ecg_test_page.sampler, 'sampling_rate'):
                try:
                    sampling_rate = float(self.ecg_test_page.sampler.sampling_rate)
                except:
                    sampling_rate = 250
            
            data_points_10_sec = int(sampling_rate * 10)  # 10 seconds of data
            print(f" Capturing {data_points_10_sec} data points at {sampling_rate}Hz")
            
            for i, lead in enumerate(ordered_leads):
                if i < len(self.ecg_test_page.data) and i < len(self.ecg_test_page.leads):
                    try:
                        # Get the last 10 seconds of data for this lead
                        lead_data = self.ecg_test_page.data[i]
                        if len(lead_data) > data_points_10_sec:
                            recent_data = lead_data[-data_points_10_sec:]
                        else:
                            recent_data = lead_data
                        
                        if len(recent_data) > 0:
                            # Create a clean plot for the report
                            import matplotlib.pyplot as plt
                            import matplotlib
                            matplotlib.use('Agg')  # Use non-interactive backend
                            
                            fig, ax = plt.subplots(figsize=(8, 2))
                            
                            # Plot the 10-second ECG trace
                            time_axis = np.linspace(0, 10, len(recent_data))  # 10 seconds
                            ax.plot(time_axis, recent_data, color='black', linewidth=0.8)
                            
                            # Clean medical-style formatting
                            ax.set_xlim(0, 10)
                            ax.set_xticks([0, 2, 4, 6, 8, 10])
                            ax.set_xticklabels(['0s', '2s', '4s', '6s', '8s', '10s'])
                            ax.set_ylabel('Amplitude (mV)')
                            ax.set_title(f'Lead {lead} - Last 10 seconds', fontsize=10, fontweight='bold')
                            
                            # Add subtle grid
                            ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)
                            ax.set_axisbelow(True)
                            
                            # Clean background
                            ax.set_facecolor('white')
                            fig.patch.set_facecolor('white')
                            
                            # Save the image
                            img_path = os.path.join(project_root, f"lead_{lead}_10sec.png")
                            fig.savefig(img_path, 
                                      bbox_inches='tight', 
                                      pad_inches=0.1, 
                                      dpi=150, 
                                      facecolor='white',
                                      edgecolor='none')
                            
                            plt.close(fig)  # Close to free memory
                            lead_img_paths[lead] = img_path
                            
                            print(f" ✅ Captured 10s Lead {lead}: {len(recent_data)} samples")
                        else:
                            print(f" ⚠️ No data available for Lead {lead}")
                            
                    except Exception as e:
                        print(f" ❌ Error capturing Lead {lead}: {e}")
                else:
                    print(f" ⚠️ Lead {lead} not available (index {i})")
        else:
            print(" ❌ No ECG test page or data available for capture")
        
        # Method 3: Check current stack widget for ECG pages
        if not lead_img_paths and hasattr(self, 'page_stack'):
            print(" Checking page stack for ECG test pages...")
            
            for i in range(self.page_stack.count()):
                widget = self.page_stack.widget(i)
                
                # Check if it's ECGTestPage
                if hasattr(widget, 'figures') and hasattr(widget, 'leads'):
                    print(f"Found ECG page in stack at index {i}")
                    
                    for j, lead in enumerate(ordered_leads):
                        if j < len(widget.figures):
                            try:
                                fig = widget.figures[j]
                                
                                # Medical-grade clean graph saving
                                if fig.axes:
                                    ax = fig.axes[0]
                                    ax.set_xticks([])
                                    ax.set_yticks([])
                                    ax.set_xlabel('')
                                    ax.set_ylabel('')
                                    ax.set_title('')
                                    
                                    for spine in ax.spines.values():
                                        spine.set_visible(False)
                                    
                                    ax.set_facecolor('none')
                                    fig.patch.set_facecolor('none')
                                    
                                    legend = ax.get_legend()
                                    if legend:
                                        legend.remove()
                                    
                                    for line in ax.lines:
                                        line.set_linewidth(0.4)       # Ultra-thin like reference
                                        line.set_antialiased(True)
                                        line.set_color('#000000')
                                        line.set_alpha(0.9)
                                        line.set_solid_capstyle('round')   # Rounded line endings
                                        line.set_solid_joinstyle('round')  # Rounded line joints
                                    
                                    ax.grid(True, color='#f0f0f0', linestyle='-', linewidth=0.3, alpha=0.7)
                                    ax.set_axisbelow(True)
                                
                                current_dir = os.path.dirname(os.path.abspath(__file__))
                                project_root = os.path.join(current_dir, '..')
                                project_root = os.path.abspath(project_root)
                                
                                img_path = os.path.join(project_root, f"lead_{lead}.png")
                                
                                fig.savefig(img_path, 
                                          bbox_inches='tight',
                                          pad_inches=0.05,
                                          dpi=200,
                                          facecolor='none',
                                          edgecolor='none',
                                          transparent=True)
                                
                                lead_img_paths[lead] = img_path
                                print(f" Saved medical-grade Lead {lead}")
                                
                            except Exception as e:
                                print(f" Error capturing Lead {lead}: {e}")
                    break
        
        # Method 4: Capture from PyQtGraph plot widgets (current 12-lead grid)
        if not lead_img_paths and hasattr(self, 'ecg_test_page') and self.ecg_test_page:
            if hasattr(self.ecg_test_page, 'plot_widgets') and self.ecg_test_page.plot_widgets:
                print(" Capturing ECG from PyQtGraph plot widgets...")
                try:
                    current_dir = os.path.dirname(os.path.abspath(__file__))
                    project_root = os.path.abspath(os.path.join(current_dir, '..'))
                    for i, lead in enumerate(ordered_leads):
                        if i < len(self.ecg_test_page.plot_widgets):
                            try:
                                w = self.ecg_test_page.plot_widgets[i]
                                pix = w.grab()  # QWidget -> QPixmap
                                img_path = os.path.join(project_root, f"lead_{lead}.png")
                                pix.save(img_path, 'PNG')
                                lead_img_paths[lead] = img_path
                                print(f" Saved PyQtGraph Lead {lead}: {img_path}")
                            except Exception as e:
                                print(f" Error capturing PyQtGraph Lead {lead}: {e}")
                except Exception as e:
                    print(f" PyQtGraph capture failed: {e}")

        # Report results
        if lead_img_paths:
            print(f" Successfully captured {len(lead_img_paths)}/12 real ECG graphs!")
        else:
            print(" No real ECG graphs found!")
            QMessageBox.warning(
                self,
                "No ECG Data",
                " No real ECG graphs found!\n\n Please:\n1. Start ECG test first\n2. Make sure 12-lead graphs are displayed\n3. Try again while ECG is running"
            )
            return
        
        # Ask user where to save the PDF
        filename, _ = QFileDialog.getSaveFileName(
            self, 
            "Save ECG Report", 
            f"ECG_Report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            "PDF Files (*.pdf)"
        )
        
        if filename:
            try:

                patient = getattr(self, "patient_details", None)
                if not patient:
                    try:
                        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
                        data_file = os.path.join(base_dir, "ecg_data.txt")
                        if os.path.exists(data_file):
                            with open(data_file, "r") as f:
                                lines = [l for l in f.readlines() if l.strip()]
                            if lines:
                                last = lines[-1]
                                parts = [x.strip() for x in last.split(",")]
                                if len(parts) >= 5:
                                    organisation, doctor, name, age, gender = parts[:5]
                                    first, *rest = name.split()
                                    patient = {
                                        "first_name": first,
                                        "last_name": " ".join(rest),
                                        "age": age,
                                        "gender": gender,
                                        "doctor": doctor
                                    }
                    except Exception:
                        patient = None

                # Always stamp current date/time from system
                now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                if not patient:
                    patient = {}
                patient["date_time"] = now_str

                # Force update conclusions before generating report
                self.update_live_conclusion()
                
                # Calculate wave amplitudes before generating report
                print("🔬 Calculating wave amplitudes for report...")
                if hasattr(self, 'ecg_test_page') and self.ecg_test_page:
                    try:
                        print(f"🔬 ECG test page found, calling calculate_wave_amplitudes()...")
                        wave_amps = self.ecg_test_page.calculate_wave_amplitudes()
                        print(f"🔬 Raw wave_amps returned: {wave_amps}")
                        
                        # Add wave amplitudes to ecg_data
                        ecg_data['p_amp'] = wave_amps.get('p_amp', 0.0)
                        ecg_data['qrs_amp'] = wave_amps.get('qrs_amp', 0.0)
                        ecg_data['t_amp'] = wave_amps.get('t_amp', 0.0)
                        ecg_data['rv5'] = wave_amps.get('rv5', 0.0)
                        ecg_data['sv1'] = wave_amps.get('sv1', 0.0)
                        
                        print(f"📊 Wave amplitudes added to ecg_data:")
                        print(f"   P={ecg_data['p_amp']:.4f}, QRS={ecg_data['qrs_amp']:.4f}, T={ecg_data['t_amp']:.4f}")
                        print(f"   RV5={ecg_data['rv5']:.4f}, SV1={ecg_data['sv1']:.4f}, RV5+SV1={ecg_data['rv5'] + ecg_data['sv1']:.4f}")
                        print(f"🔬 Final ecg_data keys: {ecg_data.keys()}")
                    except Exception as e:
                        print(f"⚠️ Error calculating wave amplitudes: {e}")
                        import traceback
                        traceback.print_exc()
                        ecg_data['p_amp'] = 0.0
                        ecg_data['qrs_amp'] = 0.0
                        ecg_data['t_amp'] = 0.0
                        ecg_data['rv5'] = 0.0
                        ecg_data['sv1'] = 0.0
                else:
                    print("⚠️ No ECG test page available for wave amplitude calculation")
                    ecg_data['p_amp'] = 0.0
                    ecg_data['qrs_amp'] = 0.0
                    ecg_data['t_amp'] = 0.0
                    ecg_data['rv5'] = 0.0
                    ecg_data['sv1'] = 0.0
                
                # Generate the PDF with patient details
                generate_ecg_report(filename, ecg_data, lead_img_paths, self, self.ecg_test_page, patient)
                
                QMessageBox.information(
                    self, 
                    "Success", 
                    f" ECG Report generated successfully!\n Saved as: {filename}\n Real graphs: {len(lead_img_paths)}/12"
                )
                
                print(f" PDF generated: {filename}")
                # Save a copy inside the app for Recent Reports + update index.json
                try:
                    import shutil, json
                    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
                    reports_dir = os.path.abspath(os.path.join(base_dir, "..", "reports"))
                    os.makedirs(reports_dir, exist_ok=True)
                    # Destination filename (keep basename)
                    dst_basename = os.path.basename(filename)
                    dst_path = os.path.join(reports_dir, dst_basename)
                    # Avoid overwrite
                    if os.path.abspath(filename) != os.path.abspath(dst_path):
                        counter = 1
                        base_name, ext = os.path.splitext(dst_basename)
                        while os.path.exists(dst_path):
                            dst_basename = f"{base_name}_{counter}{ext}"
                            dst_path = os.path.join(reports_dir, dst_basename)
                            counter += 1
                        shutil.copyfile(filename, dst_path)
                    # Update index.json (prepend)
                    index_path = os.path.join(reports_dir, "index.json")
                    items = []
                    if os.path.exists(index_path):
                        try:
                            with open(index_path, 'r') as f:
                                items = json.load(f)
                        except Exception:
                            items = []
                    now = datetime.datetime.now()
                    meta = {
                        "filename": os.path.basename(dst_path),
                        "title": "ECG Report",
                        "patient": "",  # Fill from form if available
                        "date": now.strftime('%Y-%m-%d'),
                        "time": now.strftime('%H:%M:%S')
                    }
                    items = [meta] + items
                    items = items[:10]
                    with open(index_path, 'w') as f:
                        json.dump(items, f, indent=2)
                    # Refresh dashboard list
                    self.refresh_recent_reports_ui()
                except Exception as idx_err:
                    print(f" Failed to update Recent Reports index: {idx_err}")

            except Exception as e:
                error_msg = f"Failed to generate PDF: {str(e)}"
                print(f" {error_msg}")
                QMessageBox.critical(self, "Error", error_msg)

    def animate_heartbeat(self):
        """Animate heart image synchronized with live heart rate and play sound"""
        import time
        
        current_time = time.time() * 1000  # Convert to milliseconds
        
        # Get current heart rate from metric card
        try:
            if 'heart_rate' in self.metric_labels:
                hr_text = self.metric_labels['heart_rate'].text()
                if hr_text and hr_text != "-- bpm" and "bpm" in hr_text:
                    # Extract heart rate number from text like "86 bpm"
                    hr_str = hr_text.replace(" bpm", "").strip()
                    if hr_str.isdigit():
                        self.current_heart_rate = int(hr_str)
                        # Calculate beat interval based on heart rate
                        if self.current_heart_rate > 0:
                            self.beat_interval = 60000 / self.current_heart_rate  # Convert BPM to ms between beats
        except Exception as e:
            print(f"⚠️ Error parsing heart rate: {e}")
        
        # Check if it's time for a heartbeat
        if current_time - self.last_beat_time >= self.beat_interval:
            self.last_beat_time = current_time
            
            # Play heartbeat sound with increased volume
            if self.heartbeat_sound:
                try:
                    # Try to set volume if available (some Qt versions support this)
                    if hasattr(self.heartbeat_sound, 'setVolume'):
                        self.heartbeat_sound.setVolume(100)  # Maximum volume
                    self.heartbeat_sound.play()
                except Exception as e:
                    print(f"⚠️ Error playing heartbeat sound: {e}")
            
            # Reset heartbeat phase for new beat
            self.heartbeat_phase = 0
        
        # Heartbeat effect: scale up and down based on phase
        # More pronounced beat when close to actual heartbeat
        time_since_beat = current_time - self.last_beat_time
        beat_progress = min(time_since_beat / self.beat_interval, 1.0)
        
        # Create a more realistic heartbeat pattern
        if beat_progress < 0.1:  # First 10% of cycle - sharp beat
            beat = 1 + 0.25 * math.sin(beat_progress * 10 * math.pi)
        elif beat_progress < 0.2:  # Next 10% - second beat
            beat = 1 + 0.15 * math.sin((beat_progress - 0.1) * 10 * math.pi)
        else:  # Rest of cycle - gradual return to normal
            beat = 1 + 0.05 * math.sin(self.heartbeat_phase)
        
        # Apply the beat effect
        size = int(self.heart_base_size * beat)
        self.heart_img.setPixmap(self.heart_pixmap.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        
        # Update phase for smooth animation
        self.heartbeat_phase += 0.18
        if self.heartbeat_phase > 2 * math.pi:
            self.heartbeat_phase -= 2 * math.pi
    
    def create_heartbeat_sound(self):
        """Create a synthetic heartbeat sound if no sound file is available.

        This generates a louder, normalized 'lub-dub' sound so it is clearly audible
        across devices. The waveform is normalized to full 16‑bit range.
        """
        try:
            import wave
            import struct
            import math
            
            # Create a simple heartbeat sound (lub-dub pattern)
            sample_rate = 22050
            duration = 0.6  # seconds
            samples = int(sample_rate * duration)
            
            # Generate heartbeat sound data
            sound_data = []
            for i in range(samples):
                t = i / sample_rate
                
                # First beat (lub) - lower frequency (louder envelope)
                if t < 0.1:
                    freq1 = 80  # Hz
                    amplitude = 1.0 * math.sin(2 * math.pi * freq1 * t) * math.exp(-t * 12)
                # Second beat (dub) - higher frequency (louder envelope)
                elif 0.2 < t < 0.3:
                    freq2 = 120  # Hz
                    amplitude = 0.95 * math.sin(2 * math.pi * freq2 * (t - 0.2)) * math.exp(-(t - 0.2) * 12)
                else:
                    amplitude = 0
                
                sound_data.append(amplitude)

            # Normalize to full 16‑bit range
            peak = max(1e-6, max(abs(x) for x in sound_data))
            norm = 32767.0 / peak
            pcm_data = [int(max(-32767, min(32767, x * norm))) for x in sound_data]
            
            # Save as WAV file
            heartbeat_path = get_asset_path("heartbeat.wav")
            with wave.open(heartbeat_path, 'w') as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(struct.pack('<' + 'h' * len(pcm_data), *pcm_data))
            
            # Load the created sound
            if QSound is not None:
                self.heartbeat_sound = QSound(heartbeat_path)
                print(f"✅ Created synthetic heartbeat sound: {heartbeat_path}")
            else:
                self.heartbeat_sound = None
                print(f"⚠️ QSound not available - heartbeat sound disabled")
            
        except Exception as e:
            print(f"⚠️ Could not create heartbeat sound: {e}")
            self.heartbeat_sound = None
    def handle_sign(self):
        if self.sign_btn.text() == "Sign In":
            dialog = SignInDialog(self)
            if dialog.exec_() == QDialog.Accepted:
                role, name = dialog.get_user_info()
                if not name.strip():
                    QMessageBox.warning(self, "Input Error", "Please enter your name.")
                    return
                # User label removed per request
                # self.user_label.setText(f"{name}\n{role}")
                self.sign_btn.setText("Sign Out")
        else:
            # User label removed per request
            # self.user_label.setText("Not signed in")
            self.sign_btn.setText("Sign In")
    def update_stress_and_hrv(self, ecg_signal, sampling_rate):
        """Calculate and update stress level and HRV from ECG data with smoothing"""
        try:
            from scipy.signal import find_peaks
            
            if len(ecg_signal) < 500:
                return
            
            # Find R-peaks
            peaks, _ = find_peaks(
                ecg_signal,
                height=np.mean(ecg_signal) + 0.5 * np.std(ecg_signal),
                distance=int(0.4 * sampling_rate)
            )
            
            if len(peaks) >= 3:
                # Calculate R-R intervals in milliseconds
                rr_intervals = np.diff(peaks) * (1000 / sampling_rate)
                
                # Filter valid intervals (300-2000 ms)
                valid_rr = rr_intervals[(rr_intervals >= 300) & (rr_intervals <= 2000)]
                
                if len(valid_rr) >= 2:
                    # HRV: Standard deviation of R-R intervals (SDNN)
                    current_hrv_ms = np.std(valid_rr)
                    
                    # Initialize rolling average for HRV smoothing
                    if not hasattr(self, '_hrv_history'):
                        self._hrv_history = []
                    
                    # Add current HRV to history (keep last 5 values for smoothing)
                    self._hrv_history.append(current_hrv_ms)
                    if len(self._hrv_history) > 5:
                        self._hrv_history.pop(0)
                    
                    # Use smoothed HRV value
                    smoothed_hrv_ms = np.mean(self._hrv_history)
                    
                    # Store for conclusion generation
                    self._current_hrv = smoothed_hrv_ms
                    
                    # Stress level based on smoothed HRV
                    if smoothed_hrv_ms > 100:
                        stress = "Low"
                        stress_color = "#27ae60"
                    elif smoothed_hrv_ms > 50:
                        stress = "Moderate"
                        stress_color = "#f39c12"
                    else:
                        stress = "High"
                        stress_color = "#e74c3c"
                    
                    # Update labels
                    if hasattr(self, 'stress_label'):
                        self.stress_label.setText(f"Stress Level: {stress}")
                        self.stress_label.setStyleSheet(f"font-size: 13px; color: {stress_color}; font-weight: bold;")
                    
                    if hasattr(self, 'hrv_label'):
                        self.hrv_label.setText(f"Average Variability: {int(smoothed_hrv_ms)}ms")
                        self.hrv_label.setStyleSheet("font-size: 13px; color: #666;")
        except Exception as e:
            print(f"⚠️ Error calculating stress/HRV: {e}")
    
    def update_live_conclusion(self):
        """Generate personalized conclusion based on current ECG metrics"""
        try:
            findings = []
            recommendations = []
            
            # Get current metrics
            hr_text = self.metric_labels.get('heart_rate', QLabel()).text()
            pr_text = self.metric_labels.get('pr_interval', QLabel()).text()
            qrs_text = self.metric_labels.get('qrs_duration', QLabel()).text()
            st_text = self.metric_labels.get('st_interval', QLabel()).text()
            
            # Parse values
            try:
                hr = int(hr_text.replace(' BPM', '').replace(' bpm', '').strip()) if hr_text and hr_text != '00' else 0
            except:
                hr = 0
            
            try:
                pr = int(pr_text.replace(' ms', '').strip()) if pr_text and pr_text != '0 ms' else 0
            except:
                pr = 0
            
            try:
                qrs = int(qrs_text.replace(' ms', '').strip()) if qrs_text and qrs_text != '0 ms' else 0
            except:
                qrs = 0
            
            # Analyze Heart Rate
            if hr > 0:
                if hr > 100:
                    findings.append("[!] <b>Tachycardia detected</b> - Heart rate elevated above normal range")
                    recommendations.append("• Consider relaxation techniques or consult physician")
                elif hr < 60:
                    findings.append("[i] <b>Bradycardia detected</b> - Heart rate below normal range")
                    recommendations.append("• May be normal for athletes, monitor symptoms")
                else:
                    findings.append("[OK] <b>Normal heart rate</b> - Within healthy range (60-100 BPM)")
            
            # Analyze PR Interval
            if pr > 0:
                if pr > 200:
                    findings.append("[!] <b>Prolonged PR interval</b> - Possible first-degree heart block")
                    recommendations.append("• Recommend clinical correlation and follow-up")
                elif pr < 120:
                    findings.append("[i] <b>Short PR interval</b> - May indicate pre-excitation")
                else:
                    findings.append("[OK] <b>Normal PR interval</b> - Conduction within normal limits")
            
            # Analyze QRS Duration
            if qrs > 0:
                if qrs > 120:
                    findings.append("[!] <b>Wide QRS complex</b> - Possible bundle branch block")
                    recommendations.append("• Consider 12-lead ECG analysis for bundle branch pattern")
                elif qrs > 100:
                    findings.append("[i] <b>Borderline QRS duration</b> - Monitor for changes")
                else:
                    findings.append("[OK] <b>Normal QRS duration</b> - Ventricular conduction normal")
            
            # Check HRV/Stress
            if hasattr(self, '_current_hrv'):
                hrv = self._current_hrv
                if hrv > 100:
                    findings.append("[OK] <b>Good heart rate variability</b> - Low stress indicated")
                elif hrv > 50:
                    findings.append("[i] <b>Moderate HRV</b> - Normal stress levels")
                else:
                    findings.append("[!] <b>Low HRV</b> - Elevated stress or fatigue")
                    recommendations.append("• Ensure adequate rest and stress management")
            
            # Build conclusion HTML
            if not findings:
                conclusion_html = """
                    <p style='color: #888; font-style: italic;'>
                    Waiting for stable ECG data...<br><br>
                    Metrics are being analyzed. Please wait a few seconds.
                    </p>
                """
            else:
                conclusion_html = "<b style='color: #ff6600;'>Findings:</b><br>"
                for f in findings:
                    conclusion_html += f + "<br>"
                
                if recommendations:
                    conclusion_html += "<br><b style='color: #ff6600;'>Recommendations:</b><br>"
                    for r in recommendations:
                        conclusion_html += r + "<br>"
                
                conclusion_html += """
                    <br><p style='font-size: 10px; color: #999; font-style: italic;'>
                    <b>NOTE:</b> This is an automated analysis for educational purposes only. 
                    Not a substitute for professional medical advice.
                    </p>
                """
            
            if hasattr(self, 'conclusion_box'):
                self.conclusion_box.setHtml(conclusion_html)
            
            # Save conclusions to JSON file for report generation (only if valid findings exist)
            try:
                import os
                import json
                from datetime import datetime
                import re
                
                # Only save if we have actual findings (not empty)
                if findings:
                    # Extract clean headings from findings (remove prefixes, HTML tags, and explanations)
                    clean_findings = []
                    for f in findings:
                        # Remove HTML tags first
                        text = re.sub(r'<[^>]+>', '', f).strip()
                        # Remove prefix markers like [i], [OK], [!]
                        text = re.sub(r'^\[.*?\]\s*', '', text).strip()
                        # Extract only the heading (before " - " if present)
                        if ' - ' in text:
                            text = text.split(' - ')[0].strip()
                        clean_findings.append(text)
                    
                    # Clean recommendations (remove HTML tags and bullet points)
                    clean_recommendations = []
                    for r in recommendations:
                        text = re.sub(r'<[^>]+>', '', r).strip()
                        # Remove bullet point if present
                        text = re.sub(r'^[•●○]\s*', '', text).strip()
                        clean_recommendations.append(text)
                    
                    conclusions_data = {
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "findings": clean_findings,
                        "recommendations": clean_recommendations
                    }
                    
                    # Save to project root directory
                    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
                    conclusions_file = os.path.join(base_dir, 'last_conclusions.json')
                    
                    with open(conclusions_file, 'w') as f:
                        json.dump(conclusions_data, f, indent=2)
                    
                    print(f"✅ Saved {len(clean_findings)} findings to last_conclusions.json")
                    print(f"   Findings: {clean_findings}")
                else:
                    print(f"⏭️ Skipped saving empty findings to last_conclusions.json (waiting for valid ECG data)")
                
            except Exception as save_err:
                print(f"⚠️ Error saving conclusions to JSON: {save_err}")
        
        except Exception as e:
            print(f"⚠️ Error updating conclusion: {e}")
    
    def update_session_time(self):
        """Update live session timer on both dashboard and ECG test page"""
        try:
            current_time = time.time()
            
            if self.is_ecg_active():
                # ECG IS active - timer is RUNNING
                if self.session_start_time is None:
                    # Starting fresh
                    self.session_start_time = current_time
                    self.session_total_paused_time = 0  # Track total paused duration
                    self.session_paused_at = None  # When current pause started
                    self.session_last_elapsed = 0  # Frozen elapsed time during pause
                    print("⏱️ Session timer started")
                
                # Check if we're resuming from a pause
                if self.session_paused_at is not None:
                    # We were paused and now resuming - add the paused duration to total
                    paused_duration = current_time - self.session_paused_at
                    self.session_total_paused_time += paused_duration
                    self.session_paused_at = None
                    print(f"⏯️ Resumed - total paused: {int(self.session_total_paused_time)}s")
                
                # Calculate elapsed time accounting for pauses
                elapsed = int(current_time - self.session_start_time - self.session_total_paused_time)
                mm = elapsed // 60
                ss = elapsed % 60
                time_str = f"{mm:02d}:{ss:02d}"
            else:
                # ECG is NOT active - timer is PAUSED
                if self.session_start_time is not None:
                    # Check if we're entering pause state for the first time (session_paused_at is None)
                    if self.session_paused_at is None:
                        # Just started pausing - record when pause started and capture elapsed time
                        self.session_paused_at = current_time
                        # Capture the elapsed time at the moment of pause
                        elapsed = int(current_time - self.session_start_time - self.session_total_paused_time)
                        self.session_last_elapsed = elapsed  # Store frozen elapsed time
                        print(f"⏸️ Timer paused at {elapsed}s")
                    
                    # Show FROZEN elapsed time (don't recalculate)
                    mm = self.session_last_elapsed // 60
                    ss = self.session_last_elapsed % 60
                    time_str = f"{mm:02d}:{ss:02d}"
                else:
                    # No session started yet - show 00:00
                    time_str = "00:00"
            
            # Update time on both dashboard and ECG test page for synchronization
            if 'time_elapsed' in self.metric_labels:
                self.metric_labels['time_elapsed'].setText(time_str)
            
            if hasattr(self, 'ecg_test_page') and hasattr(self.ecg_test_page, 'metric_labels'):
                if 'time_elapsed' in self.ecg_test_page.metric_labels:
                    self.ecg_test_page.metric_labels['time_elapsed'].setText(time_str)
        except Exception as e:
            print(f"⚠️ Error updating session time: {e}")
    
    def start_acquisition_timer(self):
        """Start the session timer when demo or hardware acquisition begins"""
        if self.session_start_time is None:
            # Starting fresh - never been started before
            self.session_start_time = time.time()
            self.session_total_paused_time = 0  # Reset paused time tracking
            self.session_paused_at = None
            print("⏱️ Session timer started (first time)")
        else:
            # Resuming from pause - adjust start time to account for paused duration
            if self.session_paused_at is not None:
                # Add the paused duration to total paused time
                paused_duration = time.time() - self.session_paused_at
                self.session_total_paused_time += paused_duration
                self.session_paused_at = None
                print(f"⏱️ Session timer resumed (was paused for {int(paused_duration)}s)")
            else:
                print(f"⏱️ Session timer already running")
    
    def handle_sign_out(self):
        # User label removed per request
        # self.user_label.setText("Not signed in")
        self.sign_btn.setText("Sign In")
        try:
            recorder = getattr(self, '_session_recorder', None)
            if recorder:
                recorder.close()
                self._session_recorder = None
        except Exception:
            pass
        try:
            if hasattr(self, 'session_timer'):
                self.session_timer.stop()
        except Exception:
            pass
        self.close()
    def go_to_lead_test(self):
        if hasattr(self, 'ecg_test_page') and hasattr(self.ecg_test_page, 'update_metrics_frame_theme'):
            self.ecg_test_page.update_metrics_frame_theme(self.dark_mode, self.medical_mode)
            
        self.page_stack.setCurrentWidget(self.ecg_test_page)
        # Sync dashboard metrics to ECG test page
        self.sync_dashboard_metrics_to_ecg_page()
        # Also update dashboard metrics when opening ECG test page
        self.update_dashboard_metrics_from_ecg()
    def go_to_dashboard(self):
        self.page_stack.setCurrentWidget(self.dashboard_page)
        # Update metrics when returning to dashboard
        self.update_dashboard_metrics_from_ecg()
    def update_internet_status(self):
        import socket
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=2)
            self.status_dot.setStyleSheet("border-radius: 9px; background: #00e676; border: 2px solid #fff;")
            self.status_dot.setToolTip("Connected to Internet")
        except Exception:
            self.status_dot.setStyleSheet("border-radius: 9px; background: #e74c3c; border: 2px solid #fff;")
            self.status_dot.setToolTip("No Internet Connection")
    def toggle_medical_mode(self):
        self.medical_mode = not self.medical_mode
        if self.medical_mode:
            # Medical color coding: blue/green/white (previous behavior)
            self.setStyleSheet("QWidget { background: #e3f6fd; } QFrame { background: #f8fdff; border-radius: 16px; } QLabel { color: #006266; }")
            self.medical_btn.setText("Normal Mode")
            self.medical_btn.setStyleSheet("background: #0984e3; color: white; border-radius: 10px; padding: 4px 18px;")
        else:
            self.setStyleSheet("")
            self.medical_btn.setText("Medical Mode")
            self.medical_btn.setStyleSheet("background: #00b894; color: white; border-radius: 10px; padding: 4px 18px;")
        # Update ECG test page theme if it exists
        if hasattr(self, 'ecg_test_page') and hasattr(self.ecg_test_page, 'update_metrics_frame_theme'):
            self.ecg_test_page.update_metrics_frame_theme(self.dark_mode, self.medical_mode)
            
    def toggle_dark_mode(self):
        self.dark_mode = not self.dark_mode
        if self.dark_mode:
            self.setStyleSheet("""
                QWidget { background: #181818; color: #fff; }
                QFrame { background: #232323 !important; border-radius: 16px; color: #fff; border: 2px solid #fff; }
                QLabel { color: #fff; }
                QPushButton { background: #333; color: #ff6600; border-radius: 10px; }
                QPushButton:checked { background: #ff6600; color: #fff; }
                QCalendarWidget QWidget { background: #232323; color: #fff; }
                QCalendarWidget QAbstractItemView { background: #232323; color: #fff; selection-background-color: #444; selection-color: #ff6600; }
                QTextEdit { background: #232323; color: #fff; border-radius: 12px; border: 2px solid #fff; }
            """)
            self.dark_btn.setText("Light Mode")
            # Set matplotlib canvas backgrounds to dark
            self.ecg_canvas.axes.set_facecolor("#232323")
            self.ecg_canvas.figure.set_facecolor("#232323")
            for child in self.findChildren(QFrame):
                child.setStyleSheet("background: #232323; border-radius: 16px; color: #fff; border: 2px solid #fff;")
            for key, label in self.metric_labels.items():
                label.setStyleSheet("color: #fff; background: transparent;")
                for canvas in child.findChildren(MplCanvas):
                    canvas.axes.set_facecolor("#232323")
                    canvas.figure.set_facecolor("#232323")
                    canvas.draw()
                for self.schedule_calendar in child.findChildren(QCalendarWidget):
                    self.schedule_calendar.setStyleSheet("background: #232323; color: #fff; border-radius: 12px; border: 2px solid #fff;")
                for txt in child.findChildren(QTextEdit):
                    txt.setStyleSheet("background: #232323; color: #fff; border-radius: 12px; border: 2px solid #fff;")
        else:
            self.setStyleSheet("")
            self.dark_btn.setText("Dark Mode")
            self.ecg_canvas.axes.set_facecolor("#eee")
            self.ecg_canvas.figure.set_facecolor("#fff")
            for child in self.findChildren(QFrame):
                child.setStyleSheet("")
            for key, label in self.metric_labels.items():
                label.setStyleSheet("color: #222; background: transparent;")
                for canvas in child.findChildren(MplCanvas):
                    canvas.axes.set_facecolor("#fff")
                    canvas.figure.set_facecolor("#fff")
                    canvas.draw()
                for self.schedule_calendar in child.findChildren(QCalendarWidget):
                    self.schedule_calendar.setStyleSheet("")
                for txt in child.findChildren(QTextEdit):
                    txt.setStyleSheet("")
        # Update ECG test page theme if it exists
        if hasattr(self, 'ecg_test_page') and hasattr(self.ecg_test_page, 'update_metrics_frame_theme'):
            self.ecg_test_page.update_metrics_frame_theme(self.dark_mode, self.medical_mode)
    
    def test_asset_paths(self):
        """
        Test all asset paths at startup to ensure they're working correctly.
        This helps with debugging path issues.
        """
        print("=== Testing Asset Paths ===")
        
        # Test common assets
        test_assets = ["her.png", "v.gif", "plasma.gif", "ECG1.png"]
        
        for asset in test_assets:
            path = get_asset_path(asset)
            exists = os.path.exists(path)
            print(f"{asset}: {'✓' if exists else '✗'} - {path}")
            
            if not exists:
                print(f"  Warning: {asset} not found!")
        
        print("=== Asset Path Test Complete ===\n")
    
    def change_background(self, background_type):
        """
        Change the dashboard background dynamically.
        
        Args:
            background_type (str): "plasma.gif", "tenor.gif", "v.gif", "solid", or "none"
        """
        if background_type == "none":
            self.use_gif_background = False
            self.bg_label.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #f8f9fa, stop:1 #e9ecef);")
            print("Background changed to solid color")
            return
        
        self.use_gif_background = True
        self.preferred_background = background_type
        
        # Stop current movie if any
        if hasattr(self.bg_label, 'movie'):
            self.bg_label.movie().stop()
        
        # Load new background
        movie = None
        if background_type == "plasma.gif":
            plasma_path = get_asset_path("plasma.gif")
            if os.path.exists(plasma_path):
                movie = QMovie(plasma_path)
                print("Background changed to plasma.gif")
            else:
                print("plasma.gif not found, keeping current background")
                return
        elif background_type == "tenor.gif":
            tenor_gif_path = get_asset_path("tenor.gif")
            if os.path.exists(tenor_gif_path):
                movie = QMovie(tenor_gif_path)
                print("Background changed to tenor.gif")
            else:
                print("tenor.gif not found, keeping current background")
                return
        elif background_type == "v.gif":
            v_gif_path = get_asset_path("v.gif")
            if os.path.exists(v_gif_path):
                movie = QMovie(v_gif_path)
                print("Background changed to v.gif")
            else:
                print("v.gif not found, keeping current background")
                return
        
        if movie:
            self.bg_label.setMovie(movie)
            movie.start()
            # Store reference to movie
            self.bg_label.movie = lambda: movie
    
    def cycle_background(self):
        """
        Cycle through different background options when the background button is clicked.
        """
        backgrounds = ["solid", "light_gradient", "dark_gradient", "medical_theme"]
        current_bg = "solid"  # Default to solid
        
        try:
            current_index = backgrounds.index(current_bg)
            next_index = (current_index + 1) % len(backgrounds)
            next_bg = backgrounds[next_index]
        except ValueError:
            next_bg = "solid"
        
        if next_bg == "solid":
            self.change_background("none")
            self.bg_btn.setText("BG: Solid")
        elif next_bg == "light_gradient":
            self.bg_label.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #ffffff, stop:1 #f0f0f0);")
            self.bg_btn.setText("BG: Light")
        elif next_bg == "dark_gradient":
            self.bg_label.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #2c3e50, stop:1 #34495e);")
            self.bg_btn.setText("BG: Dark")
        elif next_bg == "medical_theme":
            self.bg_label.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #e8f5e8, stop:1 #d4edda);")
            self.bg_btn.setText("BG: Medical")
        
    def center_on_screen(self):
        qr = self.frameGeometry()
        cp = QApplication.desktop().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def resizeEvent(self, event):
        """Handle window resize events to maintain responsive design"""
        super().resizeEvent(event)
        
        # Update background label size to match new window size
        if hasattr(self, 'bg_label'):
            self.bg_label.setGeometry(0, 0, self.width(), self.height())
        
        # Ensure all widgets maintain proper proportions
        self.update_layout_proportions()
    
    def update_layout_proportions(self):
        """Update layout proportions when window is resized"""
        # This method can be used to adjust layout proportions based on window size
        current_width = self.width()
        current_height = self.height()
        
        # Adjust font sizes based on window size for better readability
        if current_width < 1000:
            # Small window - use smaller fonts
            font_size = 12
        elif current_width < 1400:
            # Medium window - use medium fonts
            font_size = 14
        else:
            # Large window - use larger fonts
            font_size = 16
        
        # Update font sizes for better responsiveness
        for child in self.findChildren(QLabel):
            if hasattr(child, 'font'):
                current_font = child.font()
                if current_font.pointSize() > 8:  # Don't make fonts too small
                    current_font.setPointSize(max(8, font_size - 2))
                    child.setFont(current_font)
