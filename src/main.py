"""
ECG Monitor Application - Main Entry Point
A comprehensive ECG monitoring application with real-time analysis and visualization.
"""

import sys
import os
import json
from PyQt5.QtWidgets import (
    QApplication, QDialog, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, 
    QMessageBox, QStackedWidget, QWidget, QInputDialog, QSizePolicy
)
from PyQt5.QtCore import Qt
from utils.crash_logger import get_crash_logger
from utils.session_recorder import SessionRecorder
from PyQt5.QtGui import QFont, QPixmap

# Import core modules
try:
    from core.logging_config import get_logger, log_function_call
    from core.exceptions import ECGError, ECGConfigError
    from config.settings import get_config, resource_path
    from core.constants import SUCCESS_MESSAGES, ERROR_MESSAGES
    logger_available = True
except ImportError as e:
    print(f"⚠️ Core modules not available: {e}")
    print("💡 Using fallback logging")
    logger_available = False
    
    # Fallback logging
    class FallbackLogger:
        def info(self, msg): print(f"INFO: {msg}")
        def error(self, msg): print(f"ERROR: {msg}")
        def warning(self, msg): print(f"WARNING: {msg}")
        def debug(self, msg): print(f"DEBUG: {msg}")
    
    def log_function_call(func):
        return func
    
    def get_config():
        return type('Config', (), {'get': lambda x, y=None: y})()
    
    def resource_path(relative_path):
        if hasattr(sys, '_MEIPASS'):
            return os.path.join(sys._MEIPASS, relative_path)
        return os.path.join(os.path.abspath("."), relative_path)
    
    SUCCESS_MESSAGES = {"modules_loaded": "✅ Core modules imported successfully"}
    ERROR_MESSAGES = {"import_error": "❌ Core module import error: {}"}

# Initialize logger
if logger_available:
    logger = get_logger("MainApp")
else:
    logger = FallbackLogger()

# Import application modules with proper error handling
try:
    from auth.sign_in import SignIn
    from auth.sign_out import SignOut
    from dashboard.dashboard import Dashboard
    from splash_screen import SplashScreen
    logger.info(SUCCESS_MESSAGES["modules_loaded"])
except ImportError as e:
    logger.error(ERROR_MESSAGES["import_error"].format(e))
    logger.error("💡 Make sure you're running from the src directory")
    logger.error("💡 Try: cd src && python main.py")
    sys.exit(1)

# Import ECG modules with fallback
try:
    from ecg.pan_tompkins import pan_tompkins
    logger.info(SUCCESS_MESSAGES["ecg_modules_loaded"])
except ImportError as e:
    logger.warning(ERROR_MESSAGES["ecg_import_warning"].format(e))
    logger.warning("💡 ECG analysis features may be limited")
    # Create a dummy function to prevent errors
    def pan_tompkins(ecg, fs=500):
        return []

# Get configuration
config = get_config()
USER_DATA_FILE = resource_path("users.json")


@log_function_call
def load_users():
    """Load user data from file with error handling"""
    try:
        if os.path.exists(USER_DATA_FILE):
            with open(USER_DATA_FILE, "r") as f:
                users = json.load(f)
                logger.info(f"Loaded {len(users)} users from {USER_DATA_FILE}")
                return users
        else:
            logger.info(f"User file {USER_DATA_FILE} not found, creating empty user database")
            return {}
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Error loading users: {e}")
        logger.error("Creating empty user database")
        return {}


@log_function_call
def save_users(users):
    """Save user data to file with error handling"""
    try:
        with open(USER_DATA_FILE, "w") as f:
            json.dump(users, f, indent=2)
        logger.info(f"Saved {len(users)} users to {USER_DATA_FILE}")
    except IOError as e:
        logger.error(f"Error saving users: {e}")
        raise ECGError(f"Failed to save user data: {e}")


