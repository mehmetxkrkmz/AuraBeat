import os
from pathlib import Path
import yt_dlp
from src.utils.config import config

class MyLogger:
    def __init__(self, skip_callback):
        self.skip_callback = skip_callback
        
    def debug(self, msg):
        if "has already been recorded in the archive" in msg:
            self.skip_callback()
            
    def warning(self, msg):
        pass
        
    def error(self, msg):
        pass

class Downloader:
    def __init__(self, output_path, progress_callback=None):
        self.output_path = Path(output_path)
        self.output_path.mkdir(parents=True, exist_ok=True)
        self.progress_callback = progress_callback
        self.is_cancelled = False
        self.final_filename = None
        self.is_skipped = False
        
    def on_skip(self):
        self.is_skipped = True
        if self.progress_callback:
            self.progress_callback({
                'status': 'skipped',
                'percent': 100,
                'speed': 'Atlandı',
                'filename': 'Zaten USB/Klasörde Mevcut'
            })

    def hook(self, d):
        if self.is_cancelled:
            raise Exception("Download cancelled by user.")
            
        if d['status'] == 'downloading':
            if self.progress_callback:
                percent_str = d.get('_percent_str', '0%').strip('%').strip()
                if '\x1b' in percent_str:
                    percent_str = percent_str.split('m')[-1]
                    
                try:
                    percent = float(percent_str)
                except ValueError:
                    percent = 0.0

                speed_str = d.get('_speed_str', 'N/A').strip()
                if '\x1b' in speed_str:
                    speed_str = speed_str.split('m')[-1]

                self.progress_callback({
                    'status': 'downloading',
                    'percent': percent,
                    'speed': speed_str,
                    'filename': d.get('filename', 'Bilinmiyor')
                })
        elif d['status'] == 'finished':
            self.final_filename = d.get('filename')
            if self.progress_callback:
                self.progress_callback({
                    'status': 'finished',
                    'percent': 100,
                    'speed': 'İşleniyor...',
                    'filename': self.final_filename
                })

    def download(self, url, fmt="audio", quality="320"):
        ydl_opts = {
            'outtmpl': str(self.output_path / '%(title)s.%(ext)s'),
            'progress_hooks': [self.hook],
            'noplaylist': True,
            'download_archive': str(self.output_path / '.aurabeat_sync.txt'),
            'logger': MyLogger(self.on_skip)
        }
        
        # Apply Advanced Settings
        speed_limit = config.get("speed_limit_kb", 0)
        if speed_limit > 0:
            ydl_opts['ratelimit'] = speed_limit * 1024
            
        proxy = config.get("proxy_url", "")
        if proxy:
            ydl_opts['proxy'] = proxy
            
        ydl_opts['postprocessors'] = []
        
        if fmt == "audio":
            ydl_opts.update({
                'format': 'bestaudio/best',
                'writethumbnail': True,
            })
            ydl_opts['postprocessors'].extend([
                {'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': quality},
                {'key': 'FFmpegMetadata'},
                {'key': 'EmbedThumbnail'}
            ])
        else:
            height = ''.join(filter(str.isdigit, quality))
            if not height:
                height = "1080"
                
            ydl_opts.update({
                'format': f'bestvideo[height<={height}][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            })
            ydl_opts['postprocessors'].append({'key': 'FFmpegMetadata'})

        if config.get("sponsorblock_enabled", False):
            ydl_opts['postprocessors'].append({
                'key': 'SponsorBlock',
                'categories': ['sponsor', 'intro', 'outro', 'selfpromo', 'interaction'],
            })

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
                
            if self.is_skipped:
                return True, "Zaten indirildi (Arşivde mevcut).", "SKIPPED"
                
            # Fix final filename extension
            if self.final_filename:
                import os
                base_name = os.path.splitext(self.final_filename)[0]
                expected_ext = ".mp3" if fmt == "audio" else ".mp4"
                if not self.final_filename.endswith(expected_ext):
                    self.final_filename = base_name + expected_ext
                    
            return True, "İndirme ve işleme tamamlandı.", self.final_filename
        except Exception as e:
            if "cancelled" in str(e).lower():
                return False, "İndirme iptal edildi.", None
            return False, f"Hata: {str(e)}", None
