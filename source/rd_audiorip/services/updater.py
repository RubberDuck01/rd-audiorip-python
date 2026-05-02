import json
import urllib.request

from rd_audiorip.version import __version__

_RELEASES_API = "https://api.github.com/repos/RubberDuck01/rd-audiorip-python/releases/latest"
RELEASES_PAGE = "https://github.com/RubberDuck01/rd-audiorip-python/releases/latest"


def _parse_version(tag: str) -> tuple[int, ...]:
    tag = tag.lstrip("vV")
    try:
        return tuple(int(x) for x in tag.split("."))
    except ValueError:
        return (0,)


def check_for_app_update() -> tuple[bool, str]:
    """Check GitHub releases for a newer version.

    Returns (update_available, latest_version_string).
    Returns (False, "") on any network or parse error.
    """
    try:
        req = urllib.request.Request(
            _RELEASES_API,
            headers={"User-Agent": "RD-AudioRip-UpdateChecker"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        tag = data.get("tag_name", "").strip()
        if not tag:
            return False, ""
        latest = _parse_version(tag)
        current = _parse_version(__version__)
        return latest > current, tag.lstrip("vV")
    except Exception:
        return False, ""
