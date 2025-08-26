from PyQt5.QtWidgets import QSplashScreen, QLabel, QDesktopWidget, QSizePolicy
from PyQt5.QtGui import QPixmap, QFont, QMovie
from PyQt5.QtCore import Qt
import os

class SplashScreen(QSplashScreen):
    def __init__(self):
        super().__init__(QPixmap())
        
        # Set responsive size policy
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(400, 300)  # Minimum size for usability
        
        # Center the splash screen
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
        
        # Animated GIF
        self.label = QLabel(self)
        self.label.setGeometry(0, 0, 520, 320)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Use absolute path to assets/tenor.gif for reliability
        gif_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'tenor.gif')
        gif_path = os.path.abspath(gif_path)
        movie = QMovie(gif_path)
        self.label.setMovie(movie)
        movie.start()
        
        # App Title
        self.title_label = QLabel("Pulse Monitor", self)
        self.title_label.setFont(QFont("Arial", 22, QFont.Bold))
        self.title_label.setStyleSheet("color: #ff6600;")
        self.title_label.setGeometry(0, 320, 520, 60)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        self.setStyleSheet("background: #fff; border-radius: 18px;")