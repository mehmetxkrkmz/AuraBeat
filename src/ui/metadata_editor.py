import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QFileDialog, QMessageBox
)
from PyQt6.QtGui import QPixmap, QCursor
from PyQt6.QtCore import Qt

import mutagen
from mutagen.id3 import ID3, TIT2, TPE1, TALB, APIC
from mutagen.mp4 import MP4, MP4Cover

class MetadataEditorDialog(QDialog):
    def __init__(self, file_path, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.cover_path = None
        self.setWindowTitle("Etiket Düzenleyici (Metadata)")
        self.setFixedSize(400, 450)
        self.setup_ui()
        self.load_metadata()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)

        self.setStyleSheet("""
            QDialog { background-color: #0d1117; }
            QLabel { color: #c9d1d9; font-weight: 600; font-size: 13px; }
            QLabel#HeaderTitle { color: #ffffff; font-size: 20px; font-weight: 800; }
            QLineEdit {
                background-color: #010409;
                border: 1px solid #30363d;
                border-radius: 8px;
                color: #c9d1d9;
                padding: 10px 12px;
                font-size: 14px;
            }
            QLineEdit:focus { border: 1px solid #58a6ff; }
            QPushButton {
                background-color: #21262d;
                border: 1px solid #30363d;
                border-radius: 8px;
                color: #c9d1d9;
                padding: 10px 15px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #30363d; border-color: #8b949e; }
            QPushButton#SaveBtn {
                background-color: #238636;
                color: white;
                border: none;
            }
            QPushButton#SaveBtn:hover { background-color: #2ea043; }
        """)

        # Header
        header = QLabel("Medyayı Kişiselleştir")
        header.setObjectName("HeaderTitle")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)

        # Cover image
        self.cover_label = QLabel("Görsel\nYok")
        self.cover_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cover_label.setFixedSize(130, 130)
        self.cover_label.setStyleSheet("border: 1px solid #30363d; border-radius: 12px; background-color: #161b22; color: #8b949e;")
        
        self.change_cover_btn = QPushButton("Kapak Değiştir")
        self.change_cover_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.change_cover_btn.clicked.connect(self.select_cover)

        cover_layout = QHBoxLayout()
        cover_layout.addStretch()
        cover_layout.addWidget(self.cover_label)
        
        btn_container = QVBoxLayout()
        btn_container.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        btn_container.addWidget(self.change_cover_btn)
        
        cover_layout.addSpacing(20)
        cover_layout.addLayout(btn_container)
        cover_layout.addStretch()
        layout.addLayout(cover_layout)

        # Fields Setup
        fields_layout = QVBoxLayout()
        fields_layout.setSpacing(10)
        
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Örn: Bohemian Rhapsody")
        
        self.artist_input = QLineEdit()
        self.artist_input.setPlaceholderText("Örn: Queen")
        
        self.album_input = QLineEdit()
        self.album_input.setPlaceholderText("Örn: A Night at the Opera")

        fields_layout.addWidget(QLabel("Şarkı Adı"))
        fields_layout.addWidget(self.title_input)
        
        fields_layout.addWidget(QLabel("Sanatçı"))
        fields_layout.addWidget(self.artist_input)
        
        fields_layout.addWidget(QLabel("Albüm"))
        fields_layout.addWidget(self.album_input)
        
        layout.addLayout(fields_layout)
        layout.addStretch()

        # Buttons
        btn_layout = QHBoxLayout()
        self.cancel_btn = QPushButton("İptal")
        self.cancel_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.cancel_btn.clicked.connect(self.reject)
        
        self.save_btn = QPushButton("Değişiklikleri Kaydet")
        self.save_btn.setObjectName("SaveBtn")
        self.save_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.save_btn.clicked.connect(self.save_metadata)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.save_btn)
        layout.addLayout(btn_layout)

    def select_cover(self):
        path, _ = QFileDialog.getOpenFileName(self, "Kapak Resmi Seç", "", "Images (*.png *.jpg *.jpeg)")
        if path:
            self.cover_path = path
            pixmap = QPixmap(path).scaled(120, 120, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
            self.cover_label.setPixmap(pixmap)

    def load_metadata(self):
        try:
            audio = mutagen.File(self.file_path)
            if audio is None:
                return

            # Very basic extraction (depends on format)
            if self.file_path.endswith('.mp3'):
                tags = ID3(self.file_path)
                if 'TIT2' in tags: self.title_input.setText(str(tags['TIT2']))
                if 'TPE1' in tags: self.artist_input.setText(str(tags['TPE1']))
                if 'TALB' in tags: self.album_input.setText(str(tags['TALB']))
            elif self.file_path.endswith('.mp4') or self.file_path.endswith('.m4a'):
                tags = MP4(self.file_path)
                if '\xa9nam' in tags: self.title_input.setText(tags['\xa9nam'][0])
                if '\xa9ART' in tags: self.artist_input.setText(tags['\xa9ART'][0])
                if '\xa9alb' in tags: self.album_input.setText(tags['\xa9alb'][0])
                
        except Exception as e:
            print(f"Error reading tags: {e}")

    def save_metadata(self):
        try:
            if self.file_path.endswith('.mp3'):
                try:
                    tags = ID3(self.file_path)
                except:
                    tags = ID3()
                tags['TIT2'] = TIT2(encoding=3, text=self.title_input.text())
                tags['TPE1'] = TPE1(encoding=3, text=self.artist_input.text())
                tags['TALB'] = TALB(encoding=3, text=self.album_input.text())
                
                if self.cover_path:
                    with open(self.cover_path, 'rb') as c:
                        tags.add(APIC(
                            encoding=3,
                            mime='image/jpeg' if self.cover_path.lower().endswith('.jpg') else 'image/png',
                            type=3, desc='Cover', data=c.read()
                        ))
                tags.save(self.file_path)

            elif self.file_path.endswith('.mp4') or self.file_path.endswith('.m4a'):
                tags = MP4(self.file_path)
                tags['\xa9nam'] = [self.title_input.text()]
                tags['\xa9ART'] = [self.artist_input.text()]
                tags['\xa9alb'] = [self.album_input.text()]
                
                if self.cover_path:
                    with open(self.cover_path, 'rb') as c:
                        fmt = MP4Cover.FORMAT_JPEG if self.cover_path.lower().endswith('.jpg') else MP4Cover.FORMAT_PNG
                        tags['covr'] = [MP4Cover(c.read(), imageformat=fmt)]
                tags.save()

            QMessageBox.information(self, "Başarılı", "Etiketler kaydedildi!")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Etiketler kaydedilemedi:\n{str(e)}")
