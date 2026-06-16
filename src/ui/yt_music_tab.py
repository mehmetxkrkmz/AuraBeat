from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, 
                             QPushButton, QScrollArea, QLabel, QFrame, QGridLayout)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QCursor, QPixmap
import urllib.request

class YTSearchThread(QThread):
    result_ready = pyqtSignal(list)
    error_occurred = pyqtSignal(str)

    def __init__(self, query):
        super().__init__()
        self.query = query

    def run(self):
        try:
            from ytmusicapi import YTMusic
            ytmusic = YTMusic()
            results = ytmusic.search(self.query, filter="songs", limit=15)
            self.result_ready.emit(results)
        except Exception as e:
            self.error_occurred.emit(str(e))


class YTSongCard(QFrame):
    play_requested = pyqtSignal(str, str, str) # videoId, title, cover_url

    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.data = data
        self.videoId = data.get("videoId")
        
        self.setObjectName("YTSongCard")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            QFrame#YTSongCard {
                background-color: #161b22;
                border: 1px solid #30363d;
                border-radius: 12px;
            }
            QFrame#YTSongCard:hover {
                border: 1px solid #58a6ff;
                background-color: #21262d;
            }
        """)
        
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        
        # Cover Art
        self.cover_lbl = QLabel()
        self.cover_lbl.setFixedSize(50, 50)
        self.cover_lbl.setStyleSheet("background-color: #0d1117; border-radius: 6px;")
        layout.addWidget(self.cover_lbl)
        
        # Details
        details_layout = QVBoxLayout()
        title = data.get("title", "Unknown")
        artists = ", ".join([a.get("name", "") for a in data.get("artists", [])])
        
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("font-weight: bold; font-size: 14px; color: #ffffff;")
        
        artist_lbl = QLabel(artists)
        artist_lbl.setStyleSheet("color: #8b949e; font-size: 12px;")
        
        details_layout.addWidget(title_lbl)
        details_layout.addWidget(artist_lbl)
        layout.addLayout(details_layout, stretch=1)
        
        # Load Cover Async (simple)
        thumbnails = data.get("thumbnails", [])
        if thumbnails:
            self.cover_url = thumbnails[-1].get("url")
            # In a real app we load this async, here we just pass it to player to handle
        else:
            self.cover_url = ""

    def mousePressEvent(self, event):
        if self.videoId:
            title = self.data.get("title", "Unknown")
            artists = ", ".join([a.get("name", "") for a in self.data.get("artists", [])])
            full_title = f"{artists} - {title}"
            self.play_requested.emit(self.videoId, full_title, self.cover_url)


class YTMusicTab(QWidget):
    # Emit full yt-dlp url logic
    stream_requested = pyqtSignal(str, str, str) # url, title, cover_url

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)
        
        # Search Bar
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("YouTube Music'te milyonlarca şarkı ara...")
        self.search_input.returnPressed.connect(self.perform_search)
        
        self.search_btn = QPushButton("Ara")
        self.search_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.search_btn.setStyleSheet("""
            QPushButton {
                background-color: #238636; color: #ffffff;
                border-radius: 20px; font-weight: bold; font-size: 14px;
                padding: 10px 20px;
            }
            QPushButton:hover { background-color: #2ea043; }
        """)
        self.search_btn.clicked.connect(self.perform_search)
        
        search_layout.addWidget(self.search_input, stretch=1)
        search_layout.addWidget(self.search_btn)
        
        layout.addLayout(search_layout)
        
        # Loading Indicator
        self.status_lbl = QLabel("En sevdiğin parçaları aramaya başla!")
        self.status_lbl.setStyleSheet("color: #8b949e; font-size: 14px;")
        self.status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_lbl)
        
        # Results Scroll Area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("background: transparent; border: none;")
        
        self.results_widget = QWidget()
        self.results_widget.setStyleSheet("background: transparent;")
        self.results_layout = QVBoxLayout(self.results_widget)
        self.results_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.results_layout.setSpacing(10)
        
        self.scroll_area.setWidget(self.results_widget)
        layout.addWidget(self.scroll_area, stretch=1)

    def perform_search(self):
        query = self.search_input.text().strip()
        if not query: return
        
        # Clear results
        for i in reversed(range(self.results_layout.count())):
            w = self.results_layout.itemAt(i).widget()
            if w:
                w.setParent(None)
                
        self.status_lbl.setText("Aranıyor... Lütfen bekleyin.")
        self.status_lbl.show()
        self.scroll_area.hide()
        
        self.thread = YTSearchThread(query)
        self.thread.result_ready.connect(self.on_results)
        self.thread.error_occurred.connect(self.on_error)
        self.thread.start()

    def on_results(self, results):
        self.status_lbl.hide()
        self.scroll_area.show()
        
        if not results:
            self.status_lbl.setText("Sonuç bulunamadı.")
            self.status_lbl.show()
            self.scroll_area.hide()
            return
            
        for item in results:
            card = YTSongCard(item)
            card.play_requested.connect(self.handle_play)
            self.results_layout.addWidget(card)

    def on_error(self, err):
        self.status_lbl.setText(f"Hata oluştu: {err}")
        self.status_lbl.show()
        self.scroll_area.hide()

    def handle_play(self, video_id, title, cover_url):
        # We pass this up to main_window which will use yt-dlp to get the audio stream
        url = f"https://www.youtube.com/watch?v={video_id}"
        self.stream_requested.emit(url, title, cover_url)
