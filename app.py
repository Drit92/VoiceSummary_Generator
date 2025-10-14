import streamlit as st
import speech_recognition as sr
from transformers import pipeline
import tempfile
import os

st.set_page_config(page_title="Lightweight Voice-to-Notes", layout="centered")

@st.cache_resource(show_spinner=False)
def load_summarizer():
    # Small summarization model for speed and low resource usage
    return pipeline("summarization", model="sshleifer/distilbart-cnn-6-6")

@st.cache_resource(show_spinner=False)
def load_text_generator():
    # Use t5-small for lightweight generation
    return pipeline("text2text-generation", model="t5-small", tokenizer="t5-small")

summarizer = load_summarizer()
text_generator = load_text_generator()

st.title("Lightweight Lecture Voice-to-Notes Generator")

def transcribe_audio(file_path):
    recognizer = sr.Recognizer()
    with sr.AudioFile(file_path) as source:
        audio_data = recognizer.record(source)
        try:
            return recognizer.recognize_google(audio_data)
        except:
            return "Audio not understood"

with st.form("upload_form"):
    audio_file = st.file_uploader("Upload WAV audio (to avoid conversion overhead)", type=["wav"])
    submit = st.form_submit_button("Process Audio")

if submit and audio_file:
    with st.spinner("Transcribing and summarizing..."):
        # Save uploaded wav to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(audio_file.read())
            tmp_path = tmp.name

        transcript = transcribe_audio(tmp_path)
        os.remove(tmp_path)

        st.subheader("Transcript")
        st.write(transcript)

        if len(transcript) > 50:
            summary = summarizer(transcript, max_length=150, min_length=30, do_sample=False)[0]['summary_text']
            st.subheader("Summary")
            st.write(summary)

            if st.button("Generate Quiz"):
                prompt = f"generate quiz questions: {summary}"
                quiz = text_generator(prompt, max_length=128, do_sample=False)[0]['generated_text']
                st.subheader("Quiz Questions")
                st.write(quiz)

            if st.button("Generate Flashcards"):
                prompt = f"generate flashcards: {summary}"
                flashcards = text_generator(prompt, max_length=128, do_sample=False)[0]['generated_text']
                st.subheader("Flashcards")
                st.write(flashcards)
        else:
            st.info("Transcript too short for summarization.")
