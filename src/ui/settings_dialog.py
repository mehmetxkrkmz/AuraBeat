import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox, QFileDialog
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCursor
from src.utils.config import config

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ayarlar")
        self.setFixedSize(450, 360)
        self.setStyleSheet("""
            QDialog { background-color: #0d1117; color: #c9d1d9; }
            QLabel { font-size: 14px; font-weight: 500; }
            QLineEdit, QComboBox {
                background-color: #010409;
                border: 1px solid #30363d;
                border-radius: 6px;
                padding: 8px;
                color: #c9d1d9;
            }
            QPushButton {
                background-color: #21262d;
                border: 1px solid #30363d;
                border-radius: 6px;
                padding: 8px 15px;
                color: #c9d1d9;
            }
            QPushButton:hover { background-color: #30363d; }
            QPushButton#SaveBtn {
                background-color: #238636;
                color: white;
                font-weight: bold;
                border: none;
            }
            QPushButton#SaveBtn:hover { background-color: #2ea043; }
        """)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        # Download Path
        path_layout = QVBoxLayout()
        path_layout.addWidget(QLabel("Varsayılan İndirme Klasörü:"))
        
        path_input_layout = QHBoxLayout()
        self.path_input = QLineEdit(config.get("download_path"))
        self.path_input.setReadOnly(True)
        
        browse_btn = QPushButton("Gözat")
        browse_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        browse_btn.clicked.connect(self.browse_path)
        
        path_input_layout.addWidget(self.path_input)
        path_input_layout.addWidget(browse_btn)
        path_layout.addLayout(path_input_layout)
        layout.addLayout(path_layout)

        # Default Format
        format_layout = QVBoxLayout()
        format_layout.addWidget(QLabel("Varsayılan İndirme Formatı:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems(["Audio (MP3)", "Video (MP4)"])
        format_layout.addWidget(self.format_combo)
        layout.addLayout(format_layout)
        
        # Language Selection
        lang_layout = QVBoxLayout()
        lang_layout.addWidget(QLabel("Uygulama Dili:"))
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(["Türkçe", "English", "Deutsch", "Español"])
        
        saved_lang = config.get("language")
        if saved_lang:
            idx = self.lang_combo.findText(saved_lang)
            if idx >= 0:
                self.lang_combo.setCurrentIndex(idx)
                
        lang_layout.addWidget(self.lang_combo)
        layout.addLayout(lang_layout)

        layout.addStretch()

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("İptal")
        cancel_btn.clicked.connect(self.reject)
        
        save_btn = QPushButton("Kaydet")
        save_btn.setObjectName("SaveBtn")
        save_btn.clicked.connect(self.save_settings)
        
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)

    def browse_path(self):
        folder = QFileDialog.getExistingDirectory(self, "İndirme Klasörü Seç")
        if folder:
            self.path_input.setText(folder)

    def save_settings(self):
        config.set("download_path", self.path_input.text())
        
        # Save Language
        selected_lang = self.lang_combo.currentText()
        if config.get("language") != selected_lang:
            config.set("language", selected_lang)
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(self, "Bilgi", "Dil değişikliğinin uygulanabilmesi için uygulamayı yeniden başlatmanız gerekmektedir.")
            
        self.accept()
