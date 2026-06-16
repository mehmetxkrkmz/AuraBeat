import os
import numpy as np
from pydub import AudioSegment

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFrame
)
from PyQt6.QtCore import Qt, QUrl, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QPainter, QColor, QCursor
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput

class WaveformAnalyzerWorker(QThread):
    finished = pyqtSignal(object) # emit dict with peaks, samples, frame_rate
    error = pyqtSignal(str)

    def __init__(self, file_path, num_bars=100):
        super().__init__()
        self.file_path = file_path
        self.num_bars = num_bars

    def run(self):
        try:
            # Read file using pydub
            audio = AudioSegment.from_file(self.file_path)
            frame_rate = audio.frame_rate
            
            # Convert to mono and get raw data
            audio = audio.set_channels(1)
            samples = np.array(audio.get_array_of_samples())
            
            if len(samples) == 0:
                self.finished.emit({"peaks": [], "samples": None, "frame_rate": 0})
                return

            # Split into chunks and calculate RMS (Root Mean Square) for each chunk
            chunk_size = len(samples) // self.num_bars
            
            # Handle remainder
            if chunk_size == 0:
                self.finished.emit({"peaks": [], "samples": samples, "frame_rate": frame_rate})
                return
                
            peaks = []
            for i in range(self.num_bars):
                start = i * chunk_size
                end = start + chunk_size
                chunk = samples[start:end]
                # Cast to larger int to avoid overflow
                chunk = chunk.astype(np.int64)
                rms = np.sqrt(np.mean(chunk**2))
                peaks.append(rms)

            # Normalize peaks to 0.0 - 1.0
            max_peak = max(peaks)
            if max_peak > 0:
                peaks = [p / max_peak for p in peaks]
            else:
                peaks = [0] * self.num_bars

            # Limit samples to 1 hour to prevent huge memory just in case
            max_len = frame_rate * 60 * 60
            if len(samples) > max_len:
                samples = samples[:max_len]

            self.finished.emit({
                "peaks": peaks, 
                "samples": samples, 
                "frame_rate": frame_rate
            })
        except Exception as e:
            self.error.emit(str(e))


class WaveformWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(40)
        self.peaks = []
        self.progress = 0.0 # 0.0 to 1.0
        self.is_loading = False

    def set_peaks(self, peaks):
        self.peaks = peaks
        self.is_loading = False
        self.update()

    def set_progress(self, progress):
        self.progress = max(0.0, min(1.0, progress))
        self.update()

    def set_loading(self, loading):
        self.is_loading = loading
        self.update()

    def mousePressEvent(self, event):
        if self.peaks and event.button() == Qt.MouseButton.LeftButton:
            pos = event.position().x()
            new_progress = pos / self.width()
            # Send signal back to parent to seek
            self.parent().seek_to(new_progress)

    def paintEvent(self, event):
        from PyQt6.QtGui import QLinearGradient, QColor
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if self.is_loading:
            painter.setPen(QColor("#8b949e"))
            font = painter.font()
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Waveform Analiz Ediliyor...")
            return

        if not self.peaks:
            painter.setPen(QColor("#30363d"))
            painter.drawLine(0, int(self.height()/2), self.width(), int(self.height()/2))
            return

        width = self.width()
        height = self.height()
        
        num_bars = len(self.peaks)
        step = width / num_bars
        actual_bar_width = max(2.0, step - 1.5)
        
        painter.setPen(Qt.PenStyle.NoPen)
        
        played_grad = QLinearGradient(0, 0, width, 0)
        played_grad.setColorAt(0.0, QColor("#a371f7")) 
        played_grad.setColorAt(0.5, QColor("#58a6ff")) 
        played_grad.setColorAt(1.0, QColor("#3fb950")) 
        
        unplayed_color = QColor("#30363d")
        
        for i, peak in enumerate(self.peaks):
            bar_height = max(4, int(peak * height * 0.8)) # Slightly shorter to make room for glow
            x = i * step
            y = (height - bar_height) / 2
            
            bar_progress = i / num_bars
            if bar_progress <= self.progress:
                painter.setBrush(played_grad)
                # Draw standard bar
                painter.drawRoundedRect(int(x), int(y), int(actual_bar_width), int(bar_height), 2, 2)
            else:
                # Unplayed: Draw as a dot sequence instead of tall bars to look more elegant
                painter.setBrush(unplayed_color)
                painter.drawRoundedRect(int(x), int((height - 4)/2), int(actual_bar_width), 4, 2, 2)
            
        # Draw glowing playhead
        playhead_x = int(self.progress * width)
        painter.setBrush(QColor(255, 255, 255, 255))
        painter.drawRoundedRect(playhead_x - 2, int(height * 0.1), 4, int(height * 0.8), 2, 2)
        
        # Playhead Glow
        painter.setBrush(QColor(255, 255, 255, 100))
        painter.drawRoundedRect(playhead_x - 4, int(height * 0.1) - 2, 8, int(height * 0.8) + 4, 4, 4)

class LiveVisualizerWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(24, 24)
        self.is_playing = False
        self.bars = [0.2, 0.4, 0.6, 0.4, 0.2]
        self.target_bars = list(self.bars)
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_bars)
        self.timer.start(30) # 30ms for smooth 30fps animation

    def set_playing(self, playing):
        self.is_playing = playing
        if not playing:
            self.target_bars = [0.1, 0.1, 0.1, 0.1, 0.1]
            
    def update_bars(self):
        import random
        if self.is_playing:
            # Every few frames, pick new targets
            if random.random() < 0.2:
                self.target_bars = [random.uniform(0.2, 1.0) for _ in range(5)]
                
        # Smooth interpolation
        changed = False
        for i in range(5):
            diff = self.target_bars[i] - self.bars[i]
            if abs(diff) > 0.01:
                self.bars[i] += diff * 0.3
                changed = True
                
        if changed or self.is_playing:
            self.update()

    def paintEvent(self, event):
        from PyQt6.QtGui import QLinearGradient, QColor, QPainterPath
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        width = self.width()
        height = self.height()
        
        grad = QLinearGradient(0, height, 0, 0)
        grad.setColorAt(0.0, QColor("#58a6ff"))
        grad.setColorAt(1.0, QColor("#a371f7"))
        
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(grad)
        
        bar_w = width / 5
        for i, val in enumerate(self.bars):
            bh = max(2, int(height * val))
            # Draw pills instead of rectangles
            painter.drawRoundedRect(int(i * bar_w), height - bh, int(bar_w - 1.5), bh, 2, 2)


