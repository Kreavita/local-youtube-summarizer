import yt_dlp
import os


def download_audio(url: str, output_path: str = ".") -> str:
    """Download audio from YouTube video."""
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(output_path, '%(id)s.%(ext)s'),
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        video_id = info['id']
        ext = info.get('ext', 'm4a')
        audio_file = os.path.join(output_path, f"{video_id}.{ext}")
    
    return audio_file
