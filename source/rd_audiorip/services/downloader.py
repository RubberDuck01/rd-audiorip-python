import json
import re
import subprocess
import sys
import locale
import tempfile
import urllib.request
import zipfile
from pathlib import Path
from typing import Any
from PyQt6.QtCore import QObject, pyqtSignal

_PROGRESS_RE = re.compile(r"(\d{1,3}(?:\.\d+)?)%")
_DESTINATION_RE = re.compile(r"^\[ExtractAudio\]\s+Destination:\s+(.+)$")
YTDLP_EXE = "yt-dlp.exe"
YTDLP_DOWNLOAD_URL = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe"
FFMPEG_EXE = "ffmpeg.exe"
FFMPEG_DOWNLOAD_URL = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"

# Suppress the console window that would otherwise flash on Windows when
# spawning child processes from a --windowed PyInstaller bundle.
_SUBPROCESS_FLAGS: dict = (
    {"creationflags": subprocess.CREATE_NO_WINDOW} if sys.platform == "win32" else {}
)


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


def get_tools_ffmpeg_path() -> Path:
    return get_tools_dir() / FFMPEG_EXE


def find_ytdlp_exe() -> str | None:
    path = get_tools_ytdlp_path()
    if path.exists():
        return str(path)

    return None


def find_ffmpeg_exe() -> str | None:
    path = get_tools_ffmpeg_path()
    if path.exists():
        return str(path)

    return None


def _run_tool(command: list[str], timeout: int) -> subprocess.CompletedProcess[bytes] | None:
    try:
        return subprocess.run(command, capture_output=True, timeout=timeout, **_SUBPROCESS_FLAGS)
    except Exception:
        return None


def _extract_ffmpeg(zip_path: Path, destination: Path) -> None:
    with zipfile.ZipFile(zip_path) as archive:
        ffmpeg_member = next(
            (name for name in archive.namelist() if name.lower().endswith("/bin/ffmpeg.exe")),
            None,
        )
        if ffmpeg_member is None:
            raise FileNotFoundError("ffmpeg.exe was not found in the downloaded archive.")

        with archive.open(ffmpeg_member) as source, destination.open("wb") as target:
            target.write(source.read())


def get_video_metadata(url: str) -> dict[str, Any] | None:
    ytdlp = find_ytdlp_exe()
    if not ytdlp:
        return None

    result = _run_tool(
        [ytdlp, "--dump-single-json", "--no-warnings", "--skip-download", "--no-playlist", url],
        timeout=15,
    )
    if result is None or result.returncode != 0:
        return None

    try:
        return json.loads(_decode_output(result.stdout))
    except Exception:
        return None


def get_ytdlp_version() -> str | None:
    ytdlp = find_ytdlp_exe()
    if not ytdlp:
        return None

    result = _run_tool([ytdlp, "--version"], timeout=10)
    if result is not None and result.returncode == 0:
        return _decode_output(result.stdout).strip()

    return None


def get_ffmpeg_version() -> str | None:
    ffmpeg = find_ffmpeg_exe()
    if not ffmpeg:
        return None

    result = _run_tool([ffmpeg, "-version"], timeout=10)
    if result is not None and result.returncode == 0:
        line = _decode_output(result.stdout).splitlines()
        return line[0].strip() if line else None

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
        result = subprocess.run([ytdlp, "-U"], capture_output=True, timeout=60, **_SUBPROCESS_FLAGS)
    except Exception as ex:
        return False, f"Failed to run yt-dlp update: {ex}"

    output = _decode_output(result.stdout or result.stderr).strip()
    if result.returncode == 0:
        return True, output or "yt-dlp update command completed."
    return False, output or "yt-dlp update failed."


