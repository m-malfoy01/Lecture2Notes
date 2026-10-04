import streamlit as st
from google import genai
from gtts import gTTS
import fitz  # PyMuPDF
from PIL import Image
import io
import os
import re

# Page configuration
st.set_page_config(
    page_title="Lecture2Notes", 
    page_icon="📚", 
    layout="centered"
)

# Load CSS stylesheet
def load_css(file_name):
    if os.path.exists(file_name):
        with open(file_name) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css("style.css")

# Initialize session state variables
if "lecture_text" not in st.session_state:
    st.session_state.lecture_text = ""
if "uploaded_image" not in st.session_state:
    st.session_state.uploaded_image = None
if "pdf_images" not in st.session_state:
    st.session_state.pdf_images = []

# Header Section
st.markdown("### 📚 Lecture2Notes")
st.title("Visual Notes & Audio Briefs")
st.markdown("*Upload typed PDFs, scanned handwritten notes, text files, or photo snaps to generate visual cheat sheets and audio summaries.*")

# Sidebar Configuration
with st.sidebar:
    st.header("Settings")
    api_key_input = st.text_input("Gemini API Key:", type="password", placeholder="AIzaSy...")
    st.markdown("---")
    st.info("💡 **Study Tip:** Whether it's a typed syllabus or messy handwritten lecture notes in a PDF/photo, our multimodal AI reads and structures everything instantly.")

# Main Dashboard Container
col1, col2 = st.columns([2, 1], gap="medium")

with col1:
    uploaded_file = st.file_uploader("📂 Upload slides, text, or handwritten notes", type=["pdf", "txt", "png", "jpg", "jpeg"])

with col2:
    st.markdown("#### ✨ Features")
    st.markdown("- Handwritten OCR (PDF & Images)\n- Visual Cheat Sheets\n- Expert Audio Brief")

# Process uploaded file using PyMuPDF and PIL
if uploaded_file is not None:
    file_name_lower = uploaded_file.name.lower()
    
    # Handle PDF files (Digital text OR Scanned/Handwritten pages)
    if file_name_lower.endswith(".pdf") or uploaded_file.type == "application/pdf":
        try:
            pdf_bytes = uploaded_file.read()
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            
            extracted_text = ""
            pdf_pages_as_images = []
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()
                if text:
                    extracted_text += text + "\n"
                
                pix = page.get_pixmap(dpi=150)
                img = Image.open(io.BytesIO(pix.tobytes("png")))
                pdf_pages_as_images.append(img)
            
            st.session_state.lecture_text = extracted_text
            st.session_state.pdf_images = pdf_pages_as_images
            st.session_state.uploaded_image = None
            
            if extracted_text.strip():
                st.success(f"✅ Loaded Digital PDF: {uploaded_file.name} ({len(doc)} pages)")
            else:
                st.warning(f"⚠️ Loaded Scanned/Handwritten PDF: {uploaded_file.name} ({len(doc)} pages). Our vision AI will process the handwriting!")
                
        except Exception as e:
            st.error(f"Error reading PDF: {e}")
    
    # Handle Text files
    elif file_name_lower.endswith(".txt") or uploaded_file.type == "text/plain":
        st.session_state.lecture_text = uploaded_file.read().decode("utf-8")
        st.session_state.pdf_images = []
        st.session_state.uploaded_image = None
        st.success(f"✅ Loaded Text File: {uploaded_file.name}")
    
    # Handle Image files (PNG, JPG, JPEG)
    elif file_name_lower.endswith((".png", ".jpg", ".jpeg")) or uploaded_file.type in ["image/png", "image/jpeg", "image/jpg"]:
        st.session_state.uploaded_image = Image.open(uploaded_file)
        st.session_state.lecture_text = ""
        st.session_state.pdf_images = []
        st.image(st.session_state.uploaded_image, caption="Uploaded Notes Preview", use_container_width=True)
        st.success(f"✅ Loaded Image: {uploaded_file.name}")

st.markdown("---")

generate_btn = st.button("Generate Visual Notes & Audio Brief", type="primary")

