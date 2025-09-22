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
from dashboard.chatbot_dialog import ChatbotDialog

# Try to import configuration, fallback to defaults if not available
try:
    import sys
    # Add the src directory to the path
    src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)
    
    try:
        from dashboard_config import get_background_config
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
    def __init__(self, username=None, role=None):
        super().__init__()
        
        # Set responsive size policy
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(800, 600)  # Minimum size for usability
        
        # Store username and role
        self.username = username
        self.role = role
        
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
        header.addWidget(self.medical_btn)
        
        self.dark_btn = QPushButton("Dark Mode")
        self.dark_btn.setCheckable(True)
        self.dark_btn.setStyleSheet("background: #222; color: #fff; border-radius: 10px; padding: 4px 18px;")
        self.dark_btn.clicked.connect(self.toggle_dark_mode)
        self.dark_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        header.addWidget(self.dark_btn)
        
        # Background control button
        bg_text = "BG: Clean"  # Default to clean background
        self.bg_btn = QPushButton(bg_text)
        self.bg_btn.setStyleSheet("background: #6c5ce7; color: white; border-radius: 10px; padding: 4px 18px;")
        self.bg_btn.clicked.connect(self.cycle_background)
        self.bg_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        header.addWidget(self.bg_btn)
        
        header.addStretch()
        
        self.user_label = QLabel(f"{username or 'User'}\n{role or ''}")
        self.user_label.setFont(QFont("Arial", 12))
        self.user_label.setAlignment(Qt.AlignRight)
        self.user_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        header.addWidget(self.user_label)
        
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
        
        greet = QLabel(f"<span style='font-size:18pt;font-weight:bold;'>{greeting}, {username or 'User'}</span><br><span style='color:#888;'>Welcome to your ECG dashboard</span>")
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
        
        heart_layout.addWidget(QLabel("Stress Level: Low"))
        heart_layout.addWidget(QLabel("Average Variability: 90ms"))
        
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
        self.ecg_canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        ecg_layout.addWidget(self.ecg_canvas)
        
        grid.addWidget(ecg_card, 1, 1)
        
        # --- Total Visitors (Pie Chart) ---
        visitors_card = QFrame()
        visitors_card.setStyleSheet("background: white; border-radius: 16px;")
        visitors_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        visitors_layout = QVBoxLayout(visitors_card)
        
        visitors_label = QLabel("Total Visitors")
        visitors_label.setFont(QFont("Arial", 14, QFont.Bold))
        visitors_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        visitors_layout.addWidget(visitors_label)
        
        pie_canvas = MplCanvas(width=2.5, height=2.5)
        pie_data = [30, 25, 30, 15]
        pie_labels = ["December", "November", "October", "September"]
        pie_colors = ["#ff6600", "#00b894", "#636e72", "#fdcb6e"]
        wedges, texts, autotexts = pie_canvas.axes.pie(
            pie_data, labels=pie_labels, autopct='%1.0f%%', colors=pie_colors, startangle=90
        )
        pie_canvas.axes.set_aspect('equal')
        pie_canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        visitors_layout.addWidget(pie_canvas)
        
        grid.addWidget(visitors_card, 1, 2)
        
        # --- Schedule Card ---
        schedule_card = QFrame()
        schedule_card.setStyleSheet("background: white; border-radius: 16px;")
        schedule_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        schedule_layout = QVBoxLayout(schedule_card)
        
        schedule_label = QLabel("Schedule")
        schedule_label.setFont(QFont("Arial", 14, QFont.Bold))
        schedule_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        schedule_layout.addWidget(schedule_label)
        cal = QCalendarWidget()
        cal.setFixedHeight(120)
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
                cal.setDateTextFormat(last_date, fmt)
            except Exception:
                pass
        schedule_layout.addWidget(cal)
        grid.addWidget(schedule_card, 2, 0)
        # --- Issue Found Card ---
        issue_card = QFrame()
        issue_card.setStyleSheet("background: white; border-radius: 16px;")
        issue_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        issue_layout = QVBoxLayout(issue_card)
        
        issue_label = QLabel("Issue Found")
        issue_label.setFont(QFont("Arial", 14, QFont.Bold))
        issue_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        issue_layout.addWidget(issue_label)
        
        issues_text = (
            "1. Heart Rate\n"
            "   • Tachycardia: Abnormally fast heart rate.\n"
            "   • Bradycardia: Abnormally slow heart rate.\n\n"
            "2. Heart Rhythm\n"
            "   • Normal Sinus Rhythm: Regular rhythm from the sinoatrial node.\n"
            "   • Arrhythmias: Irregular rhythms (e.g., atrial fibrillation, ventricular tachycardia, heart block).\n\n"
            "3. Electrical Conduction\n"
            "   • Heart block (1st, 2nd, 3rd degree), bundle branch blocks (right/left).\n\n"
            "4. Cardiac Size and Hypertrophy\n"
            "   • Enlarged chambers or hypertrophy (e.g., left ventricular hypertrophy).\n\n"
            "5. Ischemia and Infarction\n"
            "   • Ischemia: ST depression.\n"
            "   • Infarction: ST elevation, pathological Q waves.\n\n"
            "6. Electrolyte Abnormalities\n"
            "   • Hyperkalemia: Peaked T waves.\n"
            "   • Hypokalemia: Flattened/inverted T waves, U waves.\n"
            "   • Calcium: QT interval changes.\n\n"
            "7. Pericardial Disease\n"
            "   • Pericarditis: Diffuse ST elevation, PR depression.\n\n"
            "8. Pacemaker Activity\n"
            "   • Pacemaker function and capture.\n\n"
            "9. Drug Effects\n"
            "   • Digitalis, antiarrhythmics: Characteristic ECG changes.\n\n"
            "10. Cardiac Arrest Patterns\n"
            "   • Asystole, ventricular fibrillation, PEA."
        )
        
        issues_box = QTextEdit()
        issues_box.setReadOnly(True)
        issues_box.setText(issues_text)
        issues_box.setStyleSheet("background: #f7f7f7; border: none; font-size: 12px;")
        issues_box.setMinimumHeight(180)
        issues_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        issue_layout.addWidget(issues_box)
        
        grid.addWidget(issue_card, 2, 1, 1, 2)
        
        # --- ECG Monitor Metrics Cards ---
        metrics_card = QFrame()
        metrics_card.setStyleSheet("background: white; border-radius: 16px;")
        metrics_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        metrics_layout = QHBoxLayout(metrics_card)
        
        # Store metric labels for live update
        self.metric_labels = {}
        metric_info = [
            ("Heart Rate", "--", "BPM", "heart_rate"),
            ("PR Intervals", "--", "ms", "pr_interval"),
            ("QRS Complex", "--", "ms", "qrs_duration"),
            ("QRS Axis", "--", "", "qrs_axis"),
            ("ST Interval", "--", "ms", "st_interval"),
            ("Time Elapsed", "--", "", "time_elapsed"),
            ("Sampling Rate", "--", "Hz", "sampling_rate"),
        ]
        
        for title, value, unit, key in metric_info:
            box = QVBoxLayout()
            lbl = QLabel(title)
            lbl.setFont(QFont("Arial", 12, QFont.Bold))
            lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            val = QLabel(f"{value} {unit}")
            val.setFont(QFont("Arial", 18, QFont.Bold))
            val.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            box.addWidget(lbl)
            box.addWidget(val)
            metrics_layout.addLayout(box)
            self.metric_labels[key] = val  # Store reference for live update
        
        grid.addWidget(metrics_card, 0, 1, 1, 2)
        
        # Add the grid widget to the scroll area
        scroll_area.setWidget(grid_widget)
        
        # Add scroll area to dashboard layout
        dashboard_layout.addWidget(scroll_area)
        
        # Add generate report button
        self.generate_report_btn = QPushButton("Generate Report")
        self.generate_report_btn.setStyleSheet("background: #ff6600; color: white; border-radius: 10px; padding: 8px 24px; font-size: 16px; font-weight: bold;")
        self.generate_report_btn.clicked.connect(self.generate_pdf_report)
        self.generate_report_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        dashboard_layout.addWidget(self.generate_report_btn, alignment=Qt.AlignRight)
        
        # --- ECG Animation Setup ---
        self.ecg_x = np.linspace(0, 2, 500)
        self.ecg_y = 1000 + 200 * np.sin(2 * np.pi * 2 * self.ecg_x) + 50 * np.random.randn(500)
        self.ecg_line, = self.ecg_canvas.axes.plot(self.ecg_x, self.ecg_y, color="#ff6600", linewidth=0.5)
        self.anim = FuncAnimation(self.ecg_canvas.figure, self.update_ecg, interval=50, blit=True)
        
        # --- Dashboard Metrics Update Timer ---
        self.metrics_timer = QTimer(self)
        self.metrics_timer.timeout.connect(self.update_dashboard_metrics_from_ecg)
        self.metrics_timer.start(1000)  # Update every second
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

    def open_chatbot_dialog(self):
        dlg = ChatbotDialog(self)
        dlg.exec_()

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
            
            metrics['sampling_rate'] = f"{sampling_rate} Hz"
            
            # Calculate Time Elapsed (simulate based on data length)
            if len(ecg_signal) > 0:
                time_elapsed_sec = len(ecg_signal) / sampling_rate
                minutes = int(time_elapsed_sec // 60)
                seconds = int(time_elapsed_sec % 60)
                metrics['time_elapsed'] = f"{minutes:02d}:{seconds:02d}"
            
            return metrics
            
        except Exception as e:
            print(f"Error calculating live ECG metrics: {e}")
            return {}

    def update_dashboard_metrics_live(self, ecg_metrics):
        """Update dashboard metrics with live calculated values"""
        try:
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
            
            # Update Time Elapsed
            if 'time_elapsed' in ecg_metrics:
                self.metric_labels['time_elapsed'].setText(ecg_metrics['time_elapsed'])
            
            # Update Sampling Rate
            if 'sampling_rate' in ecg_metrics:
                self.metric_labels['sampling_rate'].setText(ecg_metrics['sampling_rate'])
            
        except Exception as e:
            print(f"Error updating live dashboard metrics: {e}")




    def update_ecg(self, frame):
        # Try to get data from ECG test page if available
        if hasattr(self, 'ecg_test_page') and self.ecg_test_page:
            try:
                # Get Lead II data from ECG test page (index 1 is Lead II)
                if hasattr(self.ecg_test_page, 'data') and len(self.ecg_test_page.data) > 1:
                    lead_ii_data = self.ecg_test_page.data[1]  # Lead II is at index 1
                    if len(lead_ii_data) > 10:
                        arr = np.array(lead_ii_data)
                        # Store original data for calculations
                        original_data = arr.copy()
                        
                        # Process data for display
                        arr = arr - np.mean(arr)
                        arr = arr + 1000  # Center vertically
                        if len(arr) < len(self.ecg_x):
                            arr = np.pad(arr, (len(self.ecg_x)-len(arr), 0), 'constant', constant_values=(1000,))
                        self.ecg_line.set_ydata(arr[-len(self.ecg_x):])
                        
                        # Get actual sampling rate from ECG test page
                        actual_sampling_rate = 500  # Default
                        if hasattr(self.ecg_test_page, 'sampler') and hasattr(self.ecg_test_page.sampler, 'sampling_rate') and self.ecg_test_page.sampler.sampling_rate:
                            actual_sampling_rate = float(self.ecg_test_page.sampler.sampling_rate)
                        
                        # Calculate and update live ECG metrics using ORIGINAL data with SAME sampling rate
                        ecg_metrics = self.calculate_live_ecg_metrics(original_data, sampling_rate=actual_sampling_rate)
                        self.update_dashboard_metrics_live(ecg_metrics)
                        
                        return [self.ecg_line]
            except Exception as e:
                print("Error getting data from ECG test page:", e)
        
        # Fallback: mock wave
        self.ecg_y = np.roll(self.ecg_y, -1)
        self.ecg_y[-1] = 1000 + 200 * np.sin(2 * np.pi * 2 * self.ecg_x[-1] + frame/10) + 50 * np.random.randn()
        self.ecg_line.set_ydata(self.ecg_y)
        
        # Create original mock data for calculations (without the +1000 offset)
        original_mock_data = self.ecg_y - 1000  # Remove the display offset
        
        # Calculate and update live ECG metrics for mock data too (use 500 Hz like ECG test page)
        ecg_metrics = self.calculate_live_ecg_metrics(original_mock_data, sampling_rate=500)
        self.update_dashboard_metrics_live(ecg_metrics)
        
        return [self.ecg_line]
    
    
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
        if 'QTc' in intervals and intervals['QTc'] is not None:
            if isinstance(intervals['QTc'], (int, float)) and intervals['QTc'] >= 0:
                self.metric_labels['qtc_interval'].setText(f"{int(round(intervals['QTc']))} ms")
            else:
                self.metric_labels['qtc_interval'].setText("-- ms")
        if 'QRS_axis' in intervals and intervals['QRS_axis'] is not None:
            self.metric_labels['qrs_axis'].setText(str(intervals['QRS_axis']))
        if 'ST' in intervals and intervals['ST'] is not None:
            self.metric_labels['st_segment'].setText(
                f"{int(round(intervals['ST']))} ms" if isinstance(intervals['ST'], (int, float)) else str(intervals['ST'])
            )
        # Also update the ECG test page theme if it exists
        if hasattr(self, 'ecg_test_page') and hasattr(self.ecg_test_page, 'update_metrics_frame_theme'):
            self.ecg_test_page.update_metrics_frame_theme(self.dark_mode, self.medical_mode)
    
    def update_dashboard_metrics_from_ecg(self):
        """Update dashboard metrics from ECG test page data"""
        try:
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
                    
                    if 'sampling_rate' in ecg_metrics:
                        sr_text = ecg_metrics['sampling_rate']
                        if sr_text and sr_text != '--':
                            self.metric_labels['sampling_rate'].setText(f"{sr_text}")
                            
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
        QT = "380"  # Default value
        QTc = self.metric_labels['qtc_interval'].text().split()[0] if 'qtc_interval' in self.metric_labels else "400"
        ST = self.metric_labels['st_segment'].text().split()[0] if 'st_segment' in self.metric_labels else "100"

        # Prepare data for the report generator
        ecg_data = {
            "HR": 4833,  # Total heartbeats
            "beat": int(HR) if HR.isdigit() else 88,  # Current heart rate
            "PR": int(PR) if PR.isdigit() else 160,
            "QRS": int(QRS) if QRS.isdigit() else 90,
            "QT": int(QT) if QT.isdigit() else 380,
            "QTc": int(QTc) if QTc.isdigit() else 400,
            "ST": int(ST) if ST.isdigit() else 100,
            "HR_max": 136,
            "HR_min": 74,
            "HR_avg": int(HR) if HR.isdigit() else 88,
        }

        # --- UPDATED: Better real ECG graph capture ---
        lead_img_paths = {}
        ordered_leads = ["I", "II", "III", "aVR", "aVL", "aVF", "V1", "V2", "V3", "V4", "V5", "V6"]
        
        print(" Looking for ECG test page...")
        
        # Method 1: Check if ecg_test_page exists and has figures
        if hasattr(self, 'ecg_test_page') and self.ecg_test_page:
            print(f" Found ecg_test_page: {type(self.ecg_test_page)}")
            
            # Check if figures array exists
            if hasattr(self.ecg_test_page, 'figures') and self.ecg_test_page.figures:
                print(f" Found {len(self.ecg_test_page.figures)} figures in ECGTestPage")
                
                for i, lead in enumerate(ordered_leads):
                    if i < len(self.ecg_test_page.figures):
                        try:
                            # MEDICAL GRADE CLEAN GRAPH SAVING
                            fig = self.ecg_test_page.figures[i]
                            
                            # Clean the figure for medical report
                            if fig.axes:
                                ax = fig.axes[0]
                                
                                # REMOVE ALL NUMBERS AND LABELS
                                ax.set_xticks([])          # Remove X-axis numbers
                                ax.set_yticks([])          # Remove Y-axis numbers
                                ax.set_xlabel('')          # Remove X label
                                ax.set_ylabel('')          # Remove Y label
                                ax.set_title('')           # Remove title
                                
                                # Remove axis borders (spines)
                                for spine in ax.spines.values():
                                    spine.set_visible(False)
                                
                                # Clean background - MAKE TRANSPARENT
                                ax.set_facecolor('none')          
                                fig.patch.set_facecolor('none')   
                                # Remove legend if exists
                                legend = ax.get_legend()
                                if legend:
                                    legend.remove()
                                
                                # Make ECG line smooth and medical-grade
                                for line in ax.lines:
                                    line.set_linewidth(0.4)       # Ultra-thin 
                                    line.set_antialiased(True)    # Maximum smoothness
                                    line.set_color('#000000')     # Pure black
                                    line.set_alpha(0.9)           # Slightly transparent for medical look
                                    line.set_solid_capstyle('round')   
                                    line.set_solid_joinstyle('round')  
                                
                                # Add subtle medical-style grid (optional)
                                ax.grid(True, 
                                       color='#f0f0f0',          # Very light grey
                                       linestyle='-', 
                                       linewidth=0.3, 
                                       alpha=0.7)
                                ax.set_axisbelow(True)
                            
                            # Get absolute path to project root
                            current_dir = os.path.dirname(os.path.abspath(__file__))
                            project_root = os.path.join(current_dir, '..')
                            project_root = os.path.abspath(project_root)
                            
                            img_path = os.path.join(project_root, f"lead_{lead}.png")
                            
                            # Save medical-grade image
                            fig.savefig(img_path, 
                                      bbox_inches='tight',     # Remove extra space
                                      pad_inches=0.05,         # Minimal padding
                                      dpi=200,                 # High resolution for print
                                      facecolor='none',        # Transparent
                                      edgecolor='none',        # No border
                                      transparent=True)       # Enable transparency
                            
                            lead_img_paths[lead] = img_path
                            
                            print(f" Saved medical-grade Lead {lead}: {img_path}")
                            
                        except Exception as e:
                            print(f" Error capturing Lead {lead}: {e}")
                    else:
                        print(f"  No figure available for Lead {lead} (index {i})")
            
            # Method 2: Check canvases if figures not available
            elif hasattr(self.ecg_test_page, 'canvases') and self.ecg_test_page.canvases:
                print(f" Found {len(self.ecg_test_page.canvases)} canvases in ECGTestPage")
                
                for i, lead in enumerate(ordered_leads):
                    if i < len(self.ecg_test_page.canvases):
                        try:
                            canvas = self.ecg_test_page.canvases[i]
                            fig = canvas.figure
                            
                            # MEDICAL GRADE CLEAN GRAPH SAVING (same as above)
                            if fig.axes:
                                ax = fig.axes[0]
                                
                                # REMOVE ALL NUMBERS AND LABELS
                                ax.set_xticks([])         
                                ax.set_yticks([])          
                                ax.set_xlabel('')         
                                ax.set_ylabel('')          
                                ax.set_title('')           
                                
                                # Remove axis borders
                                for spine in ax.spines.values():
                                    spine.set_visible(False)
                                
                                # Clean background - MAKE TRANSPARENT  
                                ax.set_facecolor('none')          # Transparent axis
                                fig.patch.set_facecolor('none')   # Transparent figure
                                
                                # Remove legend
                                legend = ax.get_legend()
                                if legend:
                                    legend.remove()
                                
                                # Medical-grade line styling
                                for line in ax.lines:
                                    line.set_linewidth(0.4)       # Ultra-thin like reference
                                    line.set_antialiased(True)
                                    line.set_color('#000000')
                                    line.set_alpha(0.9)
                                    line.set_solid_capstyle('round')   # Rounded line endings
                                    line.set_solid_joinstyle('round')  # Rounded line joints
                                
                                # Subtle medical grid
                                ax.grid(True, color='#f0f0f0', linestyle='-', linewidth=0.3, alpha=0.7)
                                ax.set_axisbelow(True)
                            
                            # Save path
                            current_dir = os.path.dirname(os.path.abspath(__file__))
                            project_root = os.path.join(current_dir, '..')
                            project_root = os.path.abspath(project_root)
                            
                            img_path = os.path.join(project_root, f"lead_{lead}.png")
                            
                            # Save medical-grade image
                            fig.savefig(img_path, 
                                      bbox_inches='tight',
                                      pad_inches=0.05,
                                      dpi=200,
                                      facecolor='none',
                                      edgecolor='none',
                                      transparent=True)
                            
                            lead_img_paths[lead] = img_path
                            print(f"Saved clean Lead {lead}")
                            
                        except Exception as e:
                            print(f" Error capturing Lead {lead}: {e}")
            else:
                print(" No figures or canvases found in ECGTestPage")
        else:
            print(" No ecg_test_page found in dashboard")
        
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
                # Generate the PDF using the simple function from ecg_report_generator
                generate_ecg_report(filename, ecg_data, lead_img_paths)
                
                QMessageBox.information(
                    self, 
                    "Success", 
                    f" ECG Report generated successfully!\n Saved as: {filename}\n Real graphs: {len(lead_img_paths)}/12"
                )
                
                print(f" PDF generated: {filename}")
                
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
                self.user_label.setText(f"{name}\n{role}")
                self.sign_btn.setText("Sign Out")
        else:
            self.user_label.setText("Not signed in")
            self.sign_btn.setText("Sign In")
    def handle_sign_out(self):
        self.user_label.setText("Not signed in")
        self.sign_btn.setText("Sign In")
        self.close()
    def go_to_lead_test(self):
        if hasattr(self, 'ecg_test_page') and hasattr(self.ecg_test_page, 'update_metrics_frame_theme'):
            self.ecg_test_page.update_metrics_frame_theme(self.dark_mode, self.medical_mode)
            
        self.page_stack.setCurrentWidget(self.ecg_test_page)
        # Update metrics when opening ECG test page
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
            # Medical color coding: blue/green/white
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
                for cal in child.findChildren(QCalendarWidget):
                    cal.setStyleSheet("background: #232323; color: #fff; border-radius: 12px; border: 2px solid #fff;")
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
                for cal in child.findChildren(QCalendarWidget):
                    cal.setStyleSheet("")
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