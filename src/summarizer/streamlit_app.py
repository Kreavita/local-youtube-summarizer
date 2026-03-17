import streamlit as st
import tempfile
import os

try:
    from . import downloader, transcriber, summarizer
    from .config import SUMMARY_PROMPT, WHISPER_MODEL, OLLAMA_MODEL
except ImportError:
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from summarizer import downloader, transcriber, summarizer
    from summarizer.config import SUMMARY_PROMPT, WHISPER_MODEL, OLLAMA_MODEL


def run_ui():
    st.set_page_config(page_title="Video Summarizer", page_icon="🎬")
    st.title("🎬 Video Summarizer")

    url = st.text_input("YouTube URL", placeholder="https://youtube.com/watch?v=...")

    col1, col2 = st.columns(2)
    with col1:
        whisper_model = st.selectbox(
            "Whisper Model",
            ["tiny", "base", "small", "medium", "large-v3-turbo", "large-v3", "turbo"],
            index=4,
            help="Size of Whisper model for transcription"
        )
    with col2:
        ollama_model = st.text_input("Ollama Model", value=OLLAMA_MODEL)

    prompt = st.text_area("Summary Prompt", value=SUMMARY_PROMPT, height=80)

    if st.button("Summarize", type="primary"):
        if not url:
            st.error("Please enter a YouTube URL")
            return

        with st.spinner("Processing..."):
            try:
                with tempfile.TemporaryDirectory() as temp_dir:
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
                        st.info(f"📄 Using cached transcript (length: {len(transcript)} chars)")
                    else:
                        with st.status("Downloading audio...", expanded=True) as status:
                            progress_bar = st.progress(50, text="Downloading...")
                            audio_path, metadata = downloader.download_audio(url, temp_dir)
                            progress_bar.progress(100, text="Download complete")
                            status.update(label="Audio downloaded", state="complete")

                        with st.status("Transcribing with Whisper...", expanded=True) as status:
                            progress_bar = st.progress(0, text="Loading model...")
                            transcript, progress_gen = transcriber.transcribe_audio_progress(audio_path, whisper_model)
                            for p in progress_gen:
                                progress_bar.progress(p["progress"], text=p["text"])
                            with open(transcriber.get_cache_path(metadata['id']), encoding="utf-8") as f:
                                transcript = f.read()
                            status.update(label=f"Transcription complete ({len(transcript)} chars)", state="complete")

                    with st.status("Generating summary with Ollama...", expanded=True) as status:
                        progress_bar = st.progress(0.0, text="Generating summary...")
                        summary = summarizer.summarize_text(transcript, prompt, ollama_model, metadata)
                        progress_bar.progress(1.0, text="Complete")
                        status.update(label="Summary generated", state="complete")

                    st.subheader("Summary")
                    st.write(summary)

            except Exception as e:
                st.error(f"Error: {str(e)}")


if __name__ == "__main__":
    run_ui()
