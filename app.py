import streamlit as st
import re
import time
import asyncio
from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs
from model.model_handler import generate_notes  
from config import WORD_LIMIT

def extract_video_id(url: str) -> str:
    parsed = urlparse(url)
    if parsed.hostname == "youtu.be":
        return parsed.path[1:]
    elif "youtube.com" in parsed.hostname:
        return parse_qs(parsed.query).get("v", [None])[0]
    else:
        raise ValueError("Invalid YouTube URL")

def get_full_transcript(url: str, lang: str = 'en') -> str:
    video_id = extract_video_id(url)
    transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=[lang])
    # join *all* text segments in order
    full_text = " ".join(segment['text'] for segment in transcript)
    return full_text

def preprocess_transcript(text: str) -> str:
    """
    Cleans a YouTube VTT-like transcript string by:
      1. Removing <hh:mm:ss.mmm> timestamp tags
      2. Removing <c>…</c> caption tags
      3. Stripping out bracketed artifacts like [Music]
      4. Collapsing all whitespace to single spaces

    Returns:
      cleaned_text (str), word_count (int)
    """
    # 1) strip timestamp tags like <00:00:01.120>
    no_timestamps = re.sub(r'<\d{2}:\d{2}:\d{2}\.\d{3}>', '', text)

    # 2) strip <c>…</c> tags
    no_caption_tags = re.sub(r'</?c>', '', no_timestamps)

    # 3) strip out [Music], [Applause], etc.
    no_artifacts = re.sub(r'\[.*?\]', '', no_caption_tags)

    # 4) collapse whitespace
    cleaned = re.sub(r'\s+', ' ', no_artifacts).strip()
    return cleaned

def check_word_limit(text: str) -> tuple[int, int]:
    word_count = len(text.split())
    return word_count, max(0, word_count - WORD_LIMIT)


async def main():
    st.set_page_config(
        page_title="AI Video Summarizer",
        page_icon="🧠",
        layout="centered",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS styling
    st.markdown("""
    <style>
        .reportview-container {
            background: #f8f9fa;
        }
        .stTextInput input {
            border: 2px solid #dee2e6;
            border-radius: 8px;
            padding: 8px 12px;
        }
        .stButton button {
            background: #4f46e5;
            color: white;
            border-radius: 8px;
            padding: 10px 24px;
            transition: all 0.3s;
        }
        .stButton button:hover {
            background: #4338ca;
            transform: scale(1.05);
        }
    </style>
    """, unsafe_allow_html=True)

    st.title("🎬 AI-Powered Video Summary Generator")
    st.markdown("---")
    
    with st.sidebar:
        st.header("Settings")
        st.markdown("Configure processing parameters")
        word_limit = st.number_input("Word Limit", 
                                   min_value=500, 
                                   max_value=10000, 
                                   value=WORD_LIMIT)
    
    url = st.text_input("Enter YouTube Video URL:", 
                      placeholder="https://youtube.com/watch?v=...")
    
    if st.button("🚀 Generate Summary"):
        if not url:
            st.warning("Please enter a valid YouTube URL")
            return
            
        try:
            with st.status("🔄 Processing Pipeline", expanded=True) as status:
                st.write("🔍 Extracting Transcript...")
                start_time = time.time()
                
                with st.spinner("Downloading subtitles..."):
                    raw_text = get_full_transcript(url)
                
                st.write(f"✅ Retrieved {len(raw_text)} characters")
                
                st.write("🧹 Cleaning Text...")
                cleaned_text = preprocess_transcript(raw_text)
                st.write(f"📝 Final text length: {len(cleaned_text)} characters")
                
                st.write("⚖️ Checking Word Limit...")
                word_count, excess = check_word_limit(cleaned_text)
                st.write(f"ℹ️ Total words: {word_count}/{word_limit}")
                
                status.update(
                    label="Processing Complete!",
                    state="complete",
                    expanded=False
                )

            # Results display OUTSIDE the status block
            if word_count > word_limit:
                st.error(f"⚠️ Exceeds limit by {excess} words")
                return
                
            st.subheader("Processed Transcript")
            with st.expander("View Cleaned Text"):
                # Scrollable text container
                st.markdown(
                    f'<div style="height: 300px; overflow-y: auto;">'
                    f'{cleaned_text}'
                    f'</div>',
                    unsafe_allow_html=True
                )
            with st.status("🧠 Generating AI Summary...", expanded=True) as gen_status:
                st.write("⚙️ Loading model...")
                notes = await generate_notes(cleaned_text)  # Make main async
                
                if not notes:
                    st.error("Failed to generate summary")
                    return
                
                gen_status.update(
                    label="Summary Generated!",
                    state="complete",
                    expanded=False
                )
            
            st.session_state['summary_notes'] = notes
            
            st.subheader("AI Summary")
            st.markdown(st.session_state['summary_notes'])
            
            # Download button that uses session state
            st.download_button(
                label="📥 Download Summary",
                data=st.session_state['summary_notes'],
                file_name="video_summary.md",
                key="download_summary"  # Unique key
            )
            
        except RuntimeError as e:
            st.error(f"❌ Error: {str(e)}")
        except Exception as e:
            st.error(f"❌ Unexpected error: {str(e)}")
                
    st.markdown("---")
    st.caption("Made with ❤️ using Streamlit | Powered by yt-dlp")

if __name__ == "__main__":
    asyncio.run(main())