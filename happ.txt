import streamlit as st
import speech_recognition as sr
from transformers import pipeline
import soundfile as sf
import tempfile
from pydub import AudioSegment
import os

st.set_page_config(page_title="Lecture Voice-to-Notes Generator", layout="centered")

# Load summarizer
@st.cache_resource
def load_summarizer():
    return pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")

summarizer = load_summarizer()

st.title("Lecture Voice-to-Notes Generator")
st.write("""
Upload a lecture recording, and this app will transcribe it into text and generate summarized notes.
""")

audio_file = st.file_uploader("Upload Lecture Audio", type=["wav", "mp3", "m4a"])

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
            return "Speech recognition service is unavailable."

def generate_study_notes(text):
    result = summarizer(text, max_length=250, min_length=50, do_sample=False)
    return result[0]['summary_text']

if audio_file:
    st.audio(audio_file)
    st.info("Processing your audio. Please wait...")

    wav_path = convert_to_wav(audio_file)
    transcript = transcribe_audio(wav_path)

    st.subheader("Lecture Transcript")
    st.write(transcript)

    if len(transcript) > 50:
        st.subheader("Summarized Study Notes")
        summary = generate_study_notes(transcript)
        st.write(summary)

        if st.button("Generate Quiz"):
            st.write("Quiz based on notes:")
            st.write(f"Create a quiz using: {summary}")

        if st.button("Generate Flashcards"):
            st.write("Flashcards based on notes:")
            st.write(f"Create flashcards using: {summary}")

st.write("### Feedback")
feedback = st.text_area("Provide feedback here:")
if st.button("Submit Feedback"):
    st.write("Thank you for your feedback!")
