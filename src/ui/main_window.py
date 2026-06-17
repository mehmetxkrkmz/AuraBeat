import os
import subprocess
import sys
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLineEdit, QPushButton, QComboBox, QProgressBar, 
    QLabel, QFileDialog, QMessageBox, QScrollArea, QFrame,
    QGridLayout, QStatusBar, QSizePolicy, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QCursor, QColor

from src.utils.config import config
from src.threads.worker import DownloadWorker

class DownloadItemWidget(QFrame):
    play_requested = pyqtSignal(str, str) # file_path, title

    def __init__(self, url, fmt, quality, worker, parent=None):
        super().__init__(parent)
        self.worker = worker
        self.final_path = ""
        
        self.setObjectName("DownloadCard")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        
        # Add Drop Shadow for Premium 3D look
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)
        
        layout = QGridLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setVerticalSpacing(12)
        
        # Title
        self.title_label = QLabel(f"{url}")
        self.title_label.setStyleSheet("font-weight: 700; font-size: 15px; color: #e6edf3;")
        self.title_label.setWordWrap(True)
        
        # Format Badge
        self.format_label = QLabel(f" {fmt.upper()} | {quality} ")
        self.format_label.setObjectName("FormatBadge")
        self.format_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.format_label.setFixedHeight(24)

        # Progress
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False) # Clean look, no text inside bar
        self.progress_bar.setFixedHeight(8)
        
        # Status / Speed
        self.status_label = QLabel("Bağlanıyor...")
        self.status_label.setStyleSheet("color: #8b949e; font-size: 13px;")
        
        self.speed_label = QLabel("")
        self.speed_label.setStyleSheet("color: #8b949e; font-size: 13px; font-weight: 600;")
        self.speed_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.percent_label = QLabel("0%")
        self.percent_label.setStyleSheet("color: #58a6ff; font-size: 13px; font-weight: 700;")
        self.percent_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        # Action Buttons
        self.cancel_btn = QPushButton("İptal Et")
        self.cancel_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.cancel_btn.setObjectName("DangerBtn")
        self.cancel_btn.clicked.connect(self.cancel_download)

        self.edit_btn = QPushButton("✏️ Düzenle")
        self.edit_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.edit_btn.setStyleSheet("""
            QPushButton { background-color: rgba(210, 153, 34, 0.15); color: #d29922; border: 1px solid rgba(210, 153, 34, 0.4); border-radius: 6px; font-weight: bold; padding: 5px 12px; }
            QPushButton:hover { background-color: #d29922; color: #ffffff; }
        """)
        self.edit_btn.setVisible(False)
        self.edit_btn.clicked.connect(self.edit_metadata)

        self.listen_btn = QPushButton("🎵 Dinle")
        self.listen_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.listen_btn.setStyleSheet("""
            QPushButton { background-color: rgba(46, 160, 67, 0.15); color: #3fb950; border: 1px solid rgba(46, 160, 67, 0.4); border-radius: 6px; font-weight: bold; padding: 5px 12px; }
            QPushButton:hover { background-color: #2ea043; color: #ffffff; }
        """)
        self.listen_btn.setVisible(False)
        self.listen_btn.clicked.connect(self.request_play)

        self.open_btn = QPushButton("Klasörde Aç")
        self.open_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.open_btn.setObjectName("SuccessBtn")
        self.open_btn.setStyleSheet(self.open_btn.styleSheet() + " padding: 5px 12px;")
        self.open_btn.setVisible(False)
        self.open_btn.clicked.connect(self.open_file)
        
        # Add to layout
        layout.addWidget(self.title_label, 0, 0, 1, 2)
        layout.addWidget(self.format_label, 0, 2, 1, 1, Qt.AlignmentFlag.AlignRight)
        
        # Details row
        details_layout = QHBoxLayout()
        details_layout.addWidget(self.status_label)
        details_layout.addStretch()
        details_layout.addWidget(self.speed_label)
        details_layout.addStretch()
        details_layout.addWidget(self.percent_label)
        layout.addLayout(details_layout, 1, 0, 1, 3)

        layout.addWidget(self.progress_bar, 2, 0, 1, 3)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(self.listen_btn)
        btn_layout.addWidget(self.edit_btn)
        btn_layout.addWidget(self.open_btn)
        btn_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(btn_layout, 3, 0, 1, 3)

        # Connect Worker Signals
        self.worker.progress.connect(self.on_progress)
        self.worker.finished.connect(self.on_finished)

    def on_progress(self, data):
        if data['status'] == 'downloading':
            percent = int(data['percent'])
            self.progress_bar.setValue(percent)
            self.percent_label.setText(f"{percent}%")
            self.speed_label.setText(data['speed'])
            
            fname = data['filename'].split('/')[-1].split('\\')[-1]
            if len(fname) > 55:
                fname = fname[:52] + "..."
            self.title_label.setText(fname)
            self.status_label.setText("İndiriliyor")
            self.status_label.setStyleSheet("color: #58a6ff; font-size: 13px;")

        elif data['status'] == 'finished':
            self.progress_bar.setValue(100)
            self.percent_label.setText("100%")
            self.status_label.setText("İşleniyor (Metadata & Çeviri)...")
            self.status_label.setStyleSheet("color: #d29922; font-size: 13px;")
            self.speed_label.setText("")

    def on_finished(self, success, message, filename):
        if success:
            self.progress_bar.setValue(100)
            self.percent_label.setText("100%")
            self.cancel_btn.setVisible(False)
            
            if filename == "SKIPPED":
                self.status_label.setText("Atlandı (Zaten Mevcut)")
                self.status_label.setStyleSheet("color: #d29922; font-size: 13px; font-weight: bold;")
            else:
                self.status_label.setText("Tamamlandı")
                self.status_label.setStyleSheet("color: #238636; font-size: 13px; font-weight: bold;")
                self.open_btn.setVisible(True)
                if filename and (filename.endswith(".mp3") or filename.endswith(".m4a") or filename.endswith(".mp4")):
                    self.edit_btn.setVisible(True)
                    self.listen_btn.setVisible(True)
                self.final_path = filename
        else:
            self.status_label.setText(f"Hata: {message}")
            self.status_label.setStyleSheet("color: #f85149; font-size: 13px; font-weight: bold;")
            self.cancel_btn.setEnabled(False)

    def cancel_download(self):
        self.worker.cancel()
        self.status_label.setText("İptal Ediliyor...")
        self.status_label.setStyleSheet("color: #f85149; font-size: 13px;")
        self.cancel_btn.setEnabled(False)

    def request_play(self):
        if self.final_path and os.path.exists(self.final_path):
            title = self.title_label.text()
            self.play_requested.emit(self.final_path, title)

    def edit_metadata(self):
        if not self.final_path or not os.path.exists(self.final_path):
            QMessageBox.warning(self, "Hata", "Dosya bulunamadı.")
            return
        from src.ui.metadata_editor import MetadataEditorDialog
        dialog = MetadataEditorDialog(self.final_path, self)
        dialog.exec()

    def open_file(self):
        if not self.final_path or not os.path.exists(self.final_path):
            QMessageBox.warning(self, "Hata", "Dosya bulunamadı. Silinmiş veya taşınmış olabilir.")
            return
            
        file_dir = os.path.dirname(self.final_path)
        if sys.platform == "win32":
            os.startfile(file_dir)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", file_dir])
        else:
            subprocess.Popen(["xdg-open", file_dir])

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AuraBeat")
        self.resize(900, 700)
        self.workers = []
        self.apply_premium_stylesheet()
        self.setup_ui()
        self.setup_global_media_keys()

    def setup_global_media_keys(self):
        try:
            from pynput import keyboard
            
            def on_press(key):
                if key == keyboard.Key.media_play_pause:
                    self.mini_player.toggle_playback()
                elif key == keyboard.Key.media_next:
                    if self.stacked_widget.currentIndex() == 1:
                        self.expanded_player_widget.play_next()
                elif key == keyboard.Key.media_previous:
                    if self.stacked_widget.currentIndex() == 1:
                        self.expanded_player_widget.play_prev()
                        
            self.keyboard_listener = keyboard.Listener(on_press=on_press)
            self.keyboard_listener.start()
        except ImportError:
            print("pynput not installed. Global media keys disabled.")
        except Exception as e:
            print(f"Error setting up global media keys: {e}")

    def setup_tray_icon(self):
        from PyQt6.QtWidgets import QSystemTrayIcon, QMenu
        from PyQt6.QtGui import QIcon
        from PyQt6.QtWidgets import QApplication
        import sys
        import os
        
        self.tray_icon = QSystemTrayIcon(self)
        
        # Try to use an icon, fallback to default window icon
        # We can just draw a temporary pixmap if no icon exists
        from PyQt6.QtGui import QPixmap, QPainter
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setBrush(QColor("#a371f7"))
        painter.drawEllipse(10, 10, 44, 44)
        painter.end()
        
        self.tray_icon.setIcon(QIcon(pixmap))
        
        tray_menu = QMenu()
        show_action = tray_menu.addAction("Aç/Göster")
        show_action.triggered.connect(self.show)
        
        quit_action = tray_menu.addAction("Çıkış Yap")
        quit_action.triggered.connect(QApplication.instance().quit)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
        
        self.tray_icon.activated.connect(self.on_tray_icon_activated)

    def on_tray_icon_activated(self, reason):
        from PyQt6.QtWidgets import QSystemTrayIcon
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            if self.isVisible():
                self.hide()
            else:
                self.show()

    def closeEvent(self, event):
        from PyQt6.QtWidgets import QSystemTrayIcon
        # Minimize to tray instead of quitting
        event.ignore()
        self.hide()
        self.tray_icon.showMessage(
            "AuraBeat Arka Planda",
            "Uygulama arka planda (tepside) çalışmaya devam ediyor.",
            QSystemTrayIcon.MessageIcon.Information,
            2000
        )

    def apply_premium_stylesheet(self):
        # Global Stylesheet for Premium Look
        self.setStyleSheet("""
            QMainWindow { background-color: #0d1117; }
            QLabel { color: #c9d1d9; font-family: 'Segoe UI', Inter, sans-serif; }
            
            /* Input Area */
            QLineEdit {
                background-color: #010409;
                border: 2px solid #30363d;
                border-radius: 20px;
                color: #c9d1d9;
                padding: 10px 18px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #58a6ff;
                background-color: #0d1117;
            }
            
            /* Combo Boxes */
            QComboBox {
                background-color: #161b22;
                border: 1px solid #30363d;
                border-radius: 18px;
                color: #c9d1d9;
                padding: 8px 15px;
                font-weight: bold;
            }
            QComboBox::drop-down { border: none; }
            QComboBox:hover { border: 1px solid #8b949e; }
            QComboBox QAbstractItemView {
                background-color: #21262d;
                border: 1px solid #30363d;
                selection-background-color: #30363d;
                color: #c9d1d9;
                outline: none;
            }
            
            /* Buttons */
            QPushButton {
                background-color: #21262d;
                border: 1px solid #30363d;
                border-radius: 18px;
                color: #c9d1d9;
                padding: 8px 15px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #30363d;
                border: 1px solid #8b949e;
            }
            
            /* Primary Button */
            QPushButton#PrimaryBtn {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #238636, stop:1 #2ea043);
                color: #ffffff;
                border: none;
                border-radius: 18px;
                font-size: 15px;
                font-weight: 800;
            }
            QPushButton#PrimaryBtn:hover {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2ea043, stop:1 #3fb950);
            }
            
            /* Danger Button */
            QPushButton#DangerBtn {
                background-color: transparent;
                color: #f85149;
                border: 1px solid #f85149;
            }
            QPushButton#DangerBtn:hover {
                background-color: #f85149;
                color: white;
            }

            /* Success Button */
            QPushButton#SuccessBtn {
                background-color: transparent;
                color: #58a6ff;
                border: 1px solid #58a6ff;
            }
            QPushButton#SuccessBtn:hover {
                background-color: #58a6ff;
                color: white;
            }
            
            /* Download Item Card */
            QFrame#DownloadCard {
                background-color: #161b22;
                border: 1px solid #21262d;
                border-radius: 12px;
            }
            QFrame#DownloadCard:hover {
                border: 1px solid #30363d;
                background-color: #1c2128;
            }
            
            /* Badges */
            QLabel#FormatBadge {
                background-color: rgba(88, 166, 255, 0.15);
                color: #58a6ff;
                border: 1px solid rgba(88, 166, 255, 0.4);
                border-radius: 6px;
                font-size: 11px;
                font-weight: 800;
                padding: 2px 8px;
            }

            /* Progress Bar */
            QProgressBar {
                border: none;
                border-radius: 4px;
                background-color: #010409;
                height: 8px;
                text-align: center;
                color: transparent;
            }
            QProgressBar::chunk {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1f6feb, stop:1 #58a6ff);
                border-radius: 4px;
            }

            /* Scroll Area */
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            QScrollBar:vertical {
                border: none;
                background: transparent;
                width: 8px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background: #484f58;
                min-height: 30px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background: #8b949e;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
            
            /* Status Bar */
            QStatusBar {
                background-color: #0d1117;
                color: #8b949e;
                border-top: 1px solid #30363d;
            }
        """)

    def setup_ui(self):
        from PyQt6.QtWidgets import QStackedWidget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.stacked_widget = QStackedWidget()

        # --- PAGE 0: MAIN DASHBOARD (TABS) ---
        from PyQt6.QtWidgets import QTabWidget
        self.dashboard_widget = QTabWidget()
        self.dashboard_widget.setStyleSheet("""
            QTabWidget::pane { border: none; }
            QTabBar::tab {
                background: #161b22;
                color: #8b949e;
                padding: 10px 20px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-weight: bold;
                font-size: 14px;
                margin-right: 5px;
            }
            QTabBar::tab:selected {
                background: #238636;
                color: #ffffff;
            }
            QTabBar::tab:hover:!selected {
                background: #21262d;
                color: #c9d1d9;
            }
        """)
        
        self.downloads_tab = QWidget()
        dash_layout = QVBoxLayout(self.downloads_tab)
        dash_layout.setContentsMargins(30, 30, 30, 15)
        dash_layout.setSpacing(20)

        # 0. Header Area
        header_layout = QHBoxLayout()
        title_layout = QVBoxLayout()
        title_layout.setSpacing(5)
        
        app_title = QLabel("AuraBeat")
        app_title.setStyleSheet("font-size: 28px; font-weight: 800; color: #ffffff;")
        
        app_subtitle = QLabel("Evrensel Medya ve İndirme Yöneticisi")
        app_subtitle.setStyleSheet("font-size: 14px; color: #8b949e;")
        
        title_layout.addWidget(app_title)
        title_layout.addWidget(app_subtitle)
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        
        # Clipboard Monitor Toggle
        from PyQt6.QtWidgets import QCheckBox, QApplication
        self.clipboard_toggle = QCheckBox("Akıllı Pano İzleyici")
        self.clipboard_toggle.setChecked(config.get("clipboard_on_startup", False))
        self.clipboard_toggle.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.clipboard_toggle.setStyleSheet("color: #58a6ff; font-weight: bold; font-size: 13px;")
        self.clipboard_toggle.setToolTip("Kopyaladığınız YouTube/Spotify linklerini otomatik yapıştırır.")
        header_layout.addWidget(self.clipboard_toggle, alignment=Qt.AlignmentFlag.AlignBottom)
        
        # Settings Button
        from src.utils.icons import create_svg_icon, SVG_SETTINGS
        from PyQt6.QtCore import QSize
        self.settings_btn = QPushButton(" Ayarlar")
        self.settings_btn.setIcon(create_svg_icon(SVG_SETTINGS, color="#8b949e", size=16))
        self.settings_btn.setIconSize(QSize(16, 16))
        self.settings_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.settings_btn.setStyleSheet("""
            QPushButton { background-color: transparent; color: #8b949e; border: 1px solid #30363d; border-radius: 16px; padding: 6px 12px; font-weight: bold; }
            QPushButton:hover { background-color: #21262d; color: #c9d1d9; }
        """)
        self.settings_btn.clicked.connect(self.open_settings)
        header_layout.addWidget(self.settings_btn, alignment=Qt.AlignmentFlag.AlignBottom)

        # Connect Clipboard
        self.clipboard = QApplication.clipboard()
        from PyQt6.QtGui import QClipboard
        self.clipboard.changed.connect(lambda mode: self.on_clipboard_changed() if mode == QClipboard.Mode.Clipboard else None)
        
        dash_layout.addLayout(header_layout)
        dash_layout.addSpacing(10)

        # 1. Top Bar: URL Input & Controls
        top_layout = QHBoxLayout()
        top_layout.setSpacing(12)
        
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("YouTube, SoundCloud, Spotify URL'si yapıştırın...")
        self.url_input.setMinimumHeight(48)
        
        self.format_combo = QComboBox()
        self.format_combo.addItems(["Audio (MP3)", "Video (MP4)"])
        self.format_combo.setMinimumHeight(48)
        self.format_combo.setMinimumWidth(140)
        self.format_combo.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.format_combo.currentTextChanged.connect(self.update_quality_options)
        
        self.quality_combo = QComboBox()
        self.quality_combo.setMinimumHeight(48)
        self.quality_combo.setMinimumWidth(120)
        self.quality_combo.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.update_quality_options(self.format_combo.currentText())
        
        self.download_btn = QPushButton("Hemen İndir")
        self.download_btn.setObjectName("PrimaryBtn")
        self.download_btn.setMinimumHeight(48)
        self.download_btn.setFixedWidth(140)
        self.download_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.download_btn.clicked.connect(self.start_download)
        
        top_layout.addWidget(self.url_input, stretch=1)
        top_layout.addWidget(self.format_combo)
        top_layout.addWidget(self.quality_combo)
        top_layout.addWidget(self.download_btn)
        
        dash_layout.addLayout(top_layout)

        # 2. Settings Bar: Output Directory
        settings_layout = QHBoxLayout()
        folder_icon_lbl = QLabel("📂")
        folder_icon_lbl.setStyleSheet("font-size: 16px;")
        
        self.dir_label = QLabel(f"Kayıt Klasörü:  {config.get('download_path')}")
        self.dir_label.setStyleSheet("color: #8b949e; font-size: 13px;")
        
        self.change_dir_btn = QPushButton("Değiştir")
        self.change_dir_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.change_dir_btn.setFixedHeight(32)
        self.change_dir_btn.clicked.connect(self.change_directory)
        
        self.open_dir_btn = QPushButton("Klasörü Aç")
        self.open_dir_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.open_dir_btn.setFixedHeight(32)
        self.open_dir_btn.clicked.connect(self.open_directory)
        
        settings_layout.addWidget(folder_icon_lbl)
        settings_layout.addWidget(self.dir_label)
        settings_layout.addStretch()
        settings_layout.addWidget(self.change_dir_btn)
        settings_layout.addWidget(self.open_dir_btn)
        
        dash_layout.addLayout(settings_layout)
        dash_layout.addSpacing(10)

        # 3. Queue Area (Scrollable)
        queue_header = QLabel("İndirme Kuyruğu")
        queue_header.setStyleSheet("font-size: 16px; font-weight: bold; color: #e6edf3;")
        dash_layout.addWidget(queue_header)
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        
        self.queue_widget = QWidget()
        self.queue_widget.setStyleSheet("background: transparent;")
        self.queue_layout = QVBoxLayout(self.queue_widget)
        self.queue_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.queue_layout.setContentsMargins(0, 0, 10, 0)
        self.queue_layout.setSpacing(15)
        
        self.scroll_area.setWidget(self.queue_widget)
        dash_layout.addWidget(self.scroll_area, stretch=1)
        

        # Build Tabs
        self.dashboard_widget.addTab(self.downloads_tab, "İndirmeler")
        
        try:
            from src.ui.yt_music_tab import YTMusicTab
            self.yt_music_tab = YTMusicTab()
            self.yt_music_tab.stream_requested.connect(self.play_ytm_stream)
            self.dashboard_widget.addTab(self.yt_music_tab, "Keşfet (YouTube Music)")
        except Exception as e:
            print("YTMusicTab load error:", e)

        # Add Dashboard to Stacked Widget
        self.stacked_widget.addWidget(self.dashboard_widget)

        # 4. Mini Player
        from src.ui.player import MiniPlayerWidget
        self.mini_player = MiniPlayerWidget()
        
        # --- PAGE 1: EXPANDED PLAYER ---
        from src.ui.expanded_player import ExpandedPlayerWidget
        self.expanded_player_widget = ExpandedPlayerWidget(self.mini_player, self)
        self.expanded_player_widget.collapse_requested.connect(lambda: self.toggle_expanded_view(False))
        self.stacked_widget.addWidget(self.expanded_player_widget)

        # Add everything to main layout
        main_layout.addWidget(self.stacked_widget, stretch=1)
        main_layout.addWidget(self.mini_player)
        
        # Connect expanding logic
        self.mini_player.expand_toggled.connect(self.toggle_expanded_view)

        # 5. Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Sistem Hazır. Bekleniyor...")
        
        import getpass
        username = getpass.getuser()
        sig_label = QLabel(f"Crafted with 🩵 by {username}")
        sig_label.setStyleSheet("color: #484f58; font-size: 11px; font-weight: bold;")
        self.status_bar.addPermanentWidget(sig_label)
        
        # 6. System Tray
        self.setup_tray_icon()

    def toggle_expanded_view(self, is_expanded):
        from PyQt6.QtWidgets import QGraphicsOpacityEffect
        from PyQt6.QtCore import QPropertyAnimation
        
        if is_expanded:
            self.stacked_widget.setCurrentIndex(1)
            self.mini_player.hide()
            
            effect = QGraphicsOpacityEffect(self.expanded_player_widget)
            self.expanded_player_widget.setGraphicsEffect(effect)
            self.anim = QPropertyAnimation(effect, b"opacity")
            self.anim.setDuration(300)
            self.anim.setStartValue(0.0)
            self.anim.setEndValue(1.0)
            self.anim.start()
        else:
            effect = QGraphicsOpacityEffect(self.expanded_player_widget)
            self.expanded_player_widget.setGraphicsEffect(effect)
            self.anim = QPropertyAnimation(effect, b"opacity")
            self.anim.setDuration(250)
            self.anim.setStartValue(1.0)
            self.anim.setEndValue(0.0)
            self.anim.finished.connect(self._finish_collapse)
            self.anim.start()

    def _finish_collapse(self):
        from PyQt6.QtWidgets import QGraphicsOpacityEffect
        from PyQt6.QtCore import QPropertyAnimation
        self.stacked_widget.setCurrentIndex(0)
        self.mini_player.show()
        
        effect = QGraphicsOpacityEffect(self.dashboard_widget)
        self.dashboard_widget.setGraphicsEffect(effect)
        self.anim2 = QPropertyAnimation(effect, b"opacity")
        self.anim2.setDuration(250)
        self.anim2.setStartValue(0.0)
        self.anim2.setEndValue(1.0)
        self.anim2.start()

    def on_clipboard_changed(self):
        if not self.clipboard_toggle.isChecked():
            return
            
        from PyQt6.QtGui import QClipboard
        text = self.clipboard.text(mode=QClipboard.Mode.Clipboard).strip()
        if text.startswith("http://") or text.startswith("https://"):
            valid_domains = ["youtube.com", "youtu.be", "spotify.com", "soundcloud.com"]
            if any(domain in text for domain in valid_domains):
                self.url_input.setText(text)
                self.status_bar.showMessage("Pano izleyici yeni bir medya linki yakaladı!", 3000)
                
                # Show IDM style popup
                try:
                    from src.ui.clipboard_popup import ClipboardPopupWidget
                    # Keep a reference to prevent garbage collection
                    self.clipboard_popup = ClipboardPopupWidget(text)
                    self.clipboard_popup.download_requested.connect(self._popup_download_requested)
                    self.clipboard_popup.show_animation()
                except Exception as e:
                    print(f"Error showing clipboard popup: {e}")

    def _popup_download_requested(self, url):
        self.url_input.setText(url)
        self.start_download()

    def update_quality_options(self, text):
        self.quality_combo.clear()
        if "Audio" in text:
            self.quality_combo.addItems(["320kbps", "256kbps", "192kbps", "128kbps"])
        else:
            self.quality_combo.addItems(["1080p", "720p", "480p", "360p"])

    def change_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "İndirme Klasörü Seç")
        if directory:
            config.set("download_path", directory)
            self.dir_label.setText(f"Kayıt Klasörü:  {directory}")

    def open_directory(self):
        path = config.get('download_path')
        if sys.platform == "win32":
            os.startfile(path)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])

    def start_download(self):
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "Uyarı", "Lütfen geçerli bir URL girin.")
            return

        self.download_btn.setEnabled(False)
        self.status_bar.showMessage("Bağlantı analiz ediliyor...")
        
        # Add a temporary loading label
        self.loading_label = QLabel("Bağlantı analiz ediliyor, lütfen bekleyin...")
        self.loading_label.setStyleSheet("color: #58a6ff; font-weight: bold; padding: 10px;")
        self.queue_layout.addWidget(self.loading_label)

        # Keep a reference to the resolver so it isn't garbage collected
        from src.threads.worker import PlaylistResolverWorker
        self.resolver = PlaylistResolverWorker(url)
        self.resolver.finished.connect(self.on_playlist_resolved)
        self.resolver.start()

    def on_playlist_resolved(self, success, entries, error_msg):
        self.download_btn.setEnabled(True)
        if hasattr(self, 'loading_label') and self.loading_label:
            self.queue_layout.removeWidget(self.loading_label)
            self.loading_label.deleteLater()
            self.loading_label = None
        
        if not success:
            QMessageBox.critical(self, "Hata", f"Bağlantı çözümlenemedi:\n{error_msg}")
            self.status_bar.showMessage("Analiz başarısız.", 3000)
            return

        if not entries:
            QMessageBox.warning(self, "Uyarı", "Bu listede içerik bulunamadı.")
            self.status_bar.showMessage("İçerik bulunamadı.", 3000)
            return

        if len(entries) > 1:
            reply = QMessageBox.question(
                self, "Çalma Listesi Algılandı",
                f"Bu bağlantıda {len(entries)} adet medya bulundu.\nHepsini kuyruğa eklemek istiyor musunuz?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )
            if reply == QMessageBox.StandardButton.No:
                self.status_bar.showMessage("Toplu indirme iptal edildi.", 3000)
                return

        fmt_selection = self.format_combo.currentText()
        fmt = "audio" if "Audio" in fmt_selection else "video"
        quality = self.quality_combo.currentText().replace("kbps", "")
        output_path = config.get("download_path")

        from src.threads.worker import DownloadWorker
        for entry in entries:
            entry_url = entry.get('url') or entry.get('webpage_url')
            if not entry_url:
                continue
                
            if not entry_url.startswith("http"):
                entry_url = f"https://www.youtube.com/watch?v={entry.get('id')}"

            worker = DownloadWorker(entry_url, fmt, quality, output_path)
            worker.has_run = False
            
            item_widget = DownloadItemWidget(entry.get('title') or entry_url, fmt, quality, worker)
            item_widget.play_requested.connect(self.mini_player.load_media)
            self.queue_layout.addWidget(item_widget)

            self.workers.append(worker)
            
            def cleanup_worker(success, msg, fname, w=worker):
                if w in self.workers:
                    self.workers.remove(w)
                self.update_status_bar()
                
                if success and fname and hasattr(self, 'expanded_player_widget'):
                    if fname.endswith(".mp3") or fname.endswith(".m4a") or fname.endswith(".wav"):
                        current_folder = self.expanded_player_widget.current_playlist_folder
                        if current_folder and current_folder == config.get("download_path"):
                            self.expanded_player_widget.load_playlist(current_folder)
                        elif not current_folder:
                            self.expanded_player_widget.load_playlist(config.get("download_path"))
                self.check_queue()

            worker.finished.connect(cleanup_worker)
            
        self.url_input.clear()
        self.check_queue()
        self.update_status_bar()

    def check_queue(self):
        max_concurrent = config.get("max_concurrent_downloads", 3)
        active_count = sum(1 for w in self.workers if w.isRunning())
        
        for w in self.workers:
            if not w.isRunning() and not w.has_run:
                if active_count < max_concurrent:
                    w.has_run = True
                    w.start()
                    active_count += 1
                else:
                    break

    def update_status_bar(self):
        active = sum(1 for w in self.workers if w.isRunning())
        if active > 0:
            self.status_bar.showMessage(f"Devam eden indirme sayısı: {active}")
        else:
            self.status_bar.showMessage("Tüm işlemler tamamlandı. Sistem Hazır.")

    def open_settings(self):
        from src.ui.settings_dialog import SettingsDialog
        dialog = SettingsDialog(self)
        if dialog.exec():
            self.dir_label.setText(f"Kayıt Klasörü:  {config.get('download_path')}")
            if hasattr(self, 'expanded_player_widget'):
                self.expanded_player_widget.load_playlist(config.get('download_path'))

    def play_ytm_stream(self, url, title, cover_url):
        self.status_bar.showMessage("Akış başlatılıyor: " + title)
        from PyQt6.QtCore import QThread, pyqtSignal
        import subprocess

        class StreamResolver(QThread):
            resolved = pyqtSignal(str)
            error = pyqtSignal(str)
            
            def __init__(self, target_url):
                super().__init__()
                self.target_url = target_url
                
            def run(self):
                try:
                    import yt_dlp
                    ydl_opts = {
                        'format': 'bestaudio/best',
                        'quiet': True,
                        'no_warnings': True,
                    }
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(self.target_url, download=False)
                        stream_url = info['url']
                        self.resolved.emit(stream_url)
                except Exception as e:
                    self.error.emit(str(e))

        self.stream_resolver = StreamResolver(url)
        def on_resolved(stream_url):
            self.status_bar.showMessage("Oynatılıyor: " + title, 5000)
            self.mini_player.load_media(stream_url, title)
            # Fetch cover image
            if cover_url:
                self.fetch_ytm_cover(cover_url)

        def on_error(e):
            self.status_bar.showMessage("Akış hatası: " + str(e), 5000)

        self.stream_resolver.resolved.connect(on_resolved)
        self.stream_resolver.error.connect(on_error)
        self.stream_resolver.start()

    def fetch_ytm_cover(self, url):
        from PyQt6.QtCore import QThread, pyqtSignal
        from PyQt6.QtGui import QImage, QPixmap
        import requests

        class CoverFetcher(QThread):
            loaded = pyqtSignal(QPixmap)
            def __init__(self, cover_url):
                super().__init__()
                self.cover_url = cover_url
            def run(self):
                try:
                    resp = requests.get(self.cover_url, timeout=5)
                    if resp.status_code == 200:
                        img = QImage()
                        img.loadFromData(resp.content)
                        if not img.isNull():
                            pixmap = QPixmap.fromImage(img)
                            self.loaded.emit(pixmap)
                except:
                    pass

        self.cover_fetcher = CoverFetcher(url)
        def on_cover_loaded(pixmap):
            self.mini_player.high_res_cover = pixmap
            # If expanded player is visible, update it
            if hasattr(self, 'expanded_player_widget') and self.stacked_widget.currentIndex() == 1:
                self.expanded_player_widget.circular_visualizer.set_album_art(pixmap)
                
                small_pix = pixmap.scaled(20, 20, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                blurred_pix = small_pix.scaled(800, 800, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
                self.expanded_player_widget.bg_label.setPixmap(blurred_pix)

        self.cover_fetcher.loaded.connect(on_cover_loaded)
        self.cover_fetcher.start()
