import yt_dlp
import os


def download_audio(url: str, output_path: str = ".") -> str:
    """Download audio from YouTube video."""
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(output_path, '%(id)s.%(ext)s'),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        video_id = info['id']
        audio_file = os.path.join(output_path, f"{video_id}.mp3")
    
    return audio_file
