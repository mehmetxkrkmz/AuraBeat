from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QPoint, QTimer
from PyQt6.QtGui import QCursor
from PyQt6.QtGui import QGuiApplication

class ClipboardPopupWidget(QWidget):
    download_requested = pyqtSignal(str)

    def __init__(self, url, parent=None):
        super().__init__(parent)
        self.url = url
        
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.setup_ui()
        
        # Determine position (bottom right)
        screen = QGuiApplication.primaryScreen().availableGeometry()
        self.width = 320
        self.height = 120
        self.resize(self.width, self.height)
        
        self.end_pos = QPoint(screen.width() - self.width - 20, screen.height() - self.height - 20)
        self.start_pos = QPoint(self.end_pos.x(), screen.height() + 10)
        
        self.move(self.start_pos)
        
        # Auto-hide timer
        self.hide_timer = QTimer(self)
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self.hide_animation)

    def setup_ui(self):
        container = QWidget(self)
        container.setObjectName("PopupContainer")
        container.setStyleSheet("""
            QWidget#PopupContainer {
                background-color: #161b22;
                border: 2px solid #58a6ff;
                border-radius: 12px;
            }
        """)
        container.setFixedSize(320, 120)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(container)
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Title
        title_lbl = QLabel("🎵 AuraBeat: Müzik Algılandı")
        title_lbl.setStyleSheet("color: #58a6ff; font-weight: bold; font-size: 14px;")
        layout.addWidget(title_lbl)
        
        # URL (Truncated)
        display_url = self.url if len(self.url) < 35 else self.url[:35] + "..."
        url_lbl = QLabel(display_url)
        url_lbl.setStyleSheet("color: #c9d1d9; font-size: 12px;")
        layout.addWidget(url_lbl)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        self.dl_btn = QPushButton("Hemen İndir")
        self.dl_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.dl_btn.setStyleSheet("""
            QPushButton {
                background-color: #238636; color: white;
                font-weight: bold; padding: 6px 12px; border-radius: 6px;
            }
            QPushButton:hover { background-color: #2ea043; }
        """)
        self.dl_btn.clicked.connect(self.on_download_clicked)
        
        self.close_btn = QPushButton("Kapat")
        self.close_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent; color: #8b949e;
                font-weight: bold; padding: 6px 12px; border-radius: 6px;
                border: 1px solid #30363d;
            }
            QPushButton:hover { background-color: #21262d; color: #c9d1d9; }
        """)
        self.close_btn.clicked.connect(self.hide_animation)
        
        btn_layout.addWidget(self.dl_btn)
        btn_layout.addWidget(self.close_btn)
        
        layout.addLayout(btn_layout)

    def show_animation(self):
        self.show()
        self.anim = QPropertyAnimation(self, b"pos")
        self.anim.setDuration(400)
        self.anim.setStartValue(self.start_pos)
        self.anim.setEndValue(self.end_pos)
        self.anim.start()
        
        self.hide_timer.start(6000) # Hide after 6 seconds

    def hide_animation(self):
        self.anim = QPropertyAnimation(self, b"pos")
        self.anim.setDuration(400)
        self.anim.setStartValue(self.pos())
        self.anim.setEndValue(self.start_pos)
        self.anim.finished.connect(self.close)
        self.anim.start()

    def on_download_clicked(self):
        self.hide_timer.stop()
        self.download_requested.emit(self.url)
        self.hide_animation()
