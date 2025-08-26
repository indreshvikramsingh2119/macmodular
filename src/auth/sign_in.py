import os
import json
from PyQt5.QtWidgets import (
    QDialog, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, QMessageBox, QStackedWidget, QWidget, QSizePolicy
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont


def get_asset_path(asset_name):
    """
    Get the absolute path to an asset file in a portable way.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    possible_paths = [
        os.path.join(os.path.dirname(os.path.dirname(script_dir)), "assets"),
        os.path.join(script_dir, "assets"),
        os.path.join(os.path.dirname(script_dir), "assets"),
        os.path.join(script_dir, "..", "assets"),
    ]
    
    for path in possible_paths:
        if os.path.exists(path) and os.path.isdir(path):
            return os.path.join(path, asset_name)
    
    # Fallback
    return os.path.join(script_dir, "..", "assets", asset_name)


USER_DATA_FILE = os.path.join(os.path.dirname(__file__), '../../users.json')


class SignIn:
    def __init__(self):
        self.users = self.load_users()

    def load_users(self):
        if os.path.exists(USER_DATA_FILE):
            with open(USER_DATA_FILE, "r") as f:
                return json.load(f)
        return {}

    def save_users(self):
        with open(USER_DATA_FILE, "w") as f:
            json.dump(self.users, f)

    def sign_in_user(self, username, password):
        if self.validate_credentials(username, password):
            return True
        else:
            return False

    def validate_credentials(self, username, password):
        return self.users.get(username) == password

    def register_user(self, username, password):
        if username in self.users:
            return False  # Username already exists
        self.users[username] = password
        self.save_users()
        return True


class LoginRegisterDialog(QDialog):
    def __init__(self):
        super().__init__()
        
        # Set responsive size policy
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(600, 400)  # Minimum size for usability
        
        self.setWindowTitle("ECG Monitor - Sign In / Sign Up")
        self.setWindowFlags(self.windowFlags() | Qt.WindowMinMaxButtonsHint)
        self.setStyleSheet("""
            QDialog { background: #fff; border-radius: 18px; }
            QLabel { font-size: 15px; color: #222; }
            QLineEdit { border: 2px solid #ff6600; border-radius: 8px; padding: 6px 10px; font-size: 15px; background: #f7f7f7; }
            QPushButton { background: #ff6600; color: white; border-radius: 10px; padding: 8px 0; font-size: 16px; font-weight: bold; }
            QPushButton:hover { background: #ff8800; }
        """)
        self.sign_in_logic = SignIn()
        self.init_ui()
        self.result = False
        self.username = None

    def init_ui(self):
        from PyQt5.QtWidgets import QSizePolicy
        from PyQt5.QtGui import QMovie, QPixmap
        
        main_layout = QHBoxLayout()
        
        # Left: Logo/Image with plasma effect background
        logo_widget = QWidget()
        logo_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        logo_layout = QVBoxLayout()
        logo_layout.setAlignment(Qt.AlignCenter)
        
        # Clean background instead of plasma effect
        bg_label = QLabel()
        bg_label.setFixedSize(260, 260)
        bg_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        bg_label.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                stop:0 #667eea, stop:1 #764ba2);
            border-radius: 130px;
        """)
        
        # ECG image on top of clean background
        logo_label = QLabel()
        logo_path = get_asset_path('ECG1.png')
        if os.path.exists(logo_path):
            logo_pixmap = QPixmap(logo_path).scaled(180, 180, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label.setPixmap(logo_pixmap)
            logo_label.setStyleSheet("background: transparent;")
            logo_label.setAlignment(Qt.AlignCenter)
            logo_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        else:
            logo_label.setText("<b>PulseMonitor</b>")
            logo_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        # Stack background and ECG image
        bg_container = QVBoxLayout()
        bg_container.setAlignment(Qt.AlignCenter)
        bg_container.addWidget(bg_label, alignment=Qt.AlignCenter)
        bg_container.addWidget(logo_label, alignment=Qt.AlignCenter)
        
        logo_layout.addStretch(1)
        logo_layout.addLayout(bg_container)
        logo_layout.addStretch(1)
        logo_widget.setLayout(logo_layout)
        
        # Right: Form
        form_widget = QWidget()
        form_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        form_layout = QVBoxLayout()
        form_layout.setAlignment(Qt.AlignCenter)
        
        self.stacked = QStackedWidget(self)
        self.stacked.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.login_widget = self.create_login_widget()
        self.register_widget = self.create_register_widget()
        self.stacked.addWidget(self.login_widget)
        self.stacked.addWidget(self.register_widget)
        
        btn_layout = QHBoxLayout()
        self.login_tab = QPushButton("Sign In")
        self.signup_tab = QPushButton("Sign Up")
        
        # Make buttons responsive
        for btn in [self.login_tab, self.signup_tab]:
            btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            btn.setMinimumWidth(100)
        
        self.login_tab.clicked.connect(lambda: self.stacked.setCurrentIndex(0))
        self.signup_tab.clicked.connect(lambda: self.stacked.setCurrentIndex(1))
        btn_layout.addWidget(self.login_tab)
        btn_layout.addWidget(self.signup_tab)
        
        title = QLabel("<span style='font-family:cursive;font-size:32px;color:#222;'>PulseMonitor</span>")
        title.setAlignment(Qt.AlignCenter)
        title.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        form_layout.addWidget(title)
        form_layout.addLayout(btn_layout)
        form_layout.addWidget(self.stacked)
        form_widget.setLayout(form_layout)
        
        # Add to main layout (image left, form right) with responsive proportions
        main_layout.addWidget(logo_widget, 2)  # Logo takes 2 parts
        main_layout.addWidget(form_widget, 3)  # Form takes 3 parts (more space)
        self.setLayout(main_layout)

    def create_login_widget(self):
        widget = QWidget()
        layout = QVBoxLayout()
        self.login_username = QLineEdit()
        self.login_username.setPlaceholderText("Username")
        self.login_password = QLineEdit()
        self.login_password.setPlaceholderText("Password")
        self.login_password.setEchoMode(QLineEdit.Password)
        login_btn = QPushButton("Sign In")
        login_btn.clicked.connect(self.handle_login)
        layout.addWidget(self.login_username)
        layout.addWidget(self.login_password)
        layout.addWidget(login_btn)
        widget.setLayout(layout)
        return widget

    def create_register_widget(self):
        widget = QWidget()
        layout = QVBoxLayout()
        self.reg_username = QLineEdit()
        self.reg_username.setPlaceholderText("Username")
        self.reg_password = QLineEdit()
        self.reg_password.setPlaceholderText("Password")
        self.reg_password.setEchoMode(QLineEdit.Password)
        self.reg_confirm = QLineEdit()
        self.reg_confirm.setPlaceholderText("Confirm Password")
        self.reg_confirm.setEchoMode(QLineEdit.Password)
        self.reg_fullname = QLineEdit()
        self.reg_fullname.setPlaceholderText("Full Name")
        self.reg_age = QLineEdit()
        self.reg_age.setPlaceholderText("Age")
        self.reg_gender = QLineEdit()
        self.reg_gender.setPlaceholderText("Gender")
        self.reg_contact = QLineEdit()
        self.reg_contact.setPlaceholderText("Contact Number")
        self.reg_email = QLineEdit()
        self.reg_email.setPlaceholderText("Email Address")
        register_btn = QPushButton("Sign Up")
        register_btn.clicked.connect(self.handle_register)
        for w in [self.reg_username, self.reg_password, self.reg_confirm, self.reg_fullname, self.reg_age, self.reg_gender, self.reg_contact, self.reg_email, register_btn]:
            w.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(self.reg_username)
        layout.addWidget(self.reg_password)
        layout.addWidget(self.reg_confirm)
        layout.addWidget(self.reg_fullname)
        layout.addWidget(self.reg_age)
        layout.addWidget(self.reg_gender)
        layout.addWidget(self.reg_contact)
        layout.addWidget(self.reg_email)
        layout.addWidget(register_btn)
        layout.addStretch(1)
        widget.setLayout(layout)
        return widget

    def handle_login(self):
        username = self.login_username.text()
        password = self.login_password.text()
        if self.sign_in_logic.sign_in_user(username, password):
            self.result = True
            self.username = username
            self.accept()
        else:
            QMessageBox.warning(self, "Error", "Invalid username or password.")

    def handle_register(self):
        username = self.reg_username.text()
        password = self.reg_password.text()
        confirm = self.reg_confirm.text()
        fullname = self.reg_fullname.text()
        age = self.reg_age.text()
        gender = self.reg_gender.text()
        contact = self.reg_contact.text()
        email = self.reg_email.text()
        if not username or not password:
            QMessageBox.warning(self, "Error", "Username and password required.")
            return
        if password != confirm:
            QMessageBox.warning(self, "Error", "Passwords do not match.")
            return
        if not fullname or not age or not gender or not contact or not email:
            QMessageBox.warning(self, "Error", "All details required.")
            return
        if not self.sign_in_logic.register_user(username, password):
            QMessageBox.warning(self, "Error", "Username already exists.")
            return
        QMessageBox.information(self, "Success", "Registration successful! You can now sign in.")
        self.stacked.setCurrentIndex(0)