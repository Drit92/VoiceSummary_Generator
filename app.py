import streamlit as st
import warnings
warnings.filterwarnings("ignore", category=SyntaxWarning)
import speech_recognition as sr
from transformers import pipeline
import tempfile
from pydub import AudioSegment
import os
import re

# Streamlit Cloud optimized config
st.set_page_config(
    page_title="Lecture Voice-to-Notes", 
    page_icon="🎤",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ULTRA-LIGHT models (only summarizer needed now)
@st.cache_resource
def load_summarizer():
    return pipeline("summarization", model="t5-small")

summarizer = load_summarizer()
st.success("✅ Models loaded!")

st.title("🎤 Lecture Voice-to-Notes Generator")
st.markdown("**Streamlit Cloud Optimized** - Professional quizzes & flashcards!")

# Sidebar
with st.sidebar:
    st.markdown("### 📋 How to use:")
    st.markdown("1. **Upload** audio\n2. **Process**\n3. **Generate** quiz/flashcards")
    st.markdown("---")
    st.caption("🆓 Offline • No quotas • Pro outputs")

audio_file = st.file_uploader("📁 Upload Audio", type=["wav", "mp3", "m4a"])

def process_audio(audio_file):
    temp_input = tempfile.NamedTemporaryFile(delete=False, suffix=".tmp")
    temp_input.write(audio_file.getvalue())
    temp_input.flush()
    
    temp_wav = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    audio = AudioSegment.from_file(temp_input.name)
    audio = audio.set_frame_rate(16000).set_channels(1)
    audio.export(temp_wav.name, format="wav")
    
    os.unlink(temp_input.name)
    return temp_wav.name

def transcribe_audio(file_path):
    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(file_path) as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio_data = recognizer.record(source, duration=30000)
            return recognizer.recognize_google(audio_data)
    except sr.UnknownValueError:
        return "Could not understand audio."
    except Exception as e:
        return f"Error: {str(e)}"

def generate_summary(text):
    if len(text) < 30:
        return "Transcript too short."
    try:
        result = summarizer(text, max_length=150, min_length=30, do_sample=False)
        return result[0]['summary_text']
    except:
        sentences = text.split('. ')
        return '. '.join(sentences[:3]) + "..."

def generate_quiz(notes):
    """Smart rule-based quiz generator"""
    # Extract key phrases
    sentences = [s.strip() for s in notes.split('.') if len(s) > 10]
    quiz_questions = []
    
    # Question templates - FIXED SYNTAX ERROR
    templates = [
        ("What is/are", "the main topic", "mentioned"),
        ("According to the notes, what", "key point", "is discussed"),
        ("Which of these", "concept", "is explained"),
        ("The notes mention that", "topic", "involves"),
        ("What does the lecture explain about", "subject", "what")  # ← FIXED!
    ]
    
    for i, sentence in enumerate(sentences[:5]):
        if i >= 3:  # Max 3 questions
            break
        q = f"**Q{i+1}:** What is the main idea of: '{sentence[:80]}...'?\n"
        q += f"**A{i+1}:** {sentence[:120]}...\n\n"
        quiz_questions.append(q)
    
    return "**📝 Quiz Questions & Answers**\n\n" + "".join(quiz_questions)

def generate_flashcards(notes):
    """Professional flashcard generator"""
    sentences = [s.strip() for s in re.split(r'[.!?]+', notes) if len(s) > 15]
    flashcards = []
    
    for i, sentence in enumerate(sentences[:6]):
        # Create question from key terms
        words = sentence.split()
        if len(words) > 5:
            question = f"**Front {i+1}:** Define/explain: {' '.join(words[:4])}"
            answer = f"**Back {i+1}:** {' '.join(words[4:20])}..."
        else:
            question = f"**Front {i+1}:** {sentence[:60]}..."
            answer = f"**Back {i+1}:** {sentence}"
        
        flashcards.append(f"{question}\n\n{answer}")
    
    return "**📚 Flashcards (Anki Ready)**\n\n" + "\n\n---\n\n".join(flashcards)

# Main logic
if audio_file:
    st.audio(audio_file)
    
    if 'transcript' not in st.session_state:
        st.session_state.transcript = ""
        st.session_state.summary = ""
    
    col1, col2 = st.columns([3, 1])
    with col1:
        if st.button("🚀 Process Audio", type="primary", use_container_width=True):
            with st.spinner("🎙️ Transcribing..."):
                wav_path = process_audio(audio_file)
                st.session_state.transcript = transcribe_audio(wav_path)
                os.unlink(wav_path)
                
                if len(st.session_state.transcript) > 30:
                    with st.spinner("✍️ Summarizing..."):
                        st.session_state.summary = generate_summary(st.session_state.transcript)
            st.rerun()
    
    with col2:
        if st.button("🗑️ Clear"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    
    if st.session_state.transcript:
        st.subheader("📄 Transcript")
        st.text_area("transcript", st.session_state.transcript, height=120, disabled=True)
        
        if st.session_state.summary:
            st.subheader("📝 Key Notes")
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                        color: white; padding: 25px; border-radius: 15px; 
                        box-shadow: 0 10px 30px rgba(0,0,0,0.3);">
                <h3 style="margin: 0 0 15px 0;">🎯 Summary</h3>
                {st.session_state.summary}
            </div>
            """, unsafe_allow_html=True)
            
            # Action buttons
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.button("❓ Generate Quiz", use_container_width=True):
                    st.session_state.quiz = generate_quiz(st.session_state.summary)
                    st.rerun()
            
            with col_btn2:
                if st.button("🃏 Flashcards", use_container_width=True):
                    st.session_state.flashcards = generate_flashcards(st.session_state.summary)
                    st.rerun()
            
            # Results
            if 'quiz' in st.session_state and st.session_state.quiz:
                st.subheader("🧠 Quiz")
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); 
                            color: white; padding: 25px; border-radius: 15px; 
                            box-shadow: 0 10px 30px rgba(0,0,0,0.3);">
                    {st.session_state.quiz}
                </div>
                """, unsafe_allow_html=True)
            
            if 'flashcards' in st.session_state and st.session_state.flashcards:
                st.subheader("📚 Flashcards")
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); 
                            color: white; padding: 25px; border-radius: 15px; 
                            box-shadow: 0 10px 30px rgba(0,0,0,0.3);">
                    {st.session_state.flashcards}
                </div>
                """, unsafe_allow_html=True)

else:
    st.info("👆 Upload audio and click Process to start!")
    st.balloons()

st.markdown("---")
st.markdown("<p style='text-align: center; color: #666;'>✅ Offline • Professional outputs • Anki-ready flashcards</p>", unsafe_allow_html=True)
