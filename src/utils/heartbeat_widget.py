from PyQt5.QtWidgets import QLabel
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QPropertyAnimation, pyqtProperty
import os

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

class HeartbeatLabel(QLabel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._scale = 1.0
        self._pixmap = QPixmap(get_asset_path("vheart2.png"))
        if not self._pixmap.isNull():
            self.setPixmap(self._pixmap.scaledToWidth(120, Qt.SmoothTransformation))
        self.setAlignment(Qt.AlignHCenter | Qt.AlignBottom)
        self.setStyleSheet("margin-top: 16px; margin-bottom: 0; filter: drop-shadow(0px 0px 12px #ff6600);")
        self.anim = QPropertyAnimation(self, b"scale")
        self.anim.setDuration(700)
        self.anim.setStartValue(1.0)
        self.anim.setKeyValueAt(0.5, 1.18)
        self.anim.setEndValue(1.0)
        self.anim.setLoopCount(-1)
        self.anim.start()

    def getScale(self):
        return self._scale

    def setScale(self, scale):
        self._scale = scale
        if not self._pixmap.isNull():
            size = int(120 * scale)
            self.setPixmap(self._pixmap.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation))

    scale = pyqtProperty(float, fget=getScale, fset=setScale)

def heartbeat_image_widget():
    return HeartbeatLabel()