class MiniPlayerWidget(QFrame):
    expand_toggled = pyqtSignal(bool)
    media_loaded = pyqtSignal(str, str)
    peaks_ready = pyqtSignal(list)
    color_ready = pyqtSignal(QColor, QColor)

    def __init__(self, parent=None):
        from PyQt6.QtWidgets import QGraphicsDropShadowEffect
        from PyQt6.QtGui import QColor
        super().__init__(parent)
        self.setObjectName("MiniPlayer")
        self.setStyleSheet("""
            QFrame#MiniPlayer {
                background-color: #161b22;
                border: 1px solid #30363d;
                border-radius: 12px;
                margin: 10px;
            }
            QLabel { color: #c9d1d9; font-size: 13px; font-weight: 500; }
        """)
        
        # Add Drop Shadow to the Player
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(25)
        shadow.setColor(QColor(0, 0, 0, 100))
        shadow.setOffset(0, 5)
        self.setGraphicsEffect(shadow)
        
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.audio_output.setVolume(0.8)

        self.current_file = None
        self.setup_ui()

        self.player.positionChanged.connect(self.on_position_changed)
        self.player.durationChanged.connect(self.on_duration_changed)
        self.player.metaDataChanged.connect(self.on_metadata_changed)

    def on_metadata_changed(self):
        from PyQt6.QtMultimedia import QMediaMetaData
        meta = self.player.metaData()
        title = meta.stringValue(QMediaMetaData.Key.Title)
        artist = meta.stringValue(QMediaMetaData.Key.ContributingArtist) or meta.stringValue(QMediaMetaData.Key.AlbumArtist)
        
        if title:
            self.title_label.setText(title)
        if artist:
            self.subtitle_label.setText(artist)

    def setup_ui(self):
        from PyQt6.QtWidgets import QSlider
        from PyQt6.QtCore import QSize
        from src.utils.icons import create_svg_icon, create_svg_pixmap, SVG_PLAY, SVG_FOLDER, SVG_EXPAND, SVG_MUSIC, SVG_VOLUME
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(15)

        # Album Art
        self.cover_label = QLabel()
        self.cover_label.setFixedSize(50, 50)
        self.cover_label.setStyleSheet("border-radius: 8px; background-color: #21262d;")
        self.cover_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cover_label.setPixmap(create_svg_pixmap(SVG_MUSIC, color="#8b949e", size=24))

        # Beautiful Circular Play Button
        self.play_btn = QPushButton()
        self.play_btn.setIcon(create_svg_icon(SVG_PLAY, color="#0d1117", size=24))
        self.play_btn.setIconSize(QSize(24, 24))
        self.play_btn.setFixedSize(46, 46)
        self.play_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.play_btn.setStyleSheet("""
            QPushButton {
                background-color: #58a6ff;
                border-radius: 23px;
            }
            QPushButton:hover { background-color: #79c0ff; }
            QPushButton:pressed { background-color: #388bfd; }
        """)
        self.play_btn.clicked.connect(self.toggle_playback)

        # Open Local File Button
        self.open_file_btn = QPushButton()
        self.open_file_btn.setIcon(create_svg_icon(SVG_FOLDER, color="#c9d1d9", size=20))
        self.open_file_btn.setIconSize(QSize(20, 20))
        self.open_file_btn.setFixedSize(36, 36)
        self.open_file_btn.setToolTip("Bilgisayardan Medya Seç")
        self.open_file_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.open_file_btn.setStyleSheet("""
            QPushButton {
                background-color: #21262d;
                border: 1px solid #30363d;
                border-radius: 18px;
            }
            QPushButton:hover { background-color: #30363d; border-color: #8b949e; }
        """)
        self.open_file_btn.clicked.connect(self.browse_media)

        # Expand Button
        self.expand_btn = QPushButton()
        self.expand_btn.setIcon(create_svg_icon(SVG_EXPAND, color="#8b949e", size=20))
        self.expand_btn.setIconSize(QSize(20, 20))
        self.expand_btn.setFixedSize(36, 36)
        self.expand_btn.setToolTip("Tam Ekran Oynatıcı")
        self.expand_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.expand_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 1px solid #30363d;
                border-radius: 18px;
            }
            QPushButton:hover { background-color: #21262d; border-color: #58a6ff; }
        """)
        self.expand_btn.clicked.connect(self.open_expanded_player)

        # Time Label
        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setMinimumWidth(110)
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.time_label.setStyleSheet("color: #8b949e; font-family: monospace; font-size: 14px; background: transparent;")

        # Waveform Widget
        self.waveform = WaveformWidget(self)
        self.waveform.setMinimumWidth(250)

        # Volume Slider
        vol_layout = QHBoxLayout()
        vol_icon = QLabel()
        vol_icon.setPixmap(create_svg_pixmap(SVG_VOLUME, color="#8b949e", size=20))
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(80)
        self.volume_slider.setFixedWidth(80)
        self.volume_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border-radius: 2px;
                height: 4px;
                background: #30363d;
            }
            QSlider::handle:horizontal {
                background: #58a6ff;
                width: 12px;
                height: 12px;
                margin: -4px 0;
                border-radius: 6px;
            }
            QSlider::sub-page:horizontal {
                background: #58a6ff;
                border-radius: 2px;
            }
        """)
        self.volume_slider.valueChanged.connect(lambda v: self.audio_output.setVolume(v / 100))
        
        vol_layout.addWidget(vol_icon)
        vol_layout.addWidget(self.volume_slider)

        # Media Info Area
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        info_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        
        title_row = QHBoxLayout()
        self.title_label = QLabel("Medya Oynatıcı Hazır")
        self.title_label.setStyleSheet("font-weight: 800; color: #ffffff; font-size: 14px; background: transparent;")
        self.title_label.setFixedWidth(150)
        title_row.addWidget(self.title_label)
        
        self.subtitle_label = QLabel("Seçim bekleniyor...")
        self.subtitle_label.setStyleSheet("color: #8b949e; font-size: 12px; background: transparent;")
        
        info_layout.addLayout(title_row)
        info_layout.addWidget(self.subtitle_label)

        layout.addWidget(self.cover_label)
        layout.addWidget(self.play_btn)
        layout.addWidget(self.open_file_btn)
        layout.addWidget(self.time_label)
        layout.addWidget(self.waveform, stretch=1)
        layout.addLayout(vol_layout)
        layout.addLayout(info_layout)
        layout.addWidget(self.expand_btn)

    def open_expanded_player(self):
        from src.utils.icons import create_svg_icon, SVG_EXPAND, SVG_COLLAPSE
        self.is_expanded = not getattr(self, 'is_expanded', False)
        if self.is_expanded:
            self.expand_btn.setIcon(create_svg_icon(SVG_COLLAPSE, color="#8b949e", size=20))
            self.expand_btn.setToolTip("Daralt")
        else:
            self.expand_btn.setIcon(create_svg_icon(SVG_EXPAND, color="#8b949e", size=20))
            self.expand_btn.setToolTip("Tam Ekran Oynatıcı")
            
        self.expand_toggled.emit(self.is_expanded)

    def browse_media(self):
        from PyQt6.QtWidgets import QFileDialog
        import os
        path, _ = QFileDialog.getOpenFileName(
            self, "Müzik / Video Seç", "", "Audio/Video Files (*.mp3 *.m4a *.mp4 *.wav *.flac)"
        )
        if path:
            title = os.path.basename(path)
            self.load_media(path, title)

    def load_media(self, file_path, title=""):
        import mutagen
        from mutagen.id3 import ID3
        from mutagen.mp4 import MP4
        from PyQt6.QtGui import QPixmap, QImage
        from src.utils.icons import create_svg_pixmap, SVG_MUSIC, SVG_PAUSE
        from src.utils.icons import create_svg_icon
        
        self.current_file = file_path
        
        # Try to load Album Art
        pixmap = None
        qimage = None
        try:
            if file_path.endswith('.mp3'):
                tags = ID3(file_path)
                for tag in tags.values():
                    if tag.FrameID == 'APIC':
                        qimage = QImage.fromData(tag.data)
                        pixmap = QPixmap.fromImage(qimage)
                        break
            elif file_path.endswith('.m4a') or file_path.endswith('.mp4'):
                tags = MP4(file_path)
                if 'covr' in tags and len(tags['covr']) > 0:
                    qimage = QImage.fromData(tags['covr'][0])
                    pixmap = QPixmap.fromImage(qimage)
        except Exception:
            pass

        self.high_res_cover = pixmap

        if pixmap:
            scaled_pixmap = pixmap.scaled(50, 50, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
            self.cover_label.setPixmap(scaled_pixmap)
            from src.utils.image_utils import get_dominant_colors
            c1, c2 = get_dominant_colors(qimage)
            self.color_ready.emit(c1, c2)
        else:
            self.cover_label.clear()
            self.cover_label.setPixmap(create_svg_pixmap(SVG_MUSIC, color="#8b949e", size=24))
            self.color_ready.emit(QColor(13, 17, 23), QColor(48, 54, 61)) # Default background
        
        clean_title = title.split('.')[0]
        if len(clean_title) > 25:
            clean_title = clean_title[:22] + "..."
            
        self.title_label.setText(clean_title)
        self.subtitle_label.setText("Şimdi Çalıyor")
        
        self.player.setSource(QUrl.fromLocalFile(file_path))
        
        self.waveform.set_progress(0.0)
        self.waveform.set_loading(True)
        self.time_label.setText("00:00 / 00:00")
        
        self.analyzer = WaveformAnalyzerWorker(file_path, num_bars=120)
        self.analyzer.finished.connect(self.on_analyzer_finished)
        self.analyzer.start()
        
        self.player.play()
        from src.utils.icons import create_svg_icon, SVG_PAUSE
        self.play_btn.setIcon(create_svg_icon(SVG_PAUSE, color="#0d1117", size=24))
        self.media_loaded.emit(file_path, clean_title)

    def on_analyzer_finished(self, data):
        if not data or not data.get("peaks"):
            self.waveform.set_peaks([])
            self.peaks_ready.emit([])
            return
            
        self.audio_samples = data.get("samples")
        self.frame_rate = data.get("frame_rate")
        self.waveform.set_peaks(data["peaks"])
        self.peaks_ready.emit(data["peaks"])

    def toggle_playback(self):
        from src.utils.icons import create_svg_icon, SVG_PLAY, SVG_PAUSE
        if not self.current_file:
            # Auto-play a random file from download directory
            import os, random
            from src.utils.config import config
            d_path = config.get("download_path")
            if os.path.exists(d_path):
                files = [f for f in os.listdir(d_path) if f.lower().endswith(('.mp3', '.m4a', '.wav', '.flac', '.mp4'))]
                if files:
                    random_file = random.choice(files)
                    self.load_media(os.path.join(d_path, random_file))
            return
        
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
            self.play_btn.setIcon(create_svg_icon(SVG_PLAY, color="#0d1117", size=24))
        else:
            self.player.play()
            self.play_btn.setIcon(create_svg_icon(SVG_PAUSE, color="#0d1117", size=24))

    def on_position_changed(self, position):
        duration = self.player.duration()
        if duration > 0:
            self.waveform.set_progress(position / duration)
            
            # Format time
            pos_sec = position // 1000
            dur_sec = duration // 1000
            self.time_label.setText(f"{pos_sec//60:02d}:{pos_sec%60:02d} / {dur_sec//60:02d}:{dur_sec%60:02d}")
            
            # If song finishes
            if position >= duration - 500:
                if hasattr(self, 'waveform'):
                    self.waveform.set_progress(0.0)
                from src.utils.icons import create_svg_icon, SVG_PLAY
                self.play_btn.setIcon(create_svg_icon(SVG_PLAY, color="#0d1117", size=24))
    def on_duration_changed(self, duration):
        pass

    def seek_to(self, progress):
        if self.player.duration() > 0:
            new_pos = int(progress * self.player.duration())
            self.player.setPosition(new_pos)
