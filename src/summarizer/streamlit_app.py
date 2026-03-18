import streamlit as st
import tempfile
import os
import hashlib
from pathlib import Path

try:
    from . import downloader, transcriber, summarizer, transcript_fetcher
    from .config import SUMMARY_PROMPT, WHISPER_MODEL, OLLAMA_MODEL
except ImportError:
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from summarizer import downloader, transcriber, summarizer, transcript_fetcher
    from summarizer.config import SUMMARY_PROMPT, WHISPER_MODEL, OLLAMA_MODEL


def run_ui():
    st.set_page_config(page_title="Video Summarizer", page_icon="🎬")
    st.markdown("<style>.block-container {max-width: 900px;}</style>", unsafe_allow_html=True)
    st.title("🎬 Video Summarizer")

    url = st.text_input("YouTube URL or local file path", placeholder="https://youtube.com/watch?v=... or /path/to/video.mp4")

    col1, col2 = st.columns(2)
    with col1:
        whisper_model = st.selectbox(
            "Whisper Model",
            ["tiny", "base", "small", "medium", "large-v3-turbo", "large-v3", "turbo"],
            index=4,
            help="Size of Whisper model for transcription"
        )
        col_transcribe1, col_transcribe2 = st.columns(2)
        with col_transcribe1:
            use_youtube_transcript = st.checkbox("YT Transcript", value=True, help="Try fetching YouTube transcript first")
        with col_transcribe2:
            use_whisper = st.checkbox("YT-DLP and Whisper", value=True, help="Download Audio and use Whisper if YouTube transcript unavailable")
    
        include_timestamps = st.checkbox("Include timestamps", value=True, help="Include timestamps in transcript (uses more context)")
            
    with col2:
        ollama_model = st.text_input("Ollama Model", value=OLLAMA_MODEL)

        context_values = [4096, 6144, 8192, 12288, 16384, 24576, 32768, 49152, 65536, 98304, 131072, 196608, 262144, 393216, 524288, 786432, 1048576]
        context_labels = ["4K", "6K", "8K", "12K", "16K", "24K", "32K", "48K", "64K", "96K", "128K", "192K", "256K", "384K", "512K", "768K", "1M"]

        default_idx = context_values.index(32768) if 32768 in context_values else 3
        context_window = st.select_slider(
            "Ollama Context Window",
            options=context_values,
            value=context_values[default_idx],
            format_func=lambda x: context_labels[context_values.index(x)]
        )
        
    
    prompt = st.text_area("Summary Prompt", value=SUMMARY_PROMPT, height=120)

    if st.button("Summarize", type="primary"):
        if not url:
            st.error("Please enter a YouTube URL or local file path")
            return

        with st.spinner("Processing..."):
            try:
                with tempfile.TemporaryDirectory() as temp_dir:
                    is_local = downloader.is_local_path(url)
                    
                    if is_local:
                        file_id = hashlib.md5(str(Path(url).resolve()).encode()).hexdigest()[:12]
                        metadata = {}
                        transcript = transcriber.load_cached_transcript(file_id)
                        
                        st.markdown(f"**File: {Path(url).name}**")
                        
                        if transcript:
                            if not include_timestamps:
                                import re
                                transcript = re.sub(r'\[\d+\.\d+s - \d+\.\d+s\] ', '', transcript)
                            st.info(f"📄 Using cached transcript (length: {len(transcript)} chars)")
                        else:
                            with st.status("Extracting audio...", expanded=True) as status:
                                progress_bar = st.progress(0, text="Extracting audio...")
                                audio_path, metadata = downloader.extract_audio_from_file(url, temp_dir)
                                progress_bar.progress(1.0, text="Audio extracted")
                                status.update(label="Audio extracted", state="complete")

                            with st.status("Transcribing with Whisper...", expanded=True) as status:
                                progress_bar = st.progress(0, text="Loading model...")
                                transcript, progress_gen = transcriber.transcribe_audio_progress(audio_path, whisper_model)
                                for p in progress_gen:
                                    progress_bar.progress(p["progress"], text=p["text"])
                                with open(transcriber.get_cache_path(file_id), encoding="utf-8") as f:
                                    transcript = f.read()
                                status.update(label=f"Transcription complete ({len(transcript)} chars)", state="complete")
                    else:
                        metadata = downloader.get_video_metadata(url)
                        video_id = metadata['id']
                        thumbnail_url = f"https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg"

                        duration_sec = metadata.get('duration', 0)
                        minutes, seconds = divmod(duration_sec, 60)
                        hours, minutes = divmod(minutes, 60)
                        duration_str = f"{hours}h {minutes}m {seconds}s" if hours else f"{minutes}m {seconds}s"

                        view_count = metadata.get('view_count', 0)
                        view_str = f"{view_count:,}" if view_count else "N/A"

                        upload_date = metadata.get('upload_date', '')
                        if upload_date and len(upload_date) == 8:
                            upload_date = f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:]}"

                        col_thumb, col_info = st.columns([1, 1.2])
                        with col_thumb:
                            st.image(thumbnail_url, use_container_width=True)
                        with col_info:
                            st.markdown(f"**{metadata.get('title', 'N/A')}**")
                            st.markdown(f"*{metadata.get('channel', 'N/A')}*")
                            st.markdown(f"Duration: {duration_str} ♦ Views: {view_str}")
                            if upload_date:
                                st.markdown(f"Uploaded: {upload_date}")

                        transcript = transcriber.load_cached_transcript(metadata['id'])

                        if transcript:
                            if not include_timestamps:
                                import re
                                transcript = re.sub(r'\[\d+\.\d+s - \d+\.\d+s\] ', '', transcript)
                            st.info(f"📄 Using cached transcript (length: {len(transcript)} chars)")
                        else:
                            youtube_tried = False
                            whisper_tried = False
                            
                            if use_youtube_transcript:
                                with st.status("Fetching YouTube transcript...", expanded=True) as status:
                                    transcript, status_msg = transcript_fetcher.fetch_youtube_transcript(url)
                                    if transcript:
                                        transcriber.save_transcript(metadata['id'], transcript)
                                        status.update(label=f"YouTube transcript: {status_msg}", state="complete")
                                        st.info(f"📄 Using YouTube transcript: {status_msg} (length: {len(transcript)} chars)")
                                        youtube_tried = True
                                    else:
                                        status.update(label=f"YouTube transcript unavailable: {status_msg}", state="error")
                                        st.warning(f"YouTube transcript unavailable: {status_msg}")
                            
                            if not transcript and use_whisper:
                                whisper_tried = True
                                with st.status("Downloading audio...", expanded=True) as status:
                                    progress_bar = st.progress(0, text="Starting download...")
                                    audio_path, metadata, download_progress = downloader.download_audio_progress(url, temp_dir)
                                    for p in download_progress:
                                        progress_bar.progress(p["progress"], text=p["text"])
                                    status.update(label="Audio downloaded", state="complete")

                                with st.status("Transcribing with Whisper...", expanded=True) as status:
                                    progress_bar = st.progress(0, text="Loading model...")
                                    transcript, progress_gen = transcriber.transcribe_audio_progress(audio_path, whisper_model)
                                    for p in progress_gen:
                                        progress_bar.progress(p["progress"], text=p["text"])
                                    with open(transcriber.get_cache_path(metadata['id']), encoding="utf-8") as f:
                                        transcript = f.read()
                                    status.update(label=f"Transcription complete ({len(transcript)} chars)", state="complete")
                            
                            if not transcript:
                                if not youtube_tried and not whisper_tried:
                                    st.error("No transcript source available. Enable YouTube or Whisper in settings.")
                                else:
                                    st.error("Could not get a transcript, exitting.")
                                return

                    if not include_timestamps:
                        import re
                        transcript_no_ts = re.sub(r'\[\d+\.\d+s - \d+\.\d+s\] ', '', transcript)
                        if transcript_no_ts != transcript:
                            st.info(f"📄 Timestamps removed (length: {len(transcript_no_ts)} chars)")
                            transcript = transcript_no_ts

                    with st.status("Generating summary with Ollama...", expanded=True) as status:
                        progress_bar = st.progress(0.0, text="Generating summary...")
                        try:
                            summary = summarizer.summarize_text(transcript, prompt, ollama_model, metadata, context_window)
                            progress_bar.progress(1.0, text="Complete")
                            status.update(label="Summary generated", state="complete")
                        except Exception as e:
                            progress_bar.progress(1.0, text="Error")
                            status.update(label=f"Error: {str(e)}", state="error")
                            st.error(str(e))
                            return

                    st.subheader("Summary")
                    st.write(summary)

            except Exception as e:
                st.error(f"Error: {str(e)}")


if __name__ == "__main__":
    run_ui()
