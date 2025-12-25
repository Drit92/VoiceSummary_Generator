import streamlit as st
import speech_recognition as sr
import tempfile
from pydub import AudioSegment
import os
import re
import streamlit.components.v1 as components  # Only for flashcards

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
    if len(text) < 30:
        return "Transcript too short."
    
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if len(s) > 20]
    sentences.sort(key=len, reverse=True)
    summary = ' '.join(sentences[:3])
    return summary[:300] + "..." if len(summary) > 300 else summary

def generate_quiz(notes):
    sentences = [s.strip() for s in re.split(r'[.!?]+', notes) if len(s) > 15]
    quiz = []
    
    for i, sentence in enumerate(sentences[:4]):
        question = f"**Q{i+1}:** What is the key idea in: '{sentence[:70]}...'?"
        answer = f"**A{i+1}:** {sentence[:150]}..."
        quiz.append(f"{question}\n{answer}")
    
    return "**📝 Quiz (with Answers)**\n\n" + "\n\n".join(quiz)

def generate_flashcards(notes):
    """Generate flashcards with ONE-WORD answers"""
    sentences = [s.strip() for s in re.split(r'[.!?]+', notes) if len(s) > 10]
    flashcards = []
    
    for i, sentence in enumerate(sentences[:8]):  # More cards
        words = re.findall(r'\b\w+\b', sentence.lower())
        if len(words) > 4:
            # Question from first 3-4 words
            question = f"Q{i+1}: {' '.join(words[:4])}?"
            # ONE WORD answer (most frequent or key noun)
            key_words = [w for w in words[4:] if len(w) > 4]
            answer = key_words[0].upper() if key_words else "KEY"
        else:
            question = f"Q{i+1}: {sentence[:40]}?"
            answer = words[-1].upper() if words else "TERM"
        
        flashcards.append(f"Front: {question}\nBack: {answer}")
    
    return "\n\n".join(flashcards)

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
            for key in list(st.session_state.keys()):
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
        
        # 🆕 INTERACTIVE FLASHCARDS (FIXED)
if 'flashcards' in st.session_state:
    st.subheader("🃏 Interactive Flashcards")
    
    # Parse flashcards
    flashcards_text = st.session_state.flashcards.strip()
    lines = flashcards_text.splitlines()
    
    cards = []
    current_front, current_back = "", ""
    
    for line in lines:
        line = line.strip()
        if line.startswith("Front:"):
            if current_front and current_back:
                cards.append((current_front.strip(), current_back.strip()))
            current_front = line[6:]
            current_back = ""
        elif line.startswith("Back:"):
            current_back = line[5:].strip()
    
    if current_front and current_back:
        cards.append((current_front.strip(), current_back.strip()))
    
    # Generate FIXED HTML flashcards
    if cards:
        cards_html = ""
        for i, (front, back) in enumerate(cards[:8], 1):
            cards_html += f"""
            <div class="card">
              <div class="card-inner">
                <div class="card-front">
                  <span class="num">#{i}</span>
                  <div class="q">{front[:60]}{'...' if len(front)>60 else ''}</div>
                </div>
                <div class="card-back">
                  <span class="answer">{back}</span>
                </div>
              </div>
            </div>
            """
        
        html_content = f"""
        <div style="display:flex;flex-wrap:wrap;justify-content:center;gap:12px;padding:20px;background:linear-gradient(135deg,#667eea,#764ba2);border-radius:15px;">
        {cards_html}
        </div>
        <style>
        .card{{width:260px;height:160px;perspective:800px;cursor:pointer;border-radius:15px;box-shadow:0 8px 25px rgba(0,0,0,0.2);transition:transform 0.2s;}}
        .card:hover{{transform:translateY(-5px);}}
        .card-inner{{position:relative;width:100%;height:100%;transition:transform 0.6s ease;border-radius:15px;transform-style:preserve-3d;}}
        .card.flipped .card-inner{{transform:rotateY(180deg);}}
        .card-front,.card-back{{position:absolute;width:100%;height:100%;backface-visibility:hidden;border-radius:15px;padding:20px;display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;box-sizing:border-box;}}
        .card-front{{background:linear-gradient(135deg,#ffecd2 0%,#fcb69f 100%);color:#2c3e50;font-weight:500;}}
        .card-back{{background:linear-gradient(135deg,#4facfe 0%,#00f2fe 100%);color:white;transform:rotateY(180deg);}}
        .num{{position:absolute;top:10px;left:15px;font-size:14px;font-weight:700;background:rgba(255,255,255,0.9);padding:5px 10px;border-radius:20px;box-shadow:0 2px 8px rgba(0,0,0,0.1);}}
        .q{{font-size:15px;line-height:1.4;max-height:90px;overflow:hidden;padding-top:25px;}}
        .answer{{font-size:44px;font-weight:900;text-transform:uppercase;letter-spacing:4px;text-shadow:2px 2px 8px rgba(0,0,0,0.4);animation:pulse 0.5s ease-out;}}
        @keyframes pulse{{0%{{transform:scale(0.8);opacity:0;}}100%{{transform:scale(1);opacity:1;}}}}
        @media(max-width:600px){{.card{{width:90vw;max-width:300px;height:140px;}}.answer{{font-size:36px;letter-spacing:2px;}}}}
        </style>
        <script>
        document.querySelectorAll('.card').forEach((card, index) => {{
            card.addEventListener('click', () => {{
                card.classList.toggle('flipped');
            }});
        }});
        </script>
        """
        
        components.html(html_content, height=320)
    else:
        st.warning("No flashcards generated. Try longer audio.")

else:
    st.info("👆 Upload audio file to get started!")
    st.balloons()

st.markdown("---")
