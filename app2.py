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
def load_quiz_generator():
    return pipeline("text2text-generation", model="koshkosh/quiz-generator")

@st.cache_resource
def load_flashcard_generator():
    # This model is a question generation model suitable for flashcards question prompts
    return pipeline("text2text-generation", model="vblagoje/bert-quiz-question-generator")

summarizer = load_summarizer()
quiz_generator = load_quiz_generator()
flashcard_generator = load_flashcard_generator()

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
    # Generate quiz questions from notes
    result = quiz_generator(notes, max_length=512, do_sample=False)
    return result[0]['generated_text']

def generate_flashcards(notes):
    # Generate flashcard questions from notes
    result = flashcard_generator(notes, max_length=512, do_sample=False)
    return result[0]['generated_text']

with st.form("upload_form"):
    audio_file = st.file_uploader("Upload audio file (wav, mp3, m4a)", type=["wav", "mp3", "m4a"])
    submit = st.form_submit_button("Process Audio")

if submit and audio_file:
    with st.spinner("Processing audio, please wait..."):
        try:
            wav_path = convert_to_wav(audio_file)
            transcript = transcribe_audio(wav_path)
            os.remove(wav_path)

            st.subheader("Lecture Transcript")
            st.write(transcript)

            if len(transcript) > 50:
                notes = generate_study_notes(transcript)
                st.subheader("Summarized Study Notes")
                st.write(notes)

                # Buttons to generate quizzes and flashcards
                if st.button("Generate Quiz"):
                    with st.spinner("Generating quiz..."):
                        quiz_text = generate_quiz(notes)
                        st.subheader("Quiz Questions")
                        st.write(quiz_text)

                if st.button("Generate Flashcards"):
                    with st.spinner("Generating flashcards..."):
                        flashcards_text = generate_flashcards(notes)
                        st.subheader("Flashcards Questions")
                        st.write(flashcards_text)
            else:
                st.info("Transcript is too short to summarize.")
        except Exception as e:
            st.error(f"Error during processing: {e}")

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