def install_or_update_ffmpeg() -> tuple[bool, str]:
    destination = get_tools_ffmpeg_path()

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            archive_path = Path(temp_dir) / "ffmpeg.zip"
            with urllib.request.urlopen(FFMPEG_DOWNLOAD_URL, timeout=60) as response:
                archive_path.write_bytes(response.read())
            _extract_ffmpeg(archive_path, destination)
        return True, f"FFmpeg installed to {destination}"
    except Exception as ex:
        return False, f"Failed to install or update FFmpeg: {ex}"

def get_playlist_info(url: str) -> tuple[bool, str, int]:
    """Return (is_playlist, playlist_title, track_count) without downloading any video."""
    ytdlp = find_ytdlp_exe()
    if not ytdlp:
        return False, "", 0

    result = _run_tool(
        [ytdlp, "--flat-playlist", "--dump-single-json", "--no-warnings", url],
        timeout=20,
    )
    if result is None or result.returncode != 0:
        return False, "", 0

    try:
        data = json.loads(_decode_output(result.stdout))
        if data.get("_type") == "playlist":
            title = str(data.get("title") or data.get("playlist_title") or "Playlist").strip()
            count = len(data.get("entries") or []) or int(data.get("playlist_count") or 0)
            return True, title, count
        return False, "", 0
    except Exception:
        return False, "", 0


def get_video_info(url: str) -> str | None:
    metadata = get_video_metadata(url)
    if not metadata:
        return None

    uploader = str(metadata.get("uploader") or metadata.get("channel") or "").strip()
    title = str(metadata.get("title") or metadata.get("fulltitle") or "").strip()
    if uploader and title:
        return f"{uploader}: {title}"
    return title or uploader or None

def get_video_metrics(url: str) -> tuple[float, int]:
    metadata = get_video_metadata(url)
    if not metadata:
        return 0.0, 0

    try:
        raw_size = metadata.get("filesize_approx") or metadata.get("filesize") or 0
        raw_duration = metadata.get("duration") or 0
        size_b = int(raw_size) if raw_size is not None else 0
        duration_s = int(float(raw_duration)) if raw_duration is not None else 0
        return size_b / (1024 * 1024), max(0, duration_s)
    except Exception:
        return 0.0, 0

class DownloadWorker(QObject):
    progress = pyqtSignal(int)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    output_file = pyqtSignal(str)
    
    def __init__(self, url: str, output_dir: str, preferred_format: str, embed_thumbnail: bool, embed_metadata: bool, flac_compression_level: int, is_playlist: bool = False) -> None:
        super().__init__()
        self.url = url
        self.output_dir = output_dir
        self.preferred_format = (preferred_format or "mp3").lower()
        self.embed_thumbnail = embed_thumbnail
        self.embed_metadata = embed_metadata
        self.flac_compression_level = flac_compression_level
        self.is_playlist = is_playlist
    
    def run(self) -> None:
        ytdlp = find_ytdlp_exe()
        if not ytdlp:
            self.error.emit("yt-dlp executable not found!")
            return

        ffmpeg = find_ffmpeg_exe()
        if not ffmpeg:
            self.error.emit("ffmpeg executable not found!")
            return
        
        fmt = self.preferred_format if self.preferred_format in {"mp3", "flac"} else "mp3"

        output_template = (
            "%(playlist_title)s/%(title)s.%(ext)s"
            if self.is_playlist
            else "%(title)s.%(ext)s"
        )

        args = [
            ytdlp,
            "--newline",
            "-f", "bestaudio",
            "-x",
            "--audio-format", fmt,
            "--output", output_template,
            "--ffmpeg-location", ffmpeg,
        ]

        if not self.is_playlist:
            args.append("--no-playlist")
        
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
                **_SUBPROCESS_FLAGS,
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
            dest_match = _DESTINATION_RE.match(line)
            if dest_match:
                self.output_file.emit(dest_match.group(1).strip())

        rc = proc.wait()
        if rc == 0:
            self.finished.emit("Download completed successfully!")
        else:
            self.error.emit(last_line or f"yt-dlp failed with exit code: {rc}")