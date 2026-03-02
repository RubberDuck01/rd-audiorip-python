import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path
from PyQt6.QtCore import QObject, pyqtSignal

_PROGRESS_RE = re.compile(r"(\d{1,3}(?:\.\d+)?)%")
_EXE = ".exe" if platform.system() == "Windows" else ""

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
    ytdlp = find_tool_exe(f"yt-dlp{_EXE}")
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

def get_video_metrics(url: str) -> tuple[float, int]:
    ytdlp = find_tool_exe(f"yt-dlp{_EXE}")
    if not ytdlp:
        return 0.0, 0
    
    try:
        result = subprocess.run(
            [ytdlp, "--print", "%(filesize_approx)s|%(duration)s", "--no-warnings", url],
            capture_output=True,
            text=True,
            timeout=10,
            encoding="utf-8",
            errors="replace"
        )
        
        if result.returncode != 0:
            return 0.0, 0
        
        line = result.stdout.strip().splitlines()[0] if result.stdout.strip() else ""
        raw_size, raw_duration = (line.split("|", 1) + ["0"])[:2]
        
        size_b = int(raw_size) if raw_size.isdigit() else 0
        duration_s = int(float(raw_duration)) if raw_duration else 0
        
        return size_b / (1024 * 1024), max(0, duration_s)
    except Exception:
        return 0.0, 0

class DownloadWorker(QObject):
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    
    def __init__(self, url: str, output_dir: str, preferred_format: str, embed_thumbnail: bool, embed_metadata: bool, flac_compression_level: int) -> None:
        super().__init__()
        self.url = url
        self.output_dir = output_dir
        self.preferred_format = (preferred_format or "mp3").lower()
        self.embed_thumbnail = embed_thumbnail
        self.embed_metadata = embed_metadata
        self.flac_compression_level = flac_compression_level
    
    def run(self) -> None:
        ytdlp = find_tool_exe(f"yt-dlp{_EXE}")
        if not ytdlp:
            self.error.emit("yt-dlp executable not found!")
            return
        self.status.emit(f"Using yt-dlp: {ytdlp}")
        
        ffmpeg = find_tool_exe(f"ffmpeg{_EXE}")
        if not ffmpeg:
            self.error.emit("ffmpeg executable not found!")
            return
        self.status.emit(f"Using ffmpeg: {ffmpeg}")
        
        fmt = self.preferred_format if self.preferred_format in {"mp3", "flac"} else "mp3"
        
        args = [
            ytdlp,
            "--no-playlist",
            "--newline",
            "-f", "bestaudio",
            "-x",
            "--audio-format", fmt,
            "--output", "%(title)s.%(ext)s",
            "--ffmpeg-location", ffmpeg,
        ]
        
        if self.embed_thumbnail:
            args.append("--embed-thumbnail")
        
        if self.embed_metadata:
            args.append("--embed-metadata")
        
        if fmt == "mp3":
            args += [
                "--postprocessor-args",
                "ffmpeg:-codec:a libmp3lame -b:a 320k -ar 48000",
            ]
            self.status.emit("Format: MP3 (320kbps, 48kHz)")
        else:
            level = max(0, min(12, int(self.flac_compression_level)))
            args += [
                "--postprocessor-args",
                f"ffmpeg:-ar 48000 -compression_level {level}",
            ]
            self.status.emit(f"Format: FLAC (compression level {level}, 48kHz)")
        
        args += [
            "-P", self.output_dir,
            self.url,
            "--no-warnings",
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