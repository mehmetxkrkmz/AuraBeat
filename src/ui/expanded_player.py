import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFrame, QSlider, QGraphicsDropShadowEffect, QListWidget, QListWidgetItem, QFileDialog, QStackedWidget
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QPropertyAnimation, QUrl
from PyQt6.QtGui import QIcon, QCursor, QColor
from PyQt6.QtMultimedia import QMediaPlayer

from src.ui.player import WaveformWidget, LiveVisualizerWidget
from src.utils.icons import create_svg_icon, create_svg_pixmap, SVG_PLAY, SVG_PAUSE, SVG_SKIP_NEXT, SVG_SKIP_PREVIOUS, SVG_SHUFFLE, SVG_REPEAT, SVG_FOLDER, SVG_MUSIC, SVG_VOLUME

class BackgroundGradientWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_ambient_color = QColor(13, 17, 23)
        self.current_secondary_color = QColor(48, 54, 61)

    def paintEvent(self, event):
        from PyQt6.QtGui import QPainter, QRadialGradient, QBrush, QColor
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        w = self.width()
        h = self.height()
        
        grad = QRadialGradient(w * 0.3, h * 0.3, max(w, h) * 0.8)
        
        c1 = QColor(self.current_ambient_color)
        c2 = QColor(self.current_secondary_color)
        
        c1.setAlpha(180)
        c2.setAlpha(120)
        
        grad.setColorAt(0, c1)
        grad.setColorAt(1, c2)
        
        painter.fillRect(0, 0, w, h, QBrush(grad))

