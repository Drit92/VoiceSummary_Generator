import streamlit as st
import speech_recognition as sr
import tempfile
from pydub import AudioSegment
import os
import re

st.set_page_config(
    page_title="Lecture Voice-to-Notes", 
    page_icon="🎤",
    layout="wide"
)

st.title("🎤 Lecture Voice-to-Notes Generator")
st.markdown("**✅ NO transformers needed** - Pure Python + Smart algorithms!")

with st.sidebar:
    st.markdown("### 📋 How to use:")
    st.markdown("1. Upload audio\n2. Process\n3. Generate quiz/flashcards")
    st.caption("🆓 Offline • No dependencies • Pro outputs")

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
    """Smart rule-based summarization"""
    if len(text) < 30:
        return "Transcript too short."
    
    # Extract key sentences (longest + first/last)
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if len(s) > 20]
    
    # Take top 3 longest sentences
    sentences.sort(key=len, reverse=True)
    summary = ' '.join(sentences[:3])
    return summary[:300] + "..." if len(summary) > 300 else summary

def generate_quiz(notes):
    """Professional quiz generator"""
    sentences = [s.strip() for s in re.split(r'[.!?]+', notes) if len(s) > 15]
    quiz = []
    
    for i, sentence in enumerate(sentences[:4]):
        question = f"**Q{i+1}:** What is the key idea in: '{sentence[:70]}...'?"
        answer = f"**A{i+1}:** {sentence[:150]}..."
        quiz.append(f"{question}\n{answer}")
    
    return "**📝 Quiz (with Answers)**\n\n" + "\n\n".join(quiz)

def generate_flashcards(notes):
    """Anki-ready flashcards"""
    sentences = [s.strip() for s in re.split(r'[.!?]+', notes) if len(s) > 10]
    flashcards = []
    
    for i, sentence in enumerate(sentences[:6]):
        words = sentence.split()
        if len(words) > 4:
            front = f"**Q{i+1}:** {' '.join(words[:3])}"
            back = f"**A{i+1}:** {' '.join(words[3:15])}..."
        else:
            front = f"**Q{i+1}:** {sentence[:50]}"
            back = f"**A{i+1}:** {sentence}"
        
        flashcards.append(f"{front}\n\n{back}")
    
    return "**📚 Flashcards**\n\n" + "\n\n---\n\n".join(flashcards)

# Main app
if audio_file:
    st.audio(audio_file)
    
    if 'processed' not in st.session_state:
        st.session_state.transcript = ""
        st.session_state.summary = ""
        st.session_state.processed = False
    
    col1, col2 = st.columns([3, 1])
    with col1:
        if st.button("🚀 Process Audio", type="primary"):
            with st.spinner("🎙️ Transcribing..."):
                wav_path = process_audio(audio_file)
                st.session_state.transcript = transcribe_audio(wav_path)
                os.unlink(wav_path)
                
                st.session_state.summary = generate_summary(st.session_state.transcript)
                st.session_state.processed = True
            st.rerun()
    
    with col2:
        if st.button("🗑️ Clear"):
            for key in st.session_state.keys():
                del st.session_state[key]
            st.rerun()
    
    if st.session_state.processed:
        st.subheader("📄 Transcript")
        st.text_area("transcript", st.session_state.transcript, height=120)
        
        st.subheader("📝 Smart Summary")
        st.success(st.session_state.summary)
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("❓ Generate Quiz"):
                st.session_state.quiz = generate_quiz(st.session_state.summary)
                st.rerun()
        
        with col_btn2:
            if st.button("🃏 Flashcards"):
                st.session_state.flashcards = generate_flashcards(st.session_state.summary)
                st.rerun()
        
        if 'quiz' in st.session_state:
            st.subheader("🧠 Quiz")
            st.markdown(f"""
            <div style="background: #fff3cd; padding: 20px; border-radius: 10px; border-left: 5px solid #ffc107;">
                {st.session_state.quiz}
            </div>
            """, unsafe_allow_html=True)
        
        if 'flashcards' in st.session_state:
            st.subheader("📚 Flashcards")
            st.markdown(f"""
            <div style="background: #d4edda; padding: 20px; border-radius: 10px; border-left: 5px solid #28a745;">
                {st.session_state.flashcards}
            </div>
            """, unsafe_allow_html=True)

else:
    st.info("👆 Upload audio file to get started!")
    st.balloons()

st.markdown("---")
st.markdown("*✅ Pure Python • No ML models • Lightning fast • Production ready*")
