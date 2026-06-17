import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, 
    QComboBox, QFileDialog, QTabWidget, QWidget, QCheckBox, QSpinBox, 
    QFormLayout, QMessageBox, QColorDialog
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCursor, QColor
from src.utils.config import config

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gelişmiş Ayarlar")
        self.setFixedSize(550, 480)
        self.accent_color = config.get("accent_color", "#58a6ff")
        
        self.setStyleSheet(f"""
            QDialog {{ background-color: #0d1117; color: #c9d1d9; }}
            QLabel {{ font-size: 13px; font-weight: 500; }}
            QLineEdit, QComboBox, QSpinBox {{
                background-color: #010409;
                border: 1px solid #30363d;
                border-radius: 6px;
                padding: 6px;
                color: #c9d1d9;
            }}
            QTabWidget::pane {{ border: 1px solid #30363d; border-radius: 6px; background-color: #161b22; }}
            QTabBar::tab {{
                background-color: #0d1117; color: #8b949e;
                padding: 8px 15px; border-bottom: 2px solid transparent;
            }}
            QTabBar::tab:selected {{ color: {self.accent_color}; border-bottom: 2px solid {self.accent_color}; font-weight: bold; }}
            QPushButton {{
                background-color: #21262d; border: 1px solid #30363d; border-radius: 6px; padding: 6px 15px; color: #c9d1d9;
            }}
            QPushButton:hover {{ background-color: #30363d; }}
            QPushButton#SaveBtn {{ background-color: #238636; color: white; font-weight: bold; border: none; }}
            QPushButton#SaveBtn:hover {{ background-color: #2ea043; }}
            QCheckBox {{ spacing: 8px; }}
            QCheckBox::indicator {{ width: 16px; height: 16px; border-radius: 3px; border: 1px solid #30363d; background: #010409; }}
            QCheckBox::indicator:checked {{ background: {self.accent_color}; border: 1px solid {self.accent_color}; image: url(none); }}
        """)
        
        self.setup_ui()
        self.load_settings()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        
        self.tabs = QTabWidget()
        self.tabs.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        
        # --- TAB 1: GENEL (General) ---
        self.tab_general = QWidget()
        general_layout = QVBoxLayout(self.tab_general)
        general_layout.setSpacing(15)
        
        # Download Path
        path_layout = QHBoxLayout()
        self.path_input = QLineEdit()
        self.path_input.setReadOnly(True)
        browse_btn = QPushButton("Gözat")
        browse_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        browse_btn.clicked.connect(self.browse_path)
        path_layout.addWidget(QLabel("İndirme Klasörü:"))
        path_layout.addWidget(self.path_input)
        path_layout.addWidget(browse_btn)
        general_layout.addLayout(path_layout)
        
        # Language
        lang_layout = QHBoxLayout()
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(["Türkçe", "English", "Deutsch", "Español"])
        lang_layout.addWidget(QLabel("Arayüz Dili:"))
        lang_layout.addWidget(self.lang_combo)
        lang_layout.addStretch()
        general_layout.addLayout(lang_layout)
        
        # Startup options
        self.startup_clipboard_cb = QCheckBox("AuraBeat açıldığında 'Akıllı Pano İzleyici' otomatik başlasın")
        general_layout.addWidget(self.startup_clipboard_cb)
        
        general_layout.addStretch()
        self.tabs.addTab(self.tab_general, "⚙️ Genel")
        
        # --- TAB 2: AĞ & İNDİRME (Network & Download) ---
        self.tab_download = QWidget()
        download_form = QFormLayout(self.tab_download)
        download_form.setSpacing(15)
        
        self.format_combo = QComboBox()
        self.format_combo.addItems(["Audio (MP3)", "Video (MP4)"])
        download_form.addRow("Varsayılan İndirme Formatı:", self.format_combo)
        
        self.concurrent_spin = QSpinBox()
        self.concurrent_spin.setRange(1, 10)
        self.concurrent_spin.setToolTip("Aynı anda kaç farklı dosyanın indirileceğini belirler.")
        download_form.addRow("Eşzamanlı İndirme Limiti:", self.concurrent_spin)
        
        self.speed_limit_spin = QSpinBox()
        self.speed_limit_spin.setRange(0, 50000)
        self.speed_limit_spin.setSuffix(" KB/s")
        self.speed_limit_spin.setSpecialValueText("Sınırsız (0)")
        download_form.addRow("Hız Limiti (Download Throttle):", self.speed_limit_spin)
        
        self.proxy_input = QLineEdit()
        self.proxy_input.setPlaceholderText("Örn: socks5://127.0.0.1:1080 (Boş = Devre dışı)")
        download_form.addRow("Özel Proxy (Gelişmiş):", self.proxy_input)
        
        self.tabs.addTab(self.tab_download, "🌐 Ağ ve İndirme")
        
        # --- TAB 3: GELİŞMİŞ (Advanced) ---
        self.tab_advanced = QWidget()
        adv_layout = QVBoxLayout(self.tab_advanced)
        adv_layout.setSpacing(15)
        
        # SponsorBlock
        self.sponsorblock_cb = QCheckBox("YouTube SponsorBlock Entegrasyonu")
        self.sponsorblock_cb.setToolTip("Videolardaki reklam/sponsorluk konuşmalarını otomatik kesip atar.")
        adv_layout.addWidget(self.sponsorblock_cb)
        
        # Accent Color
        color_layout = QHBoxLayout()
        color_layout.addWidget(QLabel("Arayüz Vurgu Rengi:"))
        self.color_preview = QLabel("██████")
        self.color_preview.setStyleSheet(f"color: {self.accent_color}; font-size: 16px;")
        
        pick_color_btn = QPushButton("Renk Seç")
        pick_color_btn.clicked.connect(self.pick_color)
        color_layout.addWidget(self.color_preview)
        color_layout.addWidget(pick_color_btn)
        color_layout.addStretch()
        adv_layout.addLayout(color_layout)
        
        adv_layout.addStretch()
        self.tabs.addTab(self.tab_advanced, "🛠️ Gelişmiş")
        
        main_layout.addWidget(self.tabs)
        
        # Bottom Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("İptal")
        cancel_btn.clicked.connect(self.reject)
        
        save_btn = QPushButton("Kaydet ve Uygula")
        save_btn.setObjectName("SaveBtn")
        save_btn.clicked.connect(self.save_settings)
        save_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        
        main_layout.addLayout(btn_layout)

    def load_settings(self):
        self.path_input.setText(config.get("download_path", ""))
        
        lang = config.get("language", "Türkçe")
        idx = self.lang_combo.findText(lang)
        if idx >= 0: self.lang_combo.setCurrentIndex(idx)
            
        self.startup_clipboard_cb.setChecked(config.get("clipboard_on_startup", False))
        
        fmt = config.get("default_format", "audio")
        self.format_combo.setCurrentIndex(0 if fmt == "audio" else 1)
        
        self.concurrent_spin.setValue(config.get("max_concurrent_downloads", 3))
        self.speed_limit_spin.setValue(config.get("speed_limit_kb", 0))
        self.proxy_input.setText(config.get("proxy_url", ""))
        self.sponsorblock_cb.setChecked(config.get("sponsorblock_enabled", False))

    def pick_color(self):
        color = QColorDialog.getColor(QColor(self.accent_color), self, "Vurgu Rengi Seç")
        if color.isValid():
            self.accent_color = color.name()
            self.color_preview.setStyleSheet(f"color: {self.accent_color}; font-size: 16px;")

    def browse_path(self):
        folder = QFileDialog.getExistingDirectory(self, "İndirme Klasörü Seç")
        if folder:
            self.path_input.setText(folder)

    def save_settings(self):
        config.set("download_path", self.path_input.text())
        
        # Check if language changed
        selected_lang = self.lang_combo.currentText()
        lang_changed = config.get("language") != selected_lang
        config.set("language", selected_lang)
        
        config.set("clipboard_on_startup", self.startup_clipboard_cb.isChecked())
        config.set("default_format", "audio" if self.format_combo.currentIndex() == 0 else "video")
        config.set("max_concurrent_downloads", self.concurrent_spin.value())
        config.set("speed_limit_kb", self.speed_limit_spin.value())
        config.set("proxy_url", self.proxy_input.text().strip())
        config.set("sponsorblock_enabled", self.sponsorblock_cb.isChecked())
        
        color_changed = config.get("accent_color") != self.accent_color
        config.set("accent_color", self.accent_color)
        
        if lang_changed or color_changed:
            QMessageBox.information(self, "Bilgi", "Dil veya arayüz rengi değişikliğinin tam olarak uygulanabilmesi için uygulamayı yeniden başlatmanız gerekmektedir.")
            
        self.accept()
