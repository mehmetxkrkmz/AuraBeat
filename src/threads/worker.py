from PyQt6.QtCore import QThread, pyqtSignal
from src.core.downloader import Downloader

class DownloadWorker(QThread):
    progress = pyqtSignal(dict)
    finished = pyqtSignal(bool, str, str)

    def __init__(self, url, fmt, quality, output_path):
        super().__init__()
        self.url = url
        self.fmt = fmt
        self.quality = quality
        self.output_path = output_path
        self.downloader = Downloader(self.output_path, self.report_progress)

    def report_progress(self, data):
        self.progress.emit(data)

    def run(self):
        success, message, filename = self.downloader.download(self.url, self.fmt, self.quality)
        self.finished.emit(success, message, filename or "")

    def cancel(self):
        if self.downloader:
            self.downloader.is_cancelled = True

class PlaylistResolverWorker(QThread):
    finished = pyqtSignal(bool, list, str) # success, entries_list, error_msg

    def __init__(self, url):
        super().__init__()
        self.url = url

    def run(self):
        import yt_dlp
        
        ydl_opts = {
            'extract_flat': True,
            'quiet': True,
            'no_warnings': True,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self.url, download=False)
                
                if 'entries' in info:
                    # It's a playlist
                    entries = list(info['entries'])
                    self.finished.emit(True, entries, "")
                else:
                    # It's a single video
                    self.finished.emit(True, [info], "")
        except Exception as e:
            self.finished.emit(False, [], str(e))
