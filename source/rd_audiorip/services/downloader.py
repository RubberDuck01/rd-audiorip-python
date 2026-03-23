import re
import shutil
import subprocess
import sys
import locale
import urllib.request
from pathlib import Path
from PyQt6.QtCore import QObject, pyqtSignal

_PROGRESS_RE = re.compile(r"(\d{1,3}(?:\.\d+)?)%")
YTDLP_EXE = "yt-dlp.exe"
YTDLP_DOWNLOAD_URL = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe"


def _decode_output(raw: bytes) -> str:
    candidates = ["utf-8", locale.getpreferredencoding(False), "cp1251", "cp866", "latin-1"]
    seen: set[str] = set()

    for enc in candidates:
        if not enc or enc in seen:
            continue
        seen.add(enc)
        try:
            return raw.decode(enc)
        except Exception:
            continue

    return raw.decode("utf-8", errors="replace")


def get_tools_dir() -> Path:
    base = Path(sys.argv[0]).resolve().parent
    tools_dir = base / "tools"
    tools_dir.mkdir(parents=True, exist_ok=True)
    return tools_dir


def get_tools_ytdlp_path() -> Path:
    return get_tools_dir() / YTDLP_EXE


def find_ytdlp_exe() -> str | None:
    path = get_tools_ytdlp_path()
    if path.exists():
        return str(path)

    return None

def find_tool_exe(exe_name: str) -> str | None:
    base = Path(sys.argv[0]).resolve().parent
    tools = base / "tools" / exe_name
    if tools.exists():
        return str(tools)
    
    cwd_tools = Path.cwd() / "tools" / exe_name
    if cwd_tools.exists():
        return str(cwd_tools)
    
    return shutil.which(exe_name)


def get_ytdlp_version() -> str | None:
    ytdlp = find_ytdlp_exe()
    if not ytdlp:
        return None

    try:
        result = subprocess.run(
            [ytdlp, "--version"],
            capture_output=True,
            timeout=10,
        )
        if result.returncode == 0:
            return _decode_output(result.stdout).strip()
    except Exception:
        return None

    return None


def install_ytdlp() -> tuple[bool, str]:
    destination = get_tools_dir() / YTDLP_EXE

    try:
        with urllib.request.urlopen(YTDLP_DOWNLOAD_URL, timeout=30) as response:
            destination.write_bytes(response.read())
        return True, f"yt-dlp installed to {destination}"
    except Exception as ex:
        return False, f"Failed to install yt-dlp: {ex}"


def update_ytdlp() -> tuple[bool, str]:
    ytdlp = find_ytdlp_exe()
    if not ytdlp:
        return False, "yt-dlp is not installed."

    try:
        result = subprocess.run(
            [ytdlp, "-U"],
            capture_output=True,
            timeout=60,
        )
        output = _decode_output(result.stdout or result.stderr).strip()
        if result.returncode == 0:
            return True, output or "yt-dlp update command completed."
        return False, output or "yt-dlp update failed."
    except Exception as ex:
        return False, f"Failed to run yt-dlp update: {ex}"

def get_video_info(url: str) -> str | None:
    ytdlp = find_ytdlp_exe()
    if not ytdlp:
        return None
    
    try:
        result = subprocess.run(
            [ytdlp, "--print", "%(uploader)s: %(title)s", url],
            capture_output=True,
            timeout=10,
        )
        
        if result.returncode == 0:
            return _decode_output(result.stdout).strip()
    except Exception:
        pass
    return None

def get_video_metrics(url: str) -> tuple[float, int]:
    ytdlp = find_ytdlp_exe()
    if not ytdlp:
        return 0.0, 0
    
    try:
        result = subprocess.run(
            [ytdlp, "--print", "%(filesize_approx)s|%(duration)s", "--no-warnings", url],
            capture_output=True,
            timeout=10,
        )
        
        if result.returncode != 0:
            return 0.0, 0
        
        stdout = _decode_output(result.stdout).strip()
        line = stdout.splitlines()[0] if stdout else ""
        raw_size, raw_duration = (line.split("|", 1) + ["0"])[:2]
        
        size_b = int(raw_size) if raw_size.isdigit() else 0
        duration_s = int(float(raw_duration)) if raw_duration else 0
        
        return size_b / (1024 * 1024), max(0, duration_s)
    except Exception:
        return 0.0, 0

class DownloadWorker(QObject):
    progress = pyqtSignal(int)
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
        ytdlp = find_ytdlp_exe()
        if not ytdlp:
            self.error.emit("yt-dlp executable not found!")
            return
        
        ffmpeg = find_tool_exe("ffmpeg.exe")
        if not ffmpeg:
            self.error.emit("ffmpeg executable not found!")
            return
        
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
        else:
            level = max(0, min(12, int(self.flac_compression_level)))
            args += [
                "--postprocessor-args",
                f"ffmpeg:-ar 48000 -compression_level {level}",
            ]
        
        args += [
            "-P", self.output_dir,
            self.url,
            "--no-warnings",
        ]
        
        try:
            proc = subprocess.Popen(
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
        except Exception as ex:
            self.error.emit(f"Failed to start yt-dlp: {ex}")
            return
        
        last_line = ""
        assert proc.stdout is not None
        for raw_line in proc.stdout:
            line = _decode_output(raw_line).strip()
            last_line = line
            match = _PROGRESS_RE.search(line)
            if match:
                self.progress.emit(int(float(match.group(1))))
        
        rc = proc.wait()
        if rc == 0:
            self.finished.emit("Download completed successfully!")
        else:
            self.error.emit(last_line or f"yt-dlp failed with exit code: {rc}")