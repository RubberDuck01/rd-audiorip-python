import json
import os
import platform
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
import zipfile
from pathlib import Path
from PyQt6.QtCore import QObject, pyqtSignal

_EXE = ".exe" if platform.system() == "Windows" else ""

_YTDLP_API = "https://api.github.com/repos/yt-dlp/yt-dlp/releases/latest"
_FFMPEG_WIN_URL = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
_FFMPEG_LINUX_URL = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux64-gpl.tar.xz"
_FFMPEG_MAC_URL = "https://evermeet.cx/ffmpeg/getrelease/zip"


def get_tools_dir() -> Path:
    base = Path(sys.argv[0]).resolve().parent
    tools_dir = base / "tools"
    tools_dir.mkdir(exist_ok=True)
    return tools_dir


def get_installed_version(tool: str) -> str | None:
    from rd_audiorip.services.downloader import find_tool_exe
    exe = find_tool_exe(f"{tool}{_EXE}")
    if not exe:
        return None
    try:
        if tool == "yt-dlp":
            result = subprocess.run([exe, "--version"], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return result.stdout.strip()
        else:
            result = subprocess.run([exe, "-version"], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                parts = result.stdout.strip().splitlines()[0].split()
                if len(parts) >= 3:
                    return parts[2]
    except Exception:
        pass
    return None


def get_latest_ytdlp_version() -> str | None:
    try:
        req = urllib.request.Request(_YTDLP_API, headers={"User-Agent": "rd-audiorip"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        return data.get("tag_name")
    except Exception:
        return None


class UpdateWorker(QObject):
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, tool: str) -> None:
        super().__init__()
        self.tool = tool  # "ytdlp" or "ffmpeg"

    def run(self) -> None:
        try:
            if self.tool == "ytdlp":
                self._update_ytdlp()
            elif self.tool == "ffmpeg":
                self._update_ffmpeg()
        except Exception as ex:
            self.error.emit(str(ex))

    def _update_ytdlp(self) -> None:
        self.status.emit("Fetching latest yt-dlp release info...")
        try:
            req = urllib.request.Request(_YTDLP_API, headers={"User-Agent": "rd-audiorip"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read())
        except Exception as ex:
            self.error.emit(f"Failed to fetch release info: {ex}")
            return

        asset_name = f"yt-dlp{_EXE}"
        assets = data.get("assets", [])
        asset = next((a for a in assets if a["name"] == asset_name), None)
        if not asset:
            self.error.emit("Could not find a yt-dlp binary for this platform in the release.")
            return

        url = asset["browser_download_url"]
        dest = get_tools_dir() / asset_name
        self.status.emit(f"Downloading {asset_name}...")
        self._download_file(url, dest)

        if platform.system() != "Windows":
            dest.chmod(dest.stat().st_mode | 0o111)

        self.finished.emit(f"yt-dlp updated to {data.get('tag_name', 'latest')}!")

    def _update_ffmpeg(self) -> None:
        system = platform.system()
        if system == "Windows":
            url = _FFMPEG_WIN_URL
            suffix = ".zip"
        elif system == "Darwin":
            url = _FFMPEG_MAC_URL
            suffix = ".zip"
        else:
            url = _FFMPEG_LINUX_URL
            suffix = ".tar.xz"

        tools_dir = get_tools_dir()
        self.status.emit("Downloading FFmpeg (this may take a moment)...")

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp_path = Path(tmp.name)

        try:
            self._download_file(url, tmp_path)
            self.status.emit("Extracting FFmpeg binaries...")

            if suffix == ".zip":
                with zipfile.ZipFile(tmp_path) as zf:
                    for member in zf.namelist():
                        base = Path(member).name
                        if base in (f"ffmpeg{_EXE}", f"ffprobe{_EXE}"):
                            data = zf.read(member)
                            dest = tools_dir / base
                            dest.write_bytes(data)
                            if platform.system() != "Windows":
                                dest.chmod(dest.stat().st_mode | 0o111)
            else:
                with tarfile.open(tmp_path, "r:xz") as tf:
                    for member in tf.getmembers():
                        base = Path(member.name).name
                        if base in ("ffmpeg", "ffprobe"):
                            f = tf.extractfile(member)
                            if f:
                                dest = tools_dir / base
                                dest.write_bytes(f.read())
                                dest.chmod(dest.stat().st_mode | 0o111)

            self.finished.emit("FFmpeg updated successfully!")
        finally:
            tmp_path.unlink(missing_ok=True)

    def _download_file(self, url: str, dest: Path) -> None:
        req = urllib.request.Request(url, headers={"User-Agent": "rd-audiorip"})
        # 120s timeout to accommodate large FFmpeg archives (>100 MB)
        with urllib.request.urlopen(req, timeout=120) as resp:
            total = int(resp.headers.get("Content-Length", 0))
            downloaded = 0
            chunk = 65536
            with open(dest, "wb") as f:
                while True:
                    block = resp.read(chunk)
                    if not block:
                        break
                    f.write(block)
                    downloaded += len(block)
                    if total > 0:
                        self.progress.emit(int(downloaded * 100 / total))
        self.progress.emit(100)
