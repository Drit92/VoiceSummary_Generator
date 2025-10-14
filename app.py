import streamlit as st
import speech_recognition as sr
from transformers import pipeline
from pydub import AudioSegment
import tempfile
import datetime
import os

st.set_page_config(page_title="Lecture Voice-to-Notes Generator", layout="centered")

@st.cache_resource
def load_summarizer():
    return pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")

@st.cache_resource
def load_text_generator():
    return pipeline("text2text-generation", model="t5-base", tokenizer="t5-base")

summarizer = load_summarizer()
text_generator = load_text_generator()

st.title("Lecture Voice-to-Notes Generator")
st.write("""
Upload your lecture audio recording, transcribe it, summarize notes, and generate quizzes and flashcards!
""")

def convert_to_wav(uploaded_file):
    temp_input = tempfile.NamedTemporaryFile(delete=False)
    temp_input.write(uploaded_file.read())
    temp_input.flush()

    temp_output = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    audio = AudioSegment.from_file(temp_input.name)
    audio.export(temp_output.name, format="wav")
    return temp_output.name

def transcribe_audio(file_path):
    recognizer = sr.Recognizer()
    with sr.AudioFile(file_path) as source:
        audio_data = recognizer.record(source)
        try:
            return recognizer.recognize_google(audio_data)
        except sr.UnknownValueError:
            return "Sorry, could not understand the audio."
        except sr.RequestError:
            return "Speech recognition service unavailable."

def generate_study_notes(text):
    result = summarizer(text, max_length=250, min_length=50, do_sample=False)
    return result[0]['summary_text']

def generate_quiz(notes):
    prompt = f"generate quiz questions: {notes}"
    result = text_generator(prompt, max_length=512, do_sample=False)
    return result[0]['generated_text']

def generate_flashcards(notes):
    prompt = f"generate flashcards: {notes}"
    result = text_generator(prompt, max_length=512, do_sample=False)
    return result[0]['generated_text']

# Initialize session state variables
if "transcript" not in st.session_state:
    st.session_state.transcript = None
if "notes" not in st.session_state:
    st.session_state.notes = None
if "quiz" not in st.session_state:
    st.session_state.quiz = None
if "flashcards" not in st.session_state:
    st.session_state.flashcards = None

with st.form("upload_form"):
    audio_file = st.file_uploader("Upload audio file (wav, mp3, m4a)", type=["wav", "mp3", "m4a"])
    submit = st.form_submit_button("Process Audio")

if submit and audio_file:
    with st.spinner("Processing audio, please wait..."):
        try:
            wav_path = convert_to_wav(audio_file)
            transcript = transcribe_audio(wav_path)
            os.remove(wav_path)

            st.session_state.transcript = transcript
            st.session_state.notes = None
            st.session_state.quiz = None
            st.session_state.flashcards = None

        except Exception as e:
            st.error(f"Error during processing: {e}")
            st.session_state.transcript = None
            st.session_state.notes = None
            st.session_state.quiz = None
            st.session_state.flashcards = None

if st.session_state.transcript:
    st.subheader("Lecture Transcript")
    st.write(st.session_state.transcript)

    if len(st.session_state.transcript) > 50:

        if st.session_state.notes is None:
            with st.spinner("Generating study notes..."):
                notes = generate_study_notes(st.session_state.transcript)
                st.session_state.notes = notes

        st.subheader("Summarized Study Notes")
        st.write(st.session_state.notes)

        # Buttons to generate quiz and flashcards
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Generate Quiz"):
                with st.spinner("Generating quiz questions..."):
                    st.session_state.quiz = generate_quiz(st.session_state.notes)
        with col2:
            if st.button("Generate Flashcards"):
                with st.spinner("Generating flashcards..."):
                    st.session_state.flashcards = generate_flashcards(st.session_state.notes)

        if st.session_state.quiz:
            st.subheader("Quiz Questions")
            st.write(st.session_state.quiz)

        if st.session_state.flashcards:
            st.subheader("Flashcards")
            st.write(st.session_state.flashcards)

    else:
        st.info("Transcript is too short to summarize.")

st.write("### Feedback and Suggestions")
feedback = st.text_area("Provide any feedback here:")
if st.button("Submit Feedback"):
    if feedback.strip():
        try:
            with open("feedback_log.txt", "a") as f:
                f.write(f"{datetime.datetime.now()}: {feedback}\n")
            st.success("Thank you for your feedback!")
        except Exception as e:
            st.error(f"Failed to save feedback: {e}")
    else:
        st.warning("Please enter feedback before submitting.")
