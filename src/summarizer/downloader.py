import yt_dlp
import os
import subprocess
import re
import hashlib
import datetime
from pathlib import Path
from typing import Generator

AUDIO_EXTENSIONS = {'.mp3', '.m4a', '.wav', '.ogg', '.flac', '.aac', '.wma', '.aiff', '.opus'}
VIDEO_EXTENSIONS = {'.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.mpg', '.mpeg'}


def is_local_path(path: str) -> bool:
    """Check if input is a local file path."""
    if not path:
        return False
    p = Path(path)
    if p.exists() and p.is_file():
        return True
    if p.suffix.lower() in AUDIO_EXTENSIONS | VIDEO_EXTENSIONS:
        return True
    return False


def get_file_metadata(file_path: str) -> dict:
    """Get metadata from a local file."""
    input_path = Path(file_path)
    
    file_id = hashlib.md5(str(input_path.resolve()).encode()).hexdigest()[:12]
    
    mtime = input_path.stat().st_mtime
    creation_date = datetime.datetime.fromtimestamp(mtime).strftime('%Y%m%d')
    
    duration_cmd = [
        'ffprobe',
        '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        str(input_path.resolve())
    ]
    duration_result = subprocess.run(duration_cmd, capture_output=True, text=True)
    duration = 0
    if duration_result.returncode == 0 and duration_result.stdout.strip():
        try:
            duration = int(float(duration_result.stdout.strip()))
        except ValueError:
            pass
    
    metadata = {
        'id': file_id,
        'title': input_path.stem,
        'channel': 'local',
        'upload_date': creation_date,
        'description': '',
        'duration': duration,
        'view_count': 0,
        'like_count': 0,
        'categories': [],
        'tags': [],
    }
    
    return metadata


def extract_audio_from_file(file_path: str, output_path: str) -> tuple[str, dict]:
    """Extract audio from a local file using ffmpeg (without conversion)."""
    input_path = Path(file_path)
    ext = input_path.suffix.lower()
    metadata = get_file_metadata(file_path)
    
    output_ext = '.m4a'
    if ext in AUDIO_EXTENSIONS:
        output_ext = ext
    
    audio_file = os.path.join(output_path, f"{metadata['id']}{output_ext}")
    
    cmd = [
        'ffmpeg',
        '-y',
        '-i', str(input_path.resolve()),
        '-vn',
        '-c:a', 'copy',
        audio_file
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {result.stderr}")
    
    if not os.path.exists(audio_file):
        raise RuntimeError(f"Audio file was not created: {result.stderr}")
    
    return audio_file, metadata


def get_video_metadata(url: str) -> dict:
    """Get video metadata."""
    ydl_opts = {'format': 'bestaudio/best'}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        
    metadata = {
        'id': info.get('id', 'unknown'),
        'title': info.get('title', ''),
        'channel': info.get('channel', ''),
        'upload_date': info.get('upload_date', ''),
        'description': info.get('description', ''),
        'duration': info.get('duration', 0),
        'view_count': info.get('view_count', 0),
        'like_count': info.get('like_count', 0),
        'categories': info.get('categories', []),
        'tags': info.get('tags', []),
    }
    
    return metadata


def download_audio_progress(url: str, output_path: str = ".") -> tuple[str, dict, Generator[dict, None, None]]:
    """Download audio from YouTube with progress updates."""
    video_id = None
    
    class ProgressHook:
        def __init__(self):
            self.progress: list[dict] = []
        
        def __call__(self, info):
            if info['status'] == 'downloading':
                total = info.get('total_bytes') or info.get('total_bytes_estimate', 0)
                downloaded = info.get('downloaded_bytes', 0)
                speed = info.get('speed', 0)
                eta = info.get('eta', 0)
                
                if total > 0:
                    pct = downloaded / total
                    speed_str = f"{speed / 1024 / 1024:.2f}MB/s" if speed else "N/A"
                    eta_str = f"{eta // 60}m {eta % 60}s" if eta else "N/A"
                    yield {
                        "progress": pct,
                        "text": f"Downloading... {pct * 100:.1f}% ({speed_str}, ETA: {eta_str})"
                    }
            elif info['status'] == 'finished':
                yield {"progress": 1.0, "text": "Download complete"}
                video_id = info.get('filename', '').split('/')[-1].split('.')[0]

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(output_path, '%(id)s.%(ext)s'),
        'progress_hooks': [ProgressHook()],
    }

    progress_hook = ProgressHook()
    ydl_opts['progress_hooks'] = [progress_hook]

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        video_id = info['id']
        ext = info.get('ext', 'm4a')
        audio_file = os.path.join(output_path, f"{video_id}.{ext}")
        
        metadata = {
            'id': info.get('id', 'unknown'),
            'title': info.get('title', ''),
            'channel': info.get('channel', ''),
            'upload_date': info.get('upload_date', ''),
            'description': info.get('description', ''),
            'duration': info.get('duration', 0),
            'view_count': info.get('view_count', 0),
            'like_count': info.get('like_count', 0),
            'categories': info.get('categories', []),
            'tags': info.get('tags', []),
        }
    
    def progress_gen():
        yield from progress_hook.progress
        yield {"progress": 1.0, "text": "Download complete"}
    
    return audio_file, metadata, progress_gen()


def download_audio(url: str, output_path: str = ".") -> tuple[str, dict]:
    """Download audio from YouTube video and return audio path + metadata."""
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(output_path, '%(id)s.%(ext)s'),
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        video_id = info['id']
        ext = info.get('ext', 'm4a')
        audio_file = os.path.join(output_path, f"{video_id}.{ext}")
        
        metadata = {
            'id': info.get('id', 'unknown'),
            'title': info.get('title', ''),
            'channel': info.get('channel', ''),
            'upload_date': info.get('upload_date', ''),
            'description': info.get('description', ''),
            'duration': info.get('duration', 0),
            'view_count': info.get('view_count', 0),
            'like_count': info.get('like_count', 0),
            'categories': info.get('categories', []),
            'tags': info.get('tags', []),
        }
    
    return audio_file, metadata
