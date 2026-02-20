import re
import shutil
import subprocess
import sys
from pathlib import Path
from PyQt6.QtCore import QObject, pyqtSignal

_PROGRESS_RE = re.compile(r"(\d{1,3}(?:\.\d+)?)%")

def find_tool_exe(exe_name: str) -> str | None:
    base = Path(sys.argv[0]).resolve().parent
    tools = base / "tools" / exe_name
    if tools.exists():
        return str(tools)
    
    cwd_tools = Path.cwd() / "tools" / exe_name
    if cwd_tools.exists():
        return str(cwd_tools)
    
    return shutil.which(exe_name)

def get_video_info(url: str) -> str | None:
    ytdlp = find_tool_exe("yt-dlp.exe")
    if not ytdlp:
        return None
    
    try:
        result = subprocess.run(
            [ytdlp, "--print", "%(uploader)s: %(title)s", url],
            capture_output=True,
            text=True,
            timeout=10,
            encoding="utf-8",
            errors="replace"
        )
        
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return None

class DownloadWorker(QObject):
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    
    def __init__(self, url: str, output_dir: str) -> None:
        super().__init__()
        self.url = url
        self.output_dir = output_dir
    
    def run(self) -> None:
        ytdlp = find_tool_exe("yt-dlp.exe")
        if not ytdlp:
            self.error.emit("yt-dlp executable not found!")
            return
        self.status.emit(f"Using yt-dlp: {ytdlp}")
        
        ffmpeg = find_tool_exe("ffmpeg.exe")
        if not ffmpeg:
            self.error.emit("ffmpeg executable not found!")
            return
        self.status.emit(f"Using ffmpeg: {ffmpeg}")
        
        args = [
            ytdlp,
            "--no-playlist",
            "--newline",
            "-f", "bestaudio",
            "--embed-thumbnail",
            "--embed-metadata",
            "-x",
            "--audio-format", "mp3",
            "--output", "%(title)s.%(ext)s",
            "--postprocessor-args", "ffmpeg:-codec:a libmp3lame -b:a 320k -ar 48000",
            "--ffmpeg-location", ffmpeg,
            "-P", self.output_dir,
            self.url,
        ]
        
        self.status.emit("Starting yt-dlp...")
        
        try:
            proc = subprocess.Popen(
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace"
            )
        except Exception as ex:
            self.error.emit(f"Failed to start yt-dlp: {ex}")
            return
        
        last_line = ""
        assert proc.stdout is not None
        for line in proc.stdout:
            last_line = line.strip()
            match = _PROGRESS_RE.search(line)
            if match:
                self.progress.emit(int(float(match.group(1))))
        
        rc = proc.wait()
        if rc == 0:
            self.finished.emit("Download completed successfully!")
        else:
            self.error.emit(last_line or f"yt-dlp failed with exit code: {rc}")