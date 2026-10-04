# 📚 Lecture2Notes: Midnight Edition

Lecture2Notes is an emergency study assistant designed to transform dense academic materials, messy handwritten notes, and slide decks into bite-sized, high-retention formats instantly. Built for rapid studying and hackathon presentations.

## ✨ Core Features
- **Multimodal Ingestion:** Supports digital PDFs, scanned text, image snapshots, and handwritten whiteboards using Gemini's vision capabilities.
- **Visual Cheat Sheets:** Automatically parses and structures core concepts, definitions, formulas, and exam traps into a clean markdown layout.
- **Expert Audio Briefs:** Generates engaging, natural-sounding 2-person podcast audio summaries using `gTTS` to help you review on the go.
- **Midnight Study Studio UI:** A polished, distraction-free dark-mode interface built with Streamlit and custom CSS.

## 🚀 Tech Stack
- **Frontend & UI:** Streamlit, Custom CSS
- **AI Engine:** Google Gemini API (`gemini-flash` models)
- **Document & Audio Processing:** PyMuPDF (`fitz`), Google Text-to-Speech (`gTTS`), Pillow
