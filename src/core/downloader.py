import os
from pathlib import Path
import yt_dlp

class Downloader:
    def __init__(self, output_path, progress_callback=None):
        self.output_path = Path(output_path)
        self.output_path.mkdir(parents=True, exist_ok=True)
        self.progress_callback = progress_callback
        self.is_cancelled = False
        self.final_filename = None

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
        }

        if fmt == "audio":
            ydl_opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [
                    {'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': quality},
                    {'key': 'FFmpegMetadata'},
                    {'key': 'EmbedThumbnail'}
                ],
                'writethumbnail': True,
            })
        else:
            # Parse quality like "1080p" -> "1080"
            height = ''.join(filter(str.isdigit, quality))
            if not height:
                height = "1080"
                
            ydl_opts.update({
                'format': f'bestvideo[height<={height}][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                'postprocessors': [{'key': 'FFmpegMetadata'}],
            })

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            return True, "İndirme ve işleme tamamlandı.", self.final_filename
        except Exception as e:
            if "cancelled" in str(e).lower():
                return False, "İndirme iptal edildi.", None
            return False, f"Hata: {str(e)}", None
