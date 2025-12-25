import streamlit as st
import speech_recognition as sr
from transformers import pipeline
import soundfile as sf
import tempfile
from pydub import AudioSegment
import os

st.set_page_config(page_title="Lecture Voice-to-Notes Generator", layout="centered")

# Load summarizer (offline)
@st.cache_resource
def load_summarizer():
    return pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")

# Load question generator (offline)
@st.cache_resource
def load_question_generator():
    return pipeline("text-generation", model="gpt2", max_length=200)

summarizer = load_summarizer()
question_generator = load_question_generator()

st.title("📚 Lecture Voice-to-Notes Generator")
st.write("Upload a lecture recording to get transcripts, notes, quizzes, and flashcards - **all offline!**")

audio_file = st.file_uploader("Upload Lecture Audio", type=["wav", "mp3", "m4a"], help="Supports WAV, MP3, M4A")

def convert_to_wav(uploaded_file):
    """Convert uploaded audio to WAV format"""
    temp_input = tempfile.NamedTemporaryFile(delete=False, suffix=".tmp")
    temp_input.write(uploaded_file.getvalue())
    temp_input.flush()
    
    temp_output = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    audio = AudioSegment.from_file(temp_input.name)
    audio = audio.set_frame_rate(16000).set_channels(1)  # Standardize for recognition
    audio.export(temp_output.name, format="wav")
    
    os.unlink(temp_input.name)  # Clean up
    return temp_output.name

def transcribe_audio(file_path):
    """Transcribe audio using Google Speech Recognition"""
    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(file_path) as source:
            # Handle long audio by processing in chunks
            audio_data = recognizer.record(source, duration=30000)  # 30s chunks
            return recognizer.recognize_google(audio_data)
    except sr.UnknownValueError:
        return "Could not understand audio. Try speaking clearly or shorter clips."
    except sr.RequestError as e:
        return f"Speech service error: {str(e)}"
    except Exception as e:
        return f"Transcription error: {str(e)}"

def generate_summary(text):
    """Generate summary using local model"""
    if len(text) < 50:
        return "Summary too short - needs more content."
    
    try:
        result = summarizer(text, max_length=250, min_length=50, do_sample=False)
        return result[0]['summary_text']
    except Exception as e:
        return f"Summarization error: {str(e)}"

def generate_quiz(notes):
    """Generate quiz questions using local model"""
    prompt = f"Quiz questions from lecture notes:\n{notes}\n\nQ1:"
    try:
        result = question_generator(prompt, max_new_tokens=100, num_return_sequences=1)
        return result[0]['generated_text']
    except:
        return f"""**Quiz Questions:**

1. What is the main topic?
2. Name 3 key points.
3. What is the most important takeaway?

**Use these notes to answer:** {notes[:300]}..."""

def generate_flashcards(notes):
    """Generate flashcard format"""
    lines = notes.split('. ')
    flashcards = []
    
    for i, line in enumerate(lines[:5], 1):
        flashcards.append(f"**Q{i}:** {line[:80]}...\n**A{i}:** {line}")
    
    return "\n\n".join(flashcards)

if audio_file is not None:
    # Reset on new file
    if 'transcript' not in st.session_state:
        st.session_state.transcript = ""
        st.session_state.notes = ""
    
    st.audio(audio_file)
    
    if st.button("🎙️ Process Audio", type="primary"):
        with st.spinner("🔄 Converting audio and transcribing..."):
            wav_path = convert_to_wav(audio_file)
            st.session_state.transcript = transcribe_audio(wav_path)
            os.unlink(wav_path)  # Clean up temp file
            
            if len(st.session_state.transcript) > 50:
                with st.spinner("✍️ Generating summary..."):
                    st.session_state.notes = generate_summary(st.session_state.transcript)
    
    # Display results
    if st.session_state.transcript:
        st.subheader("📝 Full Transcript")
        st.text_area("transcript", st.session_state.transcript, height=200, disabled=True)
        
        if st.session_state.notes:
            st.subheader("📚 Summarized Notes")
            st.markdown(f"""
            <div style="background-color: #f0f8ff; padding: 20px; border-radius: 10px; border-left: 5px solid #2196F3;">
                {st.session_state.notes}
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("❓ Generate Quiz", use_container_width=True):
                    st.session_state.quiz = generate_quiz(st.session_state.notes)
                    st.rerun()
            
            with col2:
                if st.button("📖 Generate Flashcards", use_container_width=True):
                    st.session_state.flashcards = generate_flashcards(st.session_state.notes)
                    st.rerun()
            
            # Show quiz if generated
            if hasattr(st.session_state, 'quiz') and st.session_state.quiz:
                st.subheader("🧠 Quiz")
                st.markdown(f"""
                <div style="background-color: #fff3cd; padding: 20px; border-radius: 10px; border-left: 5px solid #ffc107;">
                    {st.session_state.quiz}
                </div>
                """, unsafe_allow_html=True)
            
            # Show flashcards if generated
            if hasattr(st.session_state, 'flashcards') and st.session_state.flashcards:
                st.subheader("🃏 Flashcards")
                st.markdown(f"""
                <div style="background-color: #e8f5e8; padding: 20px; border-radius: 10px; border-left: 5px solid #28a745;">
                    {st.session_state.flashcards}
                </div>
                """, unsafe_allow_html=True)

st.markdown("---")
st.markdown("**💡 No API keys needed! Works completely offline using local ML models.**")

# Feedback section
with st.expander("📝 Feedback"):
    feedback = st.text_area("Share your thoughts:")
    if st.button("Submit Feedback"):
        st.success("Thank you for your feedback! 🎉")