class ExpandedPlayerWidget(QWidget):
    collapse_requested = pyqtSignal()

    def __init__(self, mini_player, parent=None):
        super().__init__(parent)
        self.mini_player = mini_player
        self.setObjectName("ExpandedPlayer")
        self.setStyleSheet("QWidget#ExpandedPlayer { border-radius: 12px; }")
        
        self.target_parallax_x = 0
        self.target_parallax_y = 0
        self.setup_ui()
        self.sync_with_mini_player()

    def setup_ui(self):
        from PyQt6.QtWidgets import QListWidget, QListWidgetItem
        from PyQt6.QtCore import QSize
        from src.utils.icons import create_svg_icon, create_svg_pixmap, SVG_PLAY, SVG_FOLDER, SVG_MUSIC, SVG_VOLUME
        
        # Immersive Ambient Background (Gaussian Blur)
        self.bg_label = QLabel(self)
        self.bg_label.setScaledContents(True)
        self.bg_label.setStyleSheet("background-color: #0d1117;")
        # The custom gradient widget behind everything
        self.gradient_widget = BackgroundGradientWidget(self)
        self.gradient_widget.lower()
        
        # Particle Engine Widget
        from src.ui.particles import ParticleEngineWidget
        self.particle_engine = ParticleEngineWidget(self)
        self.particle_engine.lower()
        
        # Blurred Cover Background (Behind everything, but above gradient)
        self.bg_label = QLabel(self)
        self.bg_label.setScaledContents(True)
        
        # Overlay to darken the blurred background
        self.dark_overlay = QWidget(self)
        self.dark_overlay.setStyleSheet("background-color: rgba(1, 4, 9, 0.4);")
        
        # Audio-Reactive Effects Timer
        from PyQt6.QtCore import QTimer
        self.effect_timer = QTimer(self)
        self.effect_timer.setInterval(16) # ~60fps
        self.effect_timer.timeout.connect(self._update_reactive_effects)
        self.effect_timer.start()
        
        # Enable mouse tracking for 3D Parallax
        self.setMouseTracking(True)
        self.parallax_x = 0
        self.parallax_y = 0
        
        self.setup_layout()

    def _update_reactive_effects(self):
        import random
        if not hasattr(self, 'circular_visualizer') or not hasattr(self, 'bg_label'):
            return
            
        bass = getattr(self.circular_visualizer, 'bass_pulse', 0.0)
        is_playing = getattr(self.circular_visualizer, 'is_playing', False)
        
        self.particle_engine.is_playing = is_playing
        self.particle_engine.set_bass(bass)
        
        # Apply Parallax Offset smoothly
        if hasattr(self, 'circular_visualizer'):
            # Lerp towards target parallax
            self.parallax_x += (self.target_parallax_x - self.parallax_x) * 0.1
            self.parallax_y += (self.target_parallax_y - self.parallax_y) * 0.1
            self.circular_visualizer.set_parallax_offset(self.parallax_x, self.parallax_y)
            self.bg_label.move(int(self.parallax_x * 0.5), int(self.parallax_y * 0.5))
        
        if is_playing and bass > 0.7:
            # Shake effect proportional to bass
            shake_amt = int((bass - 0.7) * 20.0)
            dx = random.randint(-shake_amt, shake_amt) + int(self.parallax_x * 0.5)
            dy = random.randint(-shake_amt, shake_amt) + int(self.parallax_y * 0.5)
            self.bg_label.setGeometry(dx, dy, self.width() + 100, self.height() + 100)
        else:
            self.bg_label.setGeometry(int(self.parallax_x * 0.5), int(self.parallax_y * 0.5), self.width() + 100, self.height() + 100)

    def resizeEvent(self, event):
        self.bg_label.setGeometry(0, 0, self.width() + 100, self.height() + 100)
        self.dark_overlay.setGeometry(0, 0, self.width(), self.height())
        if hasattr(self, 'particle_engine'):
            self.particle_engine.setGeometry(0, 0, self.width(), self.height())
        super().resizeEvent(event)
        
    def mouseMoveEvent(self, event):
        center_x = self.width() / 2
        center_y = self.height() / 2
        offset_x = (event.pos().x() - center_x) / center_x
        offset_y = (event.pos().y() - center_y) / center_y
        
        self.target_parallax_x = offset_x * -30  # Max 30px shift
        self.target_parallax_y = offset_y * -30
        super().mouseMoveEvent(event)

    def setup_layout(self):
        outer_layout = QHBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        # LEFT SIDE: Player Area
        player_container = QWidget()
        player_container.setStyleSheet("background-color: transparent;")
        main_layout = QVBoxLayout(player_container)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(25)

        # 1. Top Bar (Collapse Button)
        top_layout = QHBoxLayout()
        self.collapse_btn = QPushButton()
        from src.utils.icons import create_svg_icon
        # Using SVG_DOWNLOAD or similar as a placeholder, actually let's draw an arrow or use a text button
        self.collapse_btn.setText("🡇 Küçült")
        self.collapse_btn.setStyleSheet("""
            QPushButton { 
                background-color: transparent; 
                color: #8b949e; 
                font-size: 14px; 
                font-weight: bold; 
                border: none;
            }
            QPushButton:hover { color: #ffffff; }
        """)
        self.collapse_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.collapse_btn.clicked.connect(self.collapse_requested.emit)
        
        top_layout.addWidget(self.collapse_btn)
        top_layout.addStretch()
        
        self.theme_btn = QPushButton("Tema: Otomatik (Kapak)")
        self.theme_btn.setStyleSheet("""
            QPushButton { 
                background-color: rgba(255, 255, 255, 0.1); 
                color: #c9d1d9; 
                border-radius: 12px;
                padding: 6px 12px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: rgba(255, 255, 255, 0.2); color: #ffffff; }
        """)
        self.theme_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.theme_btn.clicked.connect(self.cycle_theme)
        
        self.sleep_btn = QPushButton("Uyku: Kapalı")
        self.sleep_btn.setStyleSheet(self.theme_btn.styleSheet())
        self.sleep_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.sleep_btn.clicked.connect(self.cycle_sleep_timer)
        
        top_layout.addWidget(self.sleep_btn)
        top_layout.addWidget(self.theme_btn)
        
        main_layout.addLayout(top_layout)

        # 2. Ultra Premium Circular Visualizer
        from src.ui.circular_visualizer import CircularVisualizerWidget
        self.circular_visualizer = CircularVisualizerWidget()
        self.circular_visualizer.setMinimumSize(400, 400)
        
        cover_layout = QHBoxLayout()
        cover_layout.addStretch()
        cover_layout.addWidget(self.circular_visualizer)
        cover_layout.addStretch()
        main_layout.addLayout(cover_layout)

        # 3. Title & Subtitle
        self.title_label = QLabel("Şarkı Adı")
        self.title_label.setStyleSheet("color: #ffffff; font-size: 26px; font-weight: 900; background: transparent;")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.subtitle_label = QLabel("Sanatçı / Medya")
        self.subtitle_label.setStyleSheet("color: #8b949e; font-size: 18px; background: transparent;")
        self.subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        main_layout.addWidget(self.title_label)
        main_layout.addWidget(self.subtitle_label)
        main_layout.addSpacing(10)

        # Waveform removed based on user request to focus on Circular Visualizer

        # 5. Timeline & Time
        time_layout = QHBoxLayout()
        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setStyleSheet("color: #c9d1d9; font-family: monospace; font-size: 14px; background: transparent;")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        from PyQt6.QtWidgets import QSlider
        self.seek_slider = QSlider(Qt.Orientation.Horizontal)
        self.seek_slider.setRange(0, 1000)
        self.seek_slider.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.seek_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border-radius: 4px;
                height: 8px;
                background: rgba(255, 255, 255, 0.1);
            }
            QSlider::handle:horizontal {
                background: #a371f7;
                width: 16px;
                height: 16px;
                margin: -4px 0;
                border-radius: 8px;
            }
            QSlider::sub-page:horizontal {
                background: #a371f7;
                border-radius: 4px;
            }
        """)
        # Temporarily disconnect during programmatic updates
        self.seek_slider.sliderMoved.connect(self.on_seek_slider_moved)

        time_layout.addWidget(self.time_label)
        time_layout.addWidget(self.seek_slider, 1) # stretch factor 1
        main_layout.addLayout(time_layout)
        main_layout.addSpacing(10)

        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(25)
        controls_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        from src.utils.icons import SVG_SHUFFLE, SVG_REPEAT, SVG_SKIP_PREVIOUS, SVG_SKIP_NEXT
        
        # Helper to create buttons
        def make_btn(svg, size, icon_size):
            b = QPushButton()
            b.setIcon(create_svg_icon(svg, color="#ffffff", size=icon_size))
            b.setIconSize(QSize(icon_size, icon_size))
            b.setFixedSize(size, size)
            b.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            b.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    border-radius: %dpx;
                }
                QPushButton:hover {
                    background-color: rgba(255, 255, 255, 0.1);
                }
                QPushButton:pressed {
                    background-color: rgba(255, 255, 255, 0.2);
                }
            """ % (size // 2))
            return b

        self.shuffle_btn = make_btn(SVG_SHUFFLE, 40, 20)
        self.prev_btn = make_btn(SVG_SKIP_PREVIOUS, 50, 28)
        
        # Big Play Button
        self.play_btn = make_btn(SVG_PLAY, 70, 36)
        self.play_btn.setStyleSheet("""
            QPushButton {
                background-color: #a371f7;
                border-radius: 35px;
            }
            QPushButton:hover {
                background-color: #b58ef8;
            }
            QPushButton:pressed {
                background-color: #8c5ee6;
            }
        """)

        self.next_btn = make_btn(SVG_SKIP_NEXT, 50, 28)
        self.repeat_btn = make_btn(SVG_REPEAT, 40, 20)
        
        self.speed_btn = QPushButton("1.0x")
        self.speed_btn.setFixedSize(50, 40)
        self.speed_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.speed_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #ffffff;
                font-weight: bold;
                border-radius: 20px;
            }
            QPushButton:hover { background-color: rgba(255, 255, 255, 0.1); }
        """)
        self.speed_btn.clicked.connect(self.cycle_speed)

        controls_layout.addWidget(self.shuffle_btn)
        controls_layout.addWidget(self.prev_btn)
        controls_layout.addWidget(self.play_btn)
        controls_layout.addWidget(self.next_btn)
        controls_layout.addWidget(self.repeat_btn)
        controls_layout.addWidget(self.speed_btn)
        
        # Connect buttons
        self.play_btn.clicked.connect(self.mini_player.toggle_playback)
        self.next_btn.clicked.connect(self.play_next)
        self.prev_btn.clicked.connect(self.play_prev)
        self.shuffle_btn.clicked.connect(self.toggle_shuffle)
        self.repeat_btn.clicked.connect(self.toggle_repeat)
        
        main_layout.addLayout(controls_layout)

        # Volume
        vol_layout = QHBoxLayout()
        vol_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vol_icon = QLabel()
        vol_icon.setPixmap(create_svg_pixmap(SVG_VOLUME, color="#8b949e", size=24))
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setFixedWidth(150)
        self.volume_slider.setStyleSheet("""
            QSlider::groove:horizontal { border-radius: 3px; height: 6px; background: #30363d; }
            QSlider::handle:horizontal { background: #a371f7; width: 16px; height: 16px; margin: -5px 0; border-radius: 8px; }
            QSlider::sub-page:horizontal { background: #58a6ff; border-radius: 3px; }
        """)
        self.volume_slider.valueChanged.connect(lambda v: self.mini_player.audio_output.setVolume(v / 100))
        
        vol_layout.addStretch()
        vol_layout.addWidget(vol_icon)
        vol_layout.addSpacing(10)
        vol_layout.addWidget(self.volume_slider)
        vol_layout.addStretch()
        main_layout.addLayout(vol_layout)

        outer_layout.addWidget(player_container, stretch=3)

        # RIGHT SIDE STACK (Playlist with Glassmorphism)
        playlist_container = QWidget()
        playlist_container.setStyleSheet("""
            background-color: rgba(255, 255, 255, 0.03); 
            border-left: 1px solid rgba(255, 255, 255, 0.1); 
            border-top: 1px solid rgba(255, 255, 255, 0.05);
            border-top-right-radius: 12px; 
            border-bottom-right-radius: 12px;
        """)

        playlist_layout = QVBoxLayout(playlist_container)
        playlist_layout.setContentsMargins(20, 30, 20, 20)

        playlist_header = QHBoxLayout()
        lib_icon = QLabel()
        lib_icon.setPixmap(create_svg_pixmap(SVG_MUSIC, color="#ffffff", size=20))
        lib_label = QLabel("Kütüphane")
        lib_label.setStyleSheet("color: #ffffff; font-size: 18px; font-weight: bold; border: none;")

        self.folder_btn = QPushButton()
        self.folder_btn.setIcon(create_svg_icon(SVG_FOLDER, color="#c9d1d9", size=16))
        self.folder_btn.setIconSize(QSize(16, 16))
        self.folder_btn.setFixedSize(32, 32)
        self.folder_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.folder_btn.setStyleSheet("""
            QPushButton { background-color: #21262d; border: 1px solid #30363d; border-radius: 16px; }
            QPushButton:hover { background-color: #30363d; border-color: #58a6ff; }
        """)
        self.folder_btn.clicked.connect(self.choose_playlist_folder)

        playlist_header.addWidget(lib_icon)
        playlist_header.addWidget(lib_label)
        playlist_header.addStretch()
        playlist_header.addWidget(self.folder_btn)
        playlist_layout.addLayout(playlist_header)

        self.playlist_widget = QListWidget()
        self.playlist_widget.setStyleSheet("""
            QListWidget { background: transparent; border: none; outline: none; }
            QListWidget::item { color: #c9d1d9; padding: 12px; border-bottom: 1px solid #21262d; border-radius: 8px; }
            QListWidget::item:hover { background-color: #161b22; }
            QListWidget::item:selected { background-color: rgba(88, 166, 255, 0.15); color: #58a6ff; border: 1px solid #58a6ff; }
        """)
        self.playlist_widget.itemDoubleClicked.connect(self.play_selected_item)
        playlist_layout.addWidget(self.playlist_widget)
        
        outer_layout.addWidget(playlist_container, stretch=1)

        self.current_playlist_folder = ""
        from src.utils.config import config
        self.load_playlist(config.get("download_path"))

    def choose_playlist_folder(self):
        from PyQt6.QtWidgets import QFileDialog
        folder = QFileDialog.getExistingDirectory(self, "Kütüphane Klasörü Seç", self.current_playlist_folder)
        if folder:
            self.load_playlist(folder)

    def load_playlist(self, folder_path):
        self.current_playlist_folder = folder_path
        self.playlist_widget.clear()
        if not folder_path or not os.path.exists(folder_path):
            return
            
        supported = ('.mp3', '.m4a', '.mp4', '.wav', '.flac')
        for f in os.listdir(folder_path):
            if f.lower().endswith(supported):
                item = self.playlist_widget.addItem(f)
                # Store full path in item's data
                last_item = self.playlist_widget.item(self.playlist_widget.count() - 1)
                last_item.setData(Qt.ItemDataRole.UserRole, os.path.join(folder_path, f))

    def play_selected_item(self, item):
        file_path = item.data(Qt.ItemDataRole.UserRole)
        title = item.text()
        self.mini_player.load_media(file_path, title)
        # Select it in the UI list if not selected
        self.playlist_widget.setCurrentItem(item)

    def play_next(self):
        count = self.playlist_widget.count()
        if count == 0:
            return
            
        current_row = self.playlist_widget.currentRow()
        
        import random
        if getattr(self, 'is_shuffle', False):
            next_row = random.randint(0, count - 1)
        else:
            next_row = (current_row + 1) % count if current_row >= 0 else 0
            
        item = self.playlist_widget.item(next_row)
        if item:
            self.play_selected_item(item)

    def play_prev(self):
        count = self.playlist_widget.count()
        if count == 0:
            return
            
        current_row = self.playlist_widget.currentRow()
        prev_row = (current_row - 1) % count if current_row >= 0 else 0
        item = self.playlist_widget.item(prev_row)
        if item:
            self.play_selected_item(item)

    def toggle_shuffle(self):
        self.is_shuffle = not getattr(self, 'is_shuffle', False)
        if self.is_shuffle:
            self.shuffle_btn.setStyleSheet(self.shuffle_btn.styleSheet().replace("background-color: transparent;", "background-color: rgba(88, 166, 255, 0.3); border: 1px solid #58a6ff;"))
        else:
            self.shuffle_btn.setStyleSheet(self.shuffle_btn.styleSheet().replace("background-color: rgba(88, 166, 255, 0.3); border: 1px solid #58a6ff;", "background-color: transparent;"))

    def toggle_repeat(self):
        self.is_repeat = not getattr(self, 'is_repeat', False)
        if self.is_repeat:
            self.repeat_btn.setStyleSheet(self.repeat_btn.styleSheet().replace("background-color: transparent;", "background-color: rgba(88, 166, 255, 0.3); border: 1px solid #58a6ff;"))
        else:
            self.repeat_btn.setStyleSheet(self.repeat_btn.styleSheet().replace("background-color: rgba(88, 166, 255, 0.3); border: 1px solid #58a6ff;", "background-color: transparent;"))

    def sync_with_mini_player(self):
        # Initial State
        self.title_label.setText(self.mini_player.title_label.text())
        self.subtitle_label.setText(self.mini_player.subtitle_label.text())
        self.time_label.setText(self.mini_player.time_label.text())
        
        # Cover
        if hasattr(self.mini_player, 'high_res_cover') and self.mini_player.high_res_cover and not self.mini_player.high_res_cover.isNull():
            self.circular_visualizer.set_album_art(self.mini_player.high_res_cover)
        else:
            self.circular_visualizer.set_album_art(None)
        
        # Playback State
        self.circular_visualizer.set_peaks(self.mini_player.waveform.peaks)
        self.circular_visualizer.set_progress(self.mini_player.waveform.progress)
        self.volume_slider.setValue(self.mini_player.volume_slider.value())
        
        state = self.mini_player.player.playbackState()
        self.on_playback_state_changed(state)

        # Connect Dynamic Updates
        self.mini_player.player.positionChanged.connect(self.on_position_changed)
        self.mini_player.player.playbackStateChanged.connect(self.on_playback_state_changed)
        self.mini_player.player.mediaStatusChanged.connect(self.on_media_status_changed)
        self.mini_player.player.metaDataChanged.connect(self.on_metadata_changed)
        self.mini_player.media_loaded.connect(self.on_media_loaded)
        self.mini_player.color_ready.connect(self.animate_ambient_color)
        self.mini_player.peaks_ready.connect(self.on_peaks_ready)

    def on_metadata_changed(self):
        from PyQt6.QtMultimedia import QMediaMetaData
        meta = self.mini_player.player.metaData()
        title = meta.stringValue(QMediaMetaData.Key.Title)
        artist = meta.stringValue(QMediaMetaData.Key.ContributingArtist) or meta.stringValue(QMediaMetaData.Key.AlbumArtist)
        
        if title:
            self.title_label.setText(title)
        if artist:
            self.subtitle_label.setText(artist)

    def on_media_status_changed(self, status):
        from PyQt6.QtMultimedia import QMediaPlayer
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            if getattr(self, 'is_repeat', False):
                self.mini_player.player.setPosition(0)
                self.mini_player.player.play()
            else:
                self.play_next()

    def on_peaks_ready(self, peaks):
        self.circular_visualizer.set_peaks(peaks)
        if hasattr(self.mini_player, 'audio_samples'):
            self.circular_visualizer.set_audio_data(self.mini_player.audio_samples, self.mini_player.frame_rate)

    def animate_ambient_color(self, primary_color, secondary_color=None):
        from PyQt6.QtCore import QVariantAnimation, QObject
        from PyQt6.QtGui import QColor
        if not hasattr(self, 'current_ambient_color'):
            self.current_ambient_color = QColor(13, 17, 23)
        if not hasattr(self, 'current_secondary_color'):
            self.current_secondary_color = QColor(48, 54, 61)
            
        if secondary_color is None:
            secondary_color = primary_color.darker(150)
            
        self.anim_p = QVariantAnimation(self)
        self.anim_p.setDuration(1000)
        self.anim_p.setStartValue(self.current_ambient_color)
        self.anim_p.setEndValue(primary_color)
        
        self.anim_s = QVariantAnimation(self)
        self.anim_s.setDuration(1000)
        self.anim_s.setStartValue(self.current_secondary_color)
        self.anim_s.setEndValue(secondary_color)
        
        def update_p(c):
            self.current_ambient_color = c
            if hasattr(self, 'gradient_widget'):
                self.gradient_widget.current_ambient_color = c
                self.gradient_widget.update()
            
        def update_s(c):
            self.current_secondary_color = c
            if hasattr(self, 'gradient_widget'):
                self.gradient_widget.current_secondary_color = c
                self.gradient_widget.update()
            
        self.anim_p.valueChanged.connect(update_p)
        self.anim_s.valueChanged.connect(update_s)
        self.anim_p.start()
        self.anim_s.start()

    def resizeEvent(self, event):
        self.bg_label.setGeometry(0, 0, self.width(), self.height())
        self.dark_overlay.setGeometry(0, 0, self.width(), self.height())
        if hasattr(self, 'gradient_widget'):
            self.gradient_widget.setGeometry(0, 0, self.width(), self.height())
        super().resizeEvent(event)

    # Removed paintEvent from here since we use gradient_widget

    def on_media_loaded(self, file_path, title):
        self.title_label.setText(title)
        self.subtitle_label.setText("Şimdi Çalıyor")
        self.time_label.setText("00:00 / 00:00")
        self.circular_visualizer.set_progress(0.0)
        
        # Cover Update
        if hasattr(self.mini_player, 'high_res_cover') and self.mini_player.high_res_cover and not self.mini_player.high_res_cover.isNull():
            self.circular_visualizer.set_album_art(self.mini_player.high_res_cover)
            
            # Fast blur via downscale and upscale
            small_pix = self.mini_player.high_res_cover.scaled(20, 20, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            blurred_pix = small_pix.scaled(800, 800, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
            
            self.bg_label.setPixmap(blurred_pix)
            self.bg_label.show()
        else:
            self.circular_visualizer.set_album_art(None)
            self.bg_label.hide()


    def on_playback_state_changed(self, state):
        from src.utils.icons import create_svg_icon, SVG_PLAY, SVG_PAUSE
        from PyQt6.QtMultimedia import QMediaPlayer
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.play_btn.setIcon(create_svg_icon(SVG_PAUSE, color="#ffffff", size=36))
            self.circular_visualizer.is_playing = True
        else:
            self.play_btn.setIcon(create_svg_icon(SVG_PLAY, color="#ffffff", size=36))
            self.circular_visualizer.is_playing = False

    def on_position_changed(self, position):
        duration = self.mini_player.player.duration()
        if duration > 0:
            progress = position / duration
            self.circular_visualizer.set_progress(progress)
            self.circular_visualizer.set_position_ms(position)
            
            # Temporarily block signals to avoid infinite loop
            self.seek_slider.blockSignals(True)
            self.seek_slider.setValue(int(progress * 1000))
            self.seek_slider.blockSignals(False)

            pos_sec = position // 1000
            dur_sec = duration // 1000
            self.time_label.setText(f"{pos_sec//60:02d}:{pos_sec%60:02d} / {dur_sec//60:02d}:{dur_sec%60:02d}")

    def on_seek_slider_moved(self, value):
        progress = value / 1000.0
        self.mini_player.seek_to(progress)

    def cycle_theme(self):
        themes = ["Otomatik (Kapak)", "Rainbow", "Ateş (Kırmızı/Sarı)", "Neon (Mavi/Mor)", "Synthwave (80s)", "Lo-Fi (Nostalji)", "Klasik (Mor)"]
        current = self.circular_visualizer.theme
        if current in themes:
            idx = themes.index(current)
            next_theme = themes[(idx + 1) % len(themes)]
        else:
            next_theme = themes[0]
            
        self.circular_visualizer.theme = next_theme
        self.theme_btn.setText(f"Tema: {next_theme}")
        self.circular_visualizer.update()

    def cycle_speed(self):
        speeds = [1.0, 1.25, 1.5, 2.0, 0.5]
        current = getattr(self, 'current_speed', 1.0)
        if current in speeds:
            idx = speeds.index(current)
            next_speed = speeds[(idx + 1) % len(speeds)]
        else:
            next_speed = 1.0
            
        self.current_speed = next_speed
        self.speed_btn.setText(f"{next_speed}x")
        self.mini_player.player.setPlaybackRate(next_speed)

    def cycle_sleep_timer(self):
        timers = [0, 15, 30, 60] # in minutes
        current = getattr(self, 'sleep_timer_mins', 0)
        if current in timers:
            idx = timers.index(current)
            next_timer = timers[(idx + 1) % len(timers)]
        else:
            next_timer = 0
            
        self.sleep_timer_mins = next_timer
        if next_timer == 0:
            self.sleep_btn.setText("Uyku: Kapalı")
            if hasattr(self, 'sleep_timer_obj'):
                self.sleep_timer_obj.stop()
        else:
            self.sleep_btn.setText(f"Uyku: {next_timer}dk")
            from PyQt6.QtCore import QTimer
            if not hasattr(self, 'sleep_timer_obj'):
                self.sleep_timer_obj = QTimer(self)
                self.sleep_timer_obj.timeout.connect(self.execute_sleep)
            self.sleep_timer_obj.start(next_timer * 60 * 1000)
            
    def execute_sleep(self):
        self.mini_player.player.pause()
        self.sleep_timer_obj.stop()
        self.sleep_timer_mins = 0
        self.sleep_btn.setText("Uyku: Kapalı")

    # Allow clicking waveform to seek
    def mousePressEvent(self, event):
        pass # The WaveformWidget already handles its own seeking via parent.
        
    def seek_to(self, progress):
        self.mini_player.seek_to(progress)