if generate_btn:
    if not api_key_input:
        st.error("⚠️️ Please enter your Gemini API Key in the sidebar settings first.")
    elif not st.session_state.lecture_text and not st.session_state.pdf_images and st.session_state.uploaded_image is None:
        st.warning("⚠️ Please upload a document or handwritten note before generating.")
    else:
        try:
            client = genai.Client(api_key=api_key_input)
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            status_text.text("☕ Analyzing document/handwriting and structuring notes...")
            progress_bar.progress(40)
            
            prompt = f"""
            You are an expert AI study assistant. Analyze the provided input (which could be digital text, slides, or scanned pages/photos of handwritten notes/whiteboard) and provide two distinct sections separated EXACTLY by the marker line "===SPLIT===":

            [SECTION 1: VISUAL STUDY NOTES]
            Create clean, beautiful, structured markdown study notes featuring:
            - 🔑 **Core Concepts & Definitions**
            - ⚡ **Key Formulas, Rules, or Steps**
            - 🚨 **Exam Traps to Avoid**
            - 📌 **TL;DR Summary Bullet Points**

            ===SPLIT===

            [SECTION 2: AUDIO PODCAST SCRIPT]
            Create a rapid-fire, engaging 2-person podcast dialogue script under 300 words between:
            1. **Prof. Alex** (The brilliant, concise expert)
            2. **Sam** (The student asking clarifying questions)
            Format with speaker labels like "Prof. Alex:" and "Sam:".
            """

            # Build contents list based on what was uploaded
            if st.session_state.uploaded_image is not None:
                contents = [st.session_state.uploaded_image, prompt]
            elif st.session_state.pdf_images:
                contents = st.session_state.pdf_images + [prompt]
            else:
                contents = f"{prompt}\n\nLecture Document Text:\n{st.session_state.lecture_text}"

            # Resilient model selector using current active flash models
            models_to_try = ['gemini-3.8-flash', 'gemini-3.5-flash']
            response = None
            last_error = None

            for model_name in models_to_try:
                try:
                    status_text.text(f"Connecting to AI engine ({model_name})...")
                    response = client.models.generate_content(
                        model=model_name,
                        contents=contents,
                    )
                    break
                except Exception as model_err:
                    last_error = model_err
                    continue

            if response is None:
                raise Exception(f"All model endpoints busy. Last error: {last_error}")
            
            progress_bar.progress(80)
            status_text.text("🎙️ Generating audio file...")
            
            full_response = response.text
            
            # Cleanly split and strip internal markdown tags and section headers
            if "===SPLIT===" in full_response:
                parts = full_response.split("===SPLIT===")
                visual_notes = parts[0].replace("[SECTION 1: VISUAL STUDY NOTES]", "").strip()
                audio_script = parts[1].replace("[SECTION 2: AUDIO PODCAST SCRIPT]", "").strip()
            else:
                visual_notes = full_response
                audio_script = full_response

            # Clean up text for natural human-like speech (removes markdown asterisks, hashes, etc.)
            speech_text = audio_script
            speech_text = speech_text.replace("Prof. Alex:", "Professor Alex explains:").replace("Sam:", "Sam asks:")
            speech_text = re.sub(r'[*#_\-\U00010000-\U0010ffff]', '', speech_text)

            # Generate Audio via gTTS from the cleaned script portion only
            tts = gTTS(text=speech_text, lang='en', slow=False)
            audio_path = "brief.mp3"
            tts.save(audio_path)
            
            progress_bar.progress(100)
            status_text.text("✨ Ready!")
            progress_bar.empty()
            status_text.empty()

            # Display Results
            st.markdown("### 📝 Visual Study Sheet")
            st.markdown(f'<div class="note-box">{visual_notes}</div>', unsafe_allow_html=True)

            st.markdown("### 🎧 Accompanying Audio Brief")
            st.audio(audio_path, format='audio/mp3')

            with st.expander("📜 Read Audio Podcast Transcript", expanded=False):
                st.markdown(audio_script)

        except Exception as e:
            st.error(f"An error occurred: {e}")