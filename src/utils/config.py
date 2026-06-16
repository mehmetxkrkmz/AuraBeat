import os
import json
from pathlib import Path

class ConfigManager:
    def __init__(self):
        self.config_dir = Path.home() / ".config" / "AuraBeat"
        self.config_file = self.config_dir / "config.json"
        
        # Default settings
        self.settings = {
            "download_path": str(Path.home() / "Downloads" / "AuraBeat"),
            "default_format": "audio",  # 'audio' or 'video'
            "audio_quality": "320",
            "video_quality": "1080p",
            "theme": "dark"
        }
        
        self.load_config()

    def load_config(self):
        if not self.config_file.exists():
            self.save_config()
            return
        
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                self.settings.update(loaded)
        except Exception as e:
            print(f"Error loading config: {e}")

    def save_config(self):
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")

    def get(self, key, default=None):
        return self.settings.get(key, default)

    def set(self, key, value):
        self.settings[key] = value
        self.save_config()

config = ConfigManager()