# Login/Register Dialog
class LoginRegisterDialog(QDialog):
    def __init__(self):
        super().__init__()
        
        # Set responsive size policy
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(800, 600)  # Minimum size for usability
        
        # Set window properties for better responsiveness
        self.setWindowTitle("CardioX by Deckmount - Sign In / Sign Up")
        self.setWindowFlags(Qt.Window | Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint)
        
        # Initialize sign-in logic
        from auth.sign_in import SignIn
        self.sign_in_logic = SignIn()
        
        # Center the window on screen
        self.center_on_screen()
        
        self.init_ui()
        self.result = False
        self.username = None
        self.user_details = {}
        self.center_on_screen( )

    def center_on_screen(self):
        qr = self.frameGeometry()
        cp = QApplication.desktop().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def init_ui(self):
        # Set up GIF background
        self.bg_label = QLabel(self)
        self.bg_label.setGeometry(0, 0, self.width(), self.height())
        self.bg_label.lower()
        
        # Try multiple possible paths for the v.gif file
        possible_gif_paths = [
            resource_path('assets/v.gif'),
            resource_path('../assets/v.gif'),
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'assets', 'v.gif'),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets', 'v.gif')
        ]
        
        gif_path = None
        for path in possible_gif_paths:
            if os.path.exists(path):
                gif_path = path
                print(f"✅ Found v.gif at: {gif_path}")
                break
        
        if gif_path and os.path.exists(gif_path):
            try:
                from PyQt5.QtGui import QMovie
                movie = QMovie(gif_path)
                if movie.isValid():
                    self.bg_label.setMovie(movie)
                    movie.start()
                    print("✅ v.gif background started successfully")
                else:
                    print("❌ Invalid GIF file")
                    # Set fallback background
                    self.bg_label.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1a1a2e, stop:1 #16213e);")
            except Exception as e:
                print(f"❌ Error loading v.gif: {e}")
                # Set fallback background
                self.bg_label.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1a1a2e, stop:1 #16213e);")
        else:
            print("❌ v.gif not found in any expected location")
            print(f"Tried paths: {possible_gif_paths}")
            # Set fallback background
            self.bg_label.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1a1a2e, stop:1 #16213e);")
        
        self.bg_label.setScaledContents(True)
        # --- Title and tagline above glass ---
        main_layout = QVBoxLayout(self)
        main_layout.addStretch(1)
        # Title (outside glass) - logo style
        title = QLabel("CardioX by Deckmount")
        title.setFont(QFont("Arial", 52, QFont.Black))
        title.setStyleSheet("""
            color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #ff6600, stop:1 #ffb347);
            letter-spacing: 4px;
            margin-bottom: 0px;        
            padding-top: 0px;
            padding-bottom: 0px;
            font-weight: 900;
            border-radius: 18px;
        """)
        title.setAlignment(Qt.AlignHCenter)
        main_layout.addWidget(title)
        # Tagline (outside glass)
        tagline = QLabel("Built to Detect. Designed to Last.")
        tagline.setFont(QFont("Arial", 18, QFont.Bold))
        tagline.setStyleSheet("color: #ff6600; margin-bottom: 18px; margin-top: 0px; background: rgba(255,255,255,0.1);")
        tagline.setAlignment(Qt.AlignHCenter)
        main_layout.addWidget(tagline)
        # --- Glass effect container in center ---
        row = QHBoxLayout()
        row.addStretch(1)
        glass = QWidget(self)
        glass.setObjectName("Glass")
        glass.setStyleSheet("""
            QWidget#Glass {

                background: rgba(255,255,255,0.18);
                border-radius: 24px;
                border: 2px solid rgba(255,255,255,0.35);zx
            }
        """)
        glass.setMinimumSize(600, 520)
        # Create stacked widget and login/register widgets BEFORE using stacked_col
        self.stacked = QStackedWidget(glass)
        self.login_widget = self.create_login_widget()
        self.register_widget = self.create_register_widget()
        self.stacked.addWidget(self.login_widget)
        self.stacked.addWidget(self.register_widget)
        glass_layout = QHBoxLayout(glass)
        glass_layout.setContentsMargins(32, 32, 32, 32)
        # ECG image inside glass, left side (larger)
        ecg_img = QLabel()
        ecg_pix = QPixmap(resource_path('assets/v1.png'))
        if not ecg_pix.isNull():
            ecg_img.setPixmap(ecg_pix.scaled(400, 600, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            ecg_img.setAlignment(Qt.AlignVCenter | Qt.AlignHCenter)
            ecg_img.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            ecg_img.setStyleSheet("margin: 0px 32px 0px 0px; border-radius: 24px; background: transparent;")
        # Wrap image in a layout to center vertically
        img_col = QVBoxLayout()
        img_col.addStretch(1)
        img_col.addWidget(ecg_img, alignment=Qt.AlignHCenter)
        img_col.addStretch(1)
        glass_layout.addLayout(img_col, 2)
        # Login/Register stacked widget (vertical)
        stacked_col = QVBoxLayout()
        stacked_col.addStretch(1)
        stacked_col.addWidget(self.stacked, 2)
        # Add sign up/login prompt below
        signup_row = QHBoxLayout()
        signup_row.addStretch(1)
        signup_lbl = QLabel("Don't have an account?")
        signup_lbl.setStyleSheet("color: #fff; font-size: 15px;")
        signup_btn = QPushButton("Sign up")
        signup_btn.setStyleSheet("color: #ff6600; background: transparent; border: none; font-size: 15px; font-weight: bold; text-decoration: underline;")
        signup_btn.clicked.connect(lambda: self.stacked.setCurrentIndex(1))
        signup_row.addWidget(signup_lbl)
        signup_row.addWidget(signup_btn)
        signup_row.addStretch(1)
        stacked_col.addSpacing(10)
        stacked_col.addLayout(signup_row)
        # Add login prompt to register widget
        login_row = QHBoxLayout()
        
        login_row.addStretch(1)
        login_lbl = QLabel("Already have an account?")
        login_lbl.setStyleSheet("color: #fff; font-size: 15px;")
        login_btn = QPushButton("Login")
        login_btn.setStyleSheet("color: #ff6600; background: transparent; border: none; font-size: 15px; font-weight: bold; text-decoration: underline;")
        login_btn.clicked.connect(lambda: self.stacked.setCurrentIndex(0))
        login_row.addWidget(login_lbl)
        login_row.addWidget(login_btn)
        login_row.addStretch(1)
        # Insert login_row at the bottom of the register widget
        self.register_widget.layout().addSpacing(10)
        self.register_widget.layout().addLayout(login_row)
        stacked_col.addStretch(1)
        glass_layout.addLayout(stacked_col, 3)
        glass_layout.setSpacing(0)
        row.addWidget(glass, 1)
        row.addStretch(1)
        main_layout.addLayout(row)
        main_layout.addStretch(1)   
        self.setLayout(main_layout)
        # Make glass and all widgets expand responsively
        glass.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # Resize background with window
        self.resizeEvent = self._resize_bg
        
        # Ensure background is always visible
        self.ensure_background_visible()


    def _resize_bg(self, event):
        """Handle window resize to maintain background coverage"""
        self.bg_label.setGeometry(0, 0, self.width(), self.height())
        # Ensure the background stays behind all other widgets
        self.bg_label.lower()
        event.accept()
    
    def ensure_background_visible(self):
        """Ensure the background is always visible and properly positioned"""
        try:
            # Make sure the background label is at the bottom of the widget stack
            self.bg_label.lower()
            # Ensure it covers the entire window
            self.bg_label.setGeometry(0, 0, self.width(), self.height())
            # Make sure it's visible
            self.bg_label.setVisible(True)
            logger.info("✅ Background visibility ensured")
        except Exception as e:
            logger.warning(f"Background visibility issue: {e}")

    def create_login_widget(self):
        widget = QWidget()
        layout = QVBoxLayout()
        self.login_email = QLineEdit()
        self.login_email.setPlaceholderText("Full Name or Phone Number")
        self.login_password = QLineEdit()
        self.login_password.setPlaceholderText("Password (or Machine Serial ID)")
        self.login_password.setEchoMode(QLineEdit.Password)
        login_btn = QPushButton("Login")
        login_btn.setObjectName("LoginBtn")
        login_btn.setStyleSheet("background: #ff6600; color: white; border-radius: 10px; padding: 8px 0; font-size: 16px; font-weight: bold;")
        login_btn.clicked.connect(self.handle_login)
        phone_btn = QPushButton("Login with Phone Number")
        phone_btn.setObjectName("SignUpBtn")
        phone_btn.setStyleSheet("background: #ff6600; color: white; border-radius: 10px; padding: 8px 0; font-size: 16px; font-weight: bold;")
        phone_btn.clicked.connect(self.handle_phone_login)
        for w in [self.login_email, self.login_password, login_btn, phone_btn]:
            w.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.login_email.setStyleSheet("border: 2px solid #ff6600; border-radius: 8px; padding: 6px 10px; font-size: 15px; background: #f7f7f7; color: #222;")
        self.login_password.setStyleSheet("border: 2px solid #ff6600; border-radius: 8px; padding: 6px 10px; font-size: 15px; background: #f7f7f7; color: #222;")
        layout.addWidget(self.login_email)
        layout.addWidget(self.login_password)
        layout.addWidget(login_btn)
        layout.addWidget(phone_btn)
        # Add nav links under phone_btn
        nav_row = QHBoxLayout()
        # Navigation modules moved to clutter - using fallback
        try:
            # Try to import from clutter directory
            import sys
            clutter_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'clutter')
            if clutter_path not in sys.path:
                sys.path.insert(0, clutter_path)
            
            from nav_home import NavHome
            from nav_about import NavAbout
            from nav_blog import NavBlog
            from nav_pricing import NavPricing
        except ImportError as e:
            logger.warning(f"Navigation modules not available: {e}")
            # Create fallback navigation classes
            class NavHome(QWidget):
                def __init__(self): super().__init__(); self.setWindowTitle("Home")
            class NavAbout(QWidget):
                def __init__(self): super().__init__(); self.setWindowTitle("About")
            class NavBlog(QWidget):
                def __init__(self): super().__init__(); self.setWindowTitle("Blog")
            class NavPricing(QWidget):
                def __init__(self): super().__init__(); self.setWindowTitle("Pricing")
        nav_links = [
            ("Home", NavHome),
            ("About us", NavAbout),
            ("Blog", NavBlog),
            ("Pricing", NavPricing)
        ]
        self.nav_stack = QStackedWidget()
        self.nav_pages = {}
        def show_nav_page(page_name):
            self.nav_stack.setCurrentWidget(self.nav_pages[page_name])
            self.nav_stack.setVisible(True)
        for text, NavClass in nav_links:
            nav_btn = QPushButton(text)
            nav_btn.setStyleSheet("color: #ff6600; background: transparent; border: none; font-size: 15px; font-weight: bold; text-decoration: underline;")
            page = NavClass()
            self.nav_stack.addWidget(page)
            self.nav_pages[text] = page
            if text == "Pricing":
                try:
                    # Try to import from clutter directory
                    from nav_pricing import show_pricing_dialog
                except ImportError as e:
                    logger.warning(f"Pricing dialog not available: {e}")
                    # Create fallback pricing dialog
                    def show_pricing_dialog():
                        QMessageBox.information(self, "Pricing", "Pricing information not available.")
                    return
                nav_btn.clicked.connect(lambda checked, p=self: show_pricing_dialog(p))
            else:
                nav_btn.clicked.connect(lambda checked, t=text: show_nav_page(t))
            nav_row.addWidget(nav_btn)
        layout.addLayout(nav_row)
        layout.addWidget(self.nav_stack)
        self.nav_stack.setVisible(False)
        layout.addStretch(1)
        widget.setLayout(layout)
        return widget

    def create_register_widget(self):
        widget = QWidget()
        layout = QVBoxLayout()
        self.reg_serial = QLineEdit()
        self.reg_serial.setPlaceholderText("Machine Serial ID")
        self.reg_name = QLineEdit()
        self.reg_name.setPlaceholderText("Full Name")
        self.reg_age = QLineEdit()
        self.reg_age.setPlaceholderText("Age")
        self.reg_gender = QLineEdit()
        self.reg_gender.setPlaceholderText("Gender")
        self.reg_address = QLineEdit()
        self.reg_address.setPlaceholderText("Address")
        self.reg_phone = QLineEdit()
        self.reg_phone.setPlaceholderText("Phone Number")
        self.reg_password = QLineEdit()
        self.reg_password.setPlaceholderText("Password")
        self.reg_password.setEchoMode(QLineEdit.Password)
        self.reg_confirm = QLineEdit()
        self.reg_confirm.setPlaceholderText("Confirm Password")
        self.reg_confirm.setEchoMode(QLineEdit.Password)
        register_btn = QPushButton("Sign Up")
        register_btn.setObjectName("SignUpBtn")
        register_btn.clicked.connect(self.handle_register)
        for w in [self.reg_serial, self.reg_name, self.reg_age, self.reg_gender, self.reg_address, self.reg_phone, self.reg_password, self.reg_confirm]:
            w.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        # Apply dashboard color coding
        for w in [self.reg_serial, self.reg_name, self.reg_age, self.reg_gender, self.reg_address, self.reg_phone, self.reg_password, self.reg_confirm]:
            w.setStyleSheet("border: 2px solid #ff6600; border-radius: 8px; padding: 6px 10px; font-size: 15px; background: #f7f7f7; color: #222;")
        register_btn.setStyleSheet("background: #ff6600; color: white; border-radius: 10px; padding: 8px 0; font-size: 16px; font-weight: bold;")
        register_btn.setMinimumHeight(36)
        layout.addWidget(self.reg_serial)
        layout.addWidget(self.reg_name)
        layout.addWidget(self.reg_age)
        layout.addWidget(self.reg_gender)
        layout.addWidget(self.reg_address)
        layout.addWidget(self.reg_phone)
        layout.addWidget(self.reg_password)
        layout.addWidget(self.reg_confirm)
        layout.addWidget(register_btn)
        layout.addStretch(1)
        widget.setLayout(layout)
        return widget

    def handle_login(self):
        email_or_phone = self.login_email.text()
        password_or_serial = self.login_password.text()
        if self.sign_in_logic.sign_in_user_allow_serial(email_or_phone, password_or_serial):
            self.result = True
            self.username = email_or_phone
            self.user_details = {}
            self.accept()
        else:
            QMessageBox.warning(self, "Error", "Invalid credentials. Use password or machine serial ID.")

    def handle_phone_login(self):
        phone, ok = QInputDialog.getText(self, "Login with Phone Number", "Enter your phone number:")
        if ok and phone:
            # Here you would implement phone-based authentication logic
            QMessageBox.information(self, "Phone Login", f"Logged in with phone: {phone} (Demo)")
            self.result = True
            self.username = phone
            self.user_details = {'contact': phone}
            self.accept()

    def handle_register(self):
        serial_id = self.reg_serial.text()
        name = self.reg_name.text()
        age = self.reg_age.text()
        gender = self.reg_gender.text()
        address = self.reg_address.text()
        phone = self.reg_phone.text()
        password = self.reg_password.text()
        confirm = self.reg_confirm.text()
        if not all([serial_id, name, age, gender, address, phone, password, confirm]):
            QMessageBox.warning(self, "Error", "All fields are required, including Machine Serial ID.")
            return
        if password != confirm:
            QMessageBox.warning(self, "Error", "Passwords do not match.")
            return
        # Use phone as username for registration, enforce uniqueness on serial/fullname/phone
        ok, msg = self.sign_in_logic.register_user_with_details(
            username=phone,
            password=password,
            full_name=name,
            phone=phone,
            serial_id=serial_id,
            email="",
            extra={"age": age, "gender": gender, "address": address}
        )
        if not ok:
            QMessageBox.warning(self, "Error", msg)
            return
        QMessageBox.information(self, "Success", "Registration successful! You can now sign in.")
        self.stacked.setCurrentIndex(0)

    def _show_nav_window(self, NavClass, text):
        nav_win = NavClass()
        nav_win.setWindowTitle(text)
        nav_win.setMinimumSize(400, 300)
        nav_win.show()
        if not hasattr(self, '_nav_windows'):
            self._nav_windows = []
        self._nav_windows.append(nav_win)


def plot_ecg_with_peaks(ax, ecg_signal, sampling_rate=500, arrhythmia_result=None, r_peaks=None, use_pan_tompkins=False):
    import numpy as np
    from scipy.signal import find_peaks
    # Use only the last 500 samples for live effect (1 second at 500Hz)
    window_size = 500
    if len(ecg_signal) > window_size:
        ecg_signal = ecg_signal[-window_size:]
    # --- Insert artificial gap (isoelectric line) between cycles for visualization ---
    # Detect R peaks to find cycles
    if use_pan_tompkins:
        r_peaks = pan_tompkins(ecg_signal, fs=sampling_rate)
    else:
        r_peaks, _ = find_peaks(ecg_signal, distance=int(0.2 * sampling_rate), prominence=0.6 * np.std(ecg_signal))
    gap_length = int(0.08 * sampling_rate)  # 80 ms gap (40 samples at 500Hz)
    ecg_with_gaps = []
    last_idx = 0
    for i, r in enumerate(r_peaks):
        # Add segment up to this R peak
        if i == 0:
            ecg_with_gaps.extend(ecg_signal[:r+1])
        else:
            ecg_with_gaps.extend(ecg_signal[last_idx+1:r+1])
        # Add gap after each cycle except last
        if i < len(r_peaks) - 1:
            baseline = int(np.mean(ecg_signal))
            ecg_with_gaps.extend([baseline] * gap_length)
        last_idx = r
    # Add the rest of the signal after last R
    if len(r_peaks) > 0 and last_idx+1 < len(ecg_signal):
        ecg_with_gaps.extend(ecg_signal[last_idx+1:])
    elif len(r_peaks) == 0:
        ecg_with_gaps = list(ecg_signal)
    ecg_signal = np.array(ecg_with_gaps)
    x = np.arange(len(ecg_signal))
    ax.clear()
    ax.plot(x, ecg_signal, color='#ff3380', lw=2)  # Pink line for ECG

    # --- Heart rate, PR, QRS, QTc, QRS axis, ST segment calculation ---
    heart_rate = None
    pr_interval = None
    qrs_duration = None
    qt_interval = None
    qtc_interval = None
    qrs_axis = '--'
    st_segment = '--'
    if len(r_peaks) > 1:
        rr_intervals = np.diff(r_peaks) / sampling_rate  # in seconds
        mean_rr = np.mean(rr_intervals)
        if mean_rr > 0:
            heart_rate = 60 / mean_rr
    # Optionally calculate intervals (not shown on plot)
    if len(r_peaks) > 0:
        pr_interval = '--'
        qrs_duration = '--'
        qt_interval = '--'
        qtc_interval = '--'
    # --- End metrics ---
    # --- Display metrics and clinical info on the plot ---
    info_lines = [
        f"PR Interval: {pr_interval if pr_interval else '--'}",
        f"QRS Duration: {qrs_duration if qrs_duration else '--'}",
        f"QTc Interval: {qtc_interval if qtc_interval else '--'}",
        f"QRS Axis: {qrs_axis}",
        f"ST Segment: {st_segment}",
        f"Heart Rate: {heart_rate} bpm" if heart_rate else "Heart Rate: --"
    ]
    # Modern, clean info box
    y0 = np.min(ecg_signal) + 0.05 * (np.max(ecg_signal) - np.min(ecg_signal))
    ax.text(0.99, 0.01, '\n'.join(info_lines), color='#222', fontsize=12, fontweight='bold', ha='right', va='bottom', zorder=20,
            bbox=dict(facecolor='#f7f7f7', edgecolor='#ff3380', alpha=0.95, boxstyle='round,pad=0.4'), transform=ax.transAxes)
    # --- End display ---
    # No legend, no grid, no ticks for a clean look
    ax.set_facecolor('white')
    ax.figure.patch.set_facecolor('white')
    ax.set_xticks([])
    ax.set_yticks([])
    ax.grid(False)


@log_function_call
def main():
    """Main application entry point with proper error handling"""
    try:
        # Initialize crash logger first
        crash_logger = get_crash_logger()
        crash_logger.log_info("Application starting", "APP_START")
        
        logger.info("Starting ECG Monitor Application")
        
        app = QApplication(sys.argv)
        app.setApplicationName("ECG Monitor")
        app.setApplicationVersion("1.3")    
        
        # Show splash screen
        splash = SplashScreen()
        splash.show()
        app.processEvents()
        
        # Initialize login dialog
        login = LoginRegisterDialog()
        splash.finish(login)
        
        # Main application loop
        while True:
            try:
                if login.exec_() == QDialog.Accepted and login.result:
                    logger.info(f"User {login.username} logged in successfully")
                    # Attach machine serial ID to crash logger for email subject/body tagging
                    try:
                        users = load_users()
                        record = None
                        if isinstance(users, dict) and login.username in users:
                            record = users.get(login.username)
                        else:
                            # Fallback: search by phone/contact stored under 'phone'
                            for uname, rec in (users or {}).items():
                                try:
                                    if str(rec.get('phone', '')) == str(login.username):
                                        record = rec
                                        break
                                except Exception:
                                    continue
                        serial_id = ''
                        if isinstance(record, dict):
                            serial_id = str(record.get('serial_id', ''))
                        if serial_id:
                            crash_logger.set_machine_serial_id(serial_id)
                            os.environ['MACHINE_SERIAL_ID'] = serial_id
                            logger.info(f"Machine serial ID set for crash reporting: {serial_id}")
                    except Exception as e:
                        logger.warning(f"Could not set machine serial ID for crash reporting: {e}")
                    
                    # Create and show dashboard
                    dashboard = Dashboard(username=login.username, role=None)
                    # Attach a session recorder for this user
                    try:
                        user_record = None
                        users = load_users()
                        if isinstance(users, dict) and login.username in users:
                            user_record = users.get(login.username)
                        else:
                            for uname, rec in (users or {}).items():
                                try:
                                    if str(rec.get('phone', '')) == str(login.username):
                                        user_record = rec
                                        break
                                except Exception:
                                    continue
                        dashboard._session_recorder = SessionRecorder(username=login.username, user_record=user_record or {})
                    except Exception as e:
                        logger.warning(f"Session recorder init failed: {e}")
                    dashboard.show()
                    
                    # Run application
                    app.exec_()
                    
                    logger.info(f"User {login.username} logged out")
                    
                    # After dashboard closes (sign out), show login again
                    login = LoginRegisterDialog()
                else:
                    logger.info("Application closed by user")
                    break
                    
            except Exception as e:
                logger.error(f"Error in main application loop: {e}")
                QMessageBox.critical(None, "Application Error", 
                                    f"An error occurred: {e}\nThe application will continue.")
                # Continue with new login dialog
                login = LoginRegisterDialog()
                
    except Exception as e:
        logger.critical(f"Fatal error in main application: {e}")
        crash_logger.log_crash(f"Fatal application error: {str(e)}", e, "MAIN_APPLICATION")
        QMessageBox.critical(None, "Fatal Error", 
                           f"A fatal error occurred: {e}\nThe application will exit.")
        sys.exit(1)


if __name__ == "__main__":
    main()