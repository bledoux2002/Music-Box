import os
import platform
import re
import sys
from urllib.parse import parse_qs, urlparse


def setup_app_directories(base_path=None):
    """Return the application, downloaded-file, and settings paths."""
    if base_path is None:
        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
            base_path = os.path.dirname(base_path)

    filepath = os.path.join(base_path, 'files')
    settings_path = os.path.join(base_path, 'settings.json')
    os.makedirs(filepath, exist_ok=True)
    return base_path, filepath, settings_path


def get_user_data_dir(app_name='MusicBox'):
    """Return the platform-specific user data directory."""
    home = os.path.expanduser('~')
    system = platform.system()
    if system == 'Windows':
        appdata = os.getenv('APPDATA')
        if appdata:
            return os.path.join(appdata, app_name)
        return os.path.join(home, 'AppData', 'Roaming', app_name)
    if system == 'Darwin':
        return os.path.join(home, 'Library', 'Application Support', app_name)
    return os.path.join(home, '.config', app_name)


def clean_filename(file):
    """Remove the download ID and extension from a downloaded filename."""
    index = file.index('[')
    return file[:index - 1].replace('_', ' ')


def format_track_length(length):
    """Convert a duration in seconds to hours, minutes, and seconds."""
    hours = int(length // 3600)
    length %= 3600
    mins = int(length // 60)
    secs = int(length % 60)
    return hours, mins, secs


def extract_youtube_id(url):
    """Extract an 11-character video ID from supported YouTube URL formats."""
    if not url or not isinstance(url, str):
        return None

    url = url.strip()
    patterns = (
        r'(?:youtu\.be/)([a-zA-Z0-9_-]{11})',
        r'(?:youtube\.com.*[?&]v=)([a-zA-Z0-9_-]{11})',
        r'(?:youtube\.com/embed/)([a-zA-Z0-9_-]{11})',
    )
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)

    try:
        parsed = urlparse(url)
        if 'youtube.com' in parsed.netloc or 'youtu.be' in parsed.netloc:
            video_id = parse_qs(parsed.query).get('v', [None])[0]
            if video_id and re.match(r'^[a-zA-Z0-9_-]{11}$', video_id):
                return video_id
    except (TypeError, ValueError):
        return None
    return None


def get_resource_path(relative_path):
    """Get an absolute resource path in development and PyInstaller builds."""
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath('.')
    return os.path.join(base_path, relative_path)
