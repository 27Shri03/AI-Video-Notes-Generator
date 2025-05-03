import streamlit as st
import re
import time
from threading import Thread, Event
from queue import Queue
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
    return " ".join(segment['text'] for segment in transcript)

def preprocess_transcript(text: str) -> str:
    no_timestamps = re.sub(r'<\d{2}:\d{2}:\d{2}\.\d{3}>', '', text)
    no_caption_tags = re.sub(r'</?c>', '', no_timestamps)
    no_artifacts = re.sub(r'\[.*?\]', '', no_caption_tags)
    return re.sub(r'\s+', ' ', no_artifacts).strip()

def check_word_limit(text: str) -> tuple[int, int]:
    word_count = len(text.split())
    return word_count, max(0, word_count - WORD_LIMIT)

def main():
    # Initialize session state
    if 'summary_notes' not in st.session_state:
        st.session_state.summary_notes = None
    if 'show_summary' not in st.session_state:
        st.session_state.show_summary = False

    st.set_page_config(
        page_title="AI Video Summarizer",
        page_icon="🧠",
        layout="centered",
        initial_sidebar_state="expanded"
    )
    
    st.markdown("""
    <style>
        .reportview-container { background: #f8f9fa; }
        .stTextInput input { border: 2px solid #dee2e6; border-radius: 8px; padding: 8px 12px; }
        .stButton button { background: #4f46e5; color: white; border-radius: 8px; padding: 10px 24px; transition: all 0.3s; }
        .stButton button:hover { background: #4338ca; transform: scale(1.05); }
    </style>
    """, unsafe_allow_html=True)

    st.title("🎬 AI-Powered Video Summary Generator")
    st.markdown("---")
    
    with st.sidebar:
        st.header("Settings")
        word_limit = st.number_input("Word Limit", min_value=500, max_value=10000, value=WORD_LIMIT)
    
    url = st.text_input("Enter YouTube Video URL:", placeholder="https://youtube.com/watch?v=...")
    
    if st.button("🚀 Generate Summary"):
        if not url:
            st.warning("Please enter a valid YouTube URL")
            return
            
        try:
            with st.status("🔄 Processing Pipeline", expanded=True) as status:
                st.write("🔍 Extracting Transcript...")
                 
                with st.spinner("Downloading subtitles..."):
                    raw_text = get_full_transcript(url)
                 
                st.write(f"✅ Retrieved {len(raw_text)} characters")
                 
                st.write("🧹 Cleaning Text...")
                cleaned_text = preprocess_transcript(raw_text)
                st.write(f"📝 Final text length: {len(cleaned_text)} characters")
                 
                st.write("⚖️ Checking Word Limit...")
                word_count, excess = check_word_limit(cleaned_text)
                st.write(f"ℹ️ Total words: {word_count}/{word_limit}")
                if word_count > word_limit:
                    st.error(f"⚠️ Exceeds limit by {excess} words")
                    return
                
                status.update(
                    label="Processing Complete!",
                    state="complete",
                    expanded=False
                )
            st.subheader("Processed Transcript")
            with st.expander("View Cleaned Text"):
                st.markdown(
                    f'<div style="height: 300px; overflow-y: auto;">'
                    f'{cleaned_text}'
                    f'</div>',
                    unsafe_allow_html=True
                )
            

            with st.status("🧠 Generating AI Summary...", expanded=True) as gen_status:
                # Generation setup
                start_time = time.time()
                timer_placeholder = st.empty()
                stop_event = Event()
                timer_queue = Queue()

                # Timer thread
                def timer_update():
                    while not stop_event.is_set():
                        timer_queue.put(time.time() - start_time)
                        time.sleep(0.1)
                        
                Thread(target=timer_update, daemon=True).start()

                # Model generation
                notes = ""
                def generate_wrapper():
                    nonlocal notes
                    notes, _ = generate_notes(cleaned_text)
                    
                model_thread = Thread(target=generate_wrapper, daemon=True)
                model_thread.start()

                # UI updates
                while model_thread.is_alive():
                    try:
                        elapsed = timer_queue.get_nowait()
                        timer_placeholder.markdown(f"⏱️ **Generation time:** {elapsed:.1f} seconds")
                    except:
                        pass
                    time.sleep(0.1)

                # Cleanup
                stop_event.set()
                model_thread.join()
                gen_status.update(label=f"Summary Generated in {time.time()-start_time:.2f}s!", state="complete")

            # Store results
            st.session_state.summary_notes = notes
            st.session_state.show_summary = True

        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

    # Always show summary if available
    if st.session_state.show_summary and st.session_state.summary_notes:
        st.subheader("AI Summary")
        st.markdown(st.session_state.summary_notes)
        st.download_button(
            label="📥 Download Summary",
            data=st.session_state.summary_notes,
            file_name="video_summary.md",
            key="download_summary"
        )

    st.markdown("---")
    st.caption("Made with ❤️ using Streamlit | Powered by DeepseekR1")

if __name__ == "__main__":
    main()