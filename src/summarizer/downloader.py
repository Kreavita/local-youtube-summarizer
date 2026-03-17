import yt_dlp
import os


def get_video_info(url: str) -> dict:
    """Get video metadata."""
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join('.', '%(id)s.%(ext)s'),
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        
    metadata = {
        'title': info.get('title', ''),
        'channel': info.get('channel', ''),
        'upload_date': info.get('upload_date', ''),
        'description': info.get('description', ''),
    }
    
    return metadata


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
            'title': info.get('title', ''),
            'channel': info.get('channel', ''),
            'upload_date': info.get('upload_date', ''),
            'description': info.get('description', ''),
        }
    
    return audio_file, metadata
