import streamlit as st
import warnings
warnings.filterwarnings("ignore", category=SyntaxWarning)
import speech_recognition as sr
from transformers import pipeline
import tempfile
from pydub import AudioSegment
import os

# Streamlit Cloud optimized config
st.set_page_config(
    page_title="Lecture Voice-to-Notes", 
    page_icon="🎤",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ULTRA-LIGHT models for Streamlit Cloud (under 1GB total)
@st.cache_resource
def load_summarizer():
    """Lightweight summarizer for Streamlit Cloud"""
    return pipeline("summarization", model="t5-small")

@st.cache_resource
def load_qa_generator():
    """Lightweight QA generator for quizzes"""
    return pipeline("text2text-generation", model="google/flan-t5-small")

# Initialize models
try:
    summarizer = load_summarizer()
    qa_generator = load_qa_generator()
    st.success("✅ Models loaded successfully!")
except Exception as e:
    st.error(f"Model loading failed: {e}")
    st.stop()

st.title("🎤 Lecture Voice-to-Notes Generator")
st.markdown("**Streamlit Cloud Optimized** - Works offline with lightweight AI models!")

# Sidebar instructions
with st.sidebar:
    st.markdown("### 📋 How to use:")
    st.markdown("""
    1. **Upload** audio (WAV, MP3, M4A)
    2. **Click Process** 
    3. Get **transcript → notes → quiz/flashcards**
    """)
    st.markdown("---")
    st.caption("🆓 No API keys • No quotas • Private")

# File uploader
audio_file = st.file_uploader(
    "📁 Upload Lecture Audio", 
    type=["wav", "mp3", "m4a", "m4b"],
    help="Supports WAV, MP3, M4A up to 5 minutes"
)

# Audio processing functions
def process_audio(audio_file):
    """Convert uploaded audio to WAV for speech recognition"""
    # Save uploaded file temporarily
    temp_input = tempfile.NamedTemporaryFile(delete=False, suffix=".tmp")
    temp_input.write(audio_file.getvalue())
    temp_input.flush()
    
    # Convert to WAV (16kHz mono for best recognition)
    temp_wav = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    audio = AudioSegment.from_file(temp_input.name)
    audio = audio.set_frame_rate(16000).set_channels(1)
    audio.export(temp_wav.name, format="wav")
    
    # Cleanup
    os.unlink(temp_input.name)
    return temp_wav.name

def transcribe_audio(file_path):
    """Transcribe using Google Speech Recognition (free tier)"""
    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(file_path) as source:
            # Adjust for ambient noise
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio_data = recognizer.record(source, duration=30000)  # 30s max
            text = recognizer.recognize_google(audio_data)
            return text
    except sr.UnknownValueError:
        return "Could not understand audio. Try shorter/clearer clips."
    except sr.RequestError as e:
        return f"Speech service error: {str(e)}"
    except Exception as e:
        return f"Transcription error: {str(e)}"

def generate_summary(text):
    """Generate concise summary"""
    if len(text) < 30:
        return "Transcript too short for summarization."
    try:
        result = summarizer(text, max_length=150, min_length=30, do_sample=False)
        return result[0]['summary_text']
    except:
        # Fallback summary
        sentences = text.split('. ')
        return '. '.join(sentences[:3]) + "..."

def generate_quiz(notes):
    """Generate quiz questions"""
    prompt = f"Create 3 quiz questions from: {notes}"
    try:
        result = qa_generator(prompt, max_length=200, num_return_sequences=1)
        return result[0]['generated_text']
    except:
        return f"""
**Quiz Questions:**
1. What is the main topic discussed?
2. Name 2-3 key points from the lecture.
3. What is the most important takeaway?

**Answer using:** {notes[:200]}...
        """

def generate_flashcards(notes):
    """Generate flashcard pairs"""
    sentences = notes.split('. ')
    flashcards = []
    for i, sent in enumerate(sentences[:4], 1):
        question = sent[:60] + "..." if len(sent) > 60 else sent
        flashcards.append(f"**Q{i}:** {question}\n**A{i}:** {sent.strip()}")
    return "\n\n".join(flashcards)

# Main app logic
if audio_file is not None:
    # Show uploaded audio
    st.audio(audio_file)
    
    # Initialize session state
    if 'transcript' not in st.session_state:
        st.session_state.transcript = ""
        st.session_state.summary = ""
        st.session_state.quiz = ""
        st.session_state.flashcards = ""
    
    # Process button
    col1, col2, col3 = st.columns([2, 1, 1])
    with col2:
        if st.button("🚀 Process Audio", type="primary", use_container_width=True):
            with st.spinner("🔄 Converting audio..."):
                wav_path = process_audio(audio_file)
            
            with st.spinner("🎙️ Transcribing..."):
                st.session_state.transcript = transcribe_audio(wav_path)
                os.unlink(wav_path)  # Cleanup
            
            if len(st.session_state.transcript) > 30:
                with st.spinner("✍️ Generating summary..."):
                    st.session_state.summary = generate_summary(st.session_state.transcript)
            st.rerun()
    
    with col3:
        if st.button("🗑️ Clear", use_container_width=True):
            for key in st.session_state.keys():
                del st.session_state[key]
            st.rerun()
    
    # Results section
    if st.session_state.transcript:
        # Full transcript
        st.subheader("📄 Full Transcript")
        st.text_area(
            "transcript", 
            st.session_state.transcript, 
            height=150, 
            disabled=True
        )
        
        if st.session_state.summary:
            # Summary/notes
            st.subheader("📝 Study Notes")
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                        color: white; padding: 20px; border-radius: 15px; 
                        box-shadow: 0 10px 30px rgba(0,0,0,0.2);">
                <h3 style="margin: 0 0 15px 0;">📚 Key Points</h3>
                {st.session_state.summary}
            </div>
            """, unsafe_allow_html=True)
            
            # Action buttons
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.button("❓ Generate Quiz", use_container_width=True):
                    with st.spinner("Generating quiz..."):
                        st.session_state.quiz = generate_quiz(st.session_state.summary)
                    st.rerun()
            
            with col_btn2:
                if st.button("🃏 Flashcards", use_container_width=True):
                    with st.spinner("Creating flashcards..."):
                        st.session_state.flashcards = generate_flashcards(st.session_state.summary)
                    st.rerun()
            
            # Quiz results
            if st.session_state.quiz:
                st.subheader("🧠 Quiz")
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); 
                            color: white; padding: 20px; border-radius: 15px; 
                            box-shadow: 0 10px 30px rgba(0,0,0,0.2);">
                    {st.session_state.quiz}
                </div>
                """, unsafe_allow_html=True)
            
            # Flashcard results
            if st.session_state.flashcards:
                st.subheader("📚 Flashcards")
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); 
                            color: white; padding: 20px; border-radius: 15px; 
                            box-shadow: 0 10px 30px rgba(0,0,0,0.2);">
                    {st.session_state.flashcards}
                </div>
                """, unsafe_allow_html=True)

else:
    st.info("👆 Upload an audio file and click 'Process Audio' to get started!")
    st.balloons()

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    ✅ <strong>Offline AI</strong> • No quotas • No API keys • Private processing
</div>
""", unsafe_allow_html=True)
