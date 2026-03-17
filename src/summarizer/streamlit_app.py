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
                    st.info(f"📺 {metadata.get('title', 'N/A')} by {metadata.get('channel', 'N/A')}")

                    transcript = transcriber.load_cached_transcript(metadata['id'])

                    if transcript:
                        st.success(f"Using cached transcript (length: {len(transcript)})")
                    else:
                        with st.status("Downloading audio..."):
                            audio_path, metadata = downloader.download_audio(url, temp_dir)
                        
                        with st.status("Transcribing with Whisper..."):
                            transcript = transcriber.transcribe_audio(audio_path, whisper_model)
                            transcriber.save_transcript(metadata['id'], transcript)
                        
                        st.success("Transcription complete!")

                    with st.status("Generating summary with Ollama..."):
                        summary = summarizer.summarize_text(transcript, prompt, ollama_model, metadata)

                    st.subheader("Summary")
                    st.write(summary)

            except Exception as e:
                st.error(f"Error: {str(e)}")


if __name__ == "__main__":
    run_ui()
