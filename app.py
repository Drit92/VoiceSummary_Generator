import streamlit as st
import speech_recognition as sr
from transformers import pipeline
import os
import soundfile as sf
import tempfile

# Initialize Llama-based summarizer pipeline from Hugging Face
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

# Streamlit page configuration
st.set_page_config(page_title="Lecture Voice-to-Notes Generator", layout="centered")

# Title and Description
st.title("Lecture Voice-to-Notes Generator")
st.write("""
    Welcome to the Lecture Voice-to-Notes Generator! 
    This tool will transcribe your lecture audio and summarize the content into clear notes, quizzes, and flashcards.
""")

# File uploader for audio input (lecture)
audio_file = st.file_uploader("Upload Your Lecture Audio", type=["wav", "mp3", "m4a"])

# Audio transcription function using SpeechRecognition
def transcribe_audio(audio_file):
    recognizer = sr.Recognizer()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmpfile:
        tmpfile.write(audio_file.read())
        tmpfile.close()

        # Use SpeechRecognition to transcribe the uploaded audio file
        audio = sr.AudioFile(tmpfile.name)
        with audio as source:
            audio_data = recognizer.record(source)
            try:
                # Perform speech-to-text using Google's API (can be replaced with a different model)
                transcript = recognizer.recognize_google(audio_data)
                return transcript
            except sr.UnknownValueError:
                return "Sorry, we could not understand the audio."
            except sr.RequestError:
                return "There was an error with the speech-to-text service."

# Function to generate study notes using summarization
def generate_study_notes(transcript):
    summary = summarizer(transcript, max_length=250, min_length=50, do_sample=False)
    return summary[0]['summary_text']

# Display the uploaded file's transcription and generate notes
if audio_file:
    st.audio(audio_file, format="audio/wav")
    st.write("Transcribing the lecture...")

    transcript = transcribe_audio(audio_file)
    st.write("### Lecture Transcript")
    st.write(transcript)

    if len(transcript) > 50:  # Only summarize if the transcript is long enough
        st.write("### Summarized Study Notes")
        notes = generate_study_notes(transcript)
        st.write(notes)

        # Optional: Generate quizzes or flashcards from notes
        if st.button("Generate Quiz"):
            st.write("### Quiz Generated from Notes")
            quiz = f"Create a quiz based on these notes: {notes}"
            st.write(quiz)
        if st.button("Generate Flashcards"):
            st.write("### Flashcards Generated")
            flashcards = f"Create flashcards based on these notes: {notes}"
            st.write(flashcards)

# Feedback Section (Logging)
st.write("### Feedback and Suggestions")
feedback = st.text_area("Provide any feedback here:")
if st.button("Submit Feedback"):
    st.write("Thank you for your feedback!")
