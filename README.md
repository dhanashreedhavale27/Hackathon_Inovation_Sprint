# NexaBot - Multi-Modal AI Document Scanner & Chatbot

NexaBot is a highly polished, premium Streamlit application that acts as a Multi-Modal AI Agent. It leverages the Google Gemini API to scan documents, images, and other files, allowing you to ask questions about your documents or conduct general AI chatbot queries.

## ✨ Features

- **Futuristic UI/UX**: Custom Glassmorphic Dark Theme with vibrant gradients, glowing typography, clean UI cards, and responsive micro-animations.
- **Multi-Modal Native Parsing**: Supports uploading and parsing of multiple file formats:
  - **Images** (`.png`, `.jpg`, `.jpeg`, `.webp`): Passed directly to Gemini's vision core for visual chart interpretation, handwriting scanning, and diagram explanation.
  - **PDFs** (`.pdf`): Passed natively to Gemini for structural document understanding, maintaining table layout and visual features.
  - **DOCX / TXT / CSV**: Extracted locally and injected into the contextual prompt window.
- **Smart Agent Routing**: An autonomous agent mode that automatically decides whether the user's question requires querying the uploaded documents or answering from general knowledge.
- **Model Selection**: Switch dynamically between `gemini-1.5-flash` (for fast iterations) and `gemini-1.5-pro` (for deep analytical reasoning).
- **Session Continuity**: Retains your scanned knowledge base and chat history while enabling clean sidebar-triggered resets.

---

## 🛠️ Setup Instructions

### 1. Prerequisites
Make sure you have **Python 3.10+** installed on your system.

### 2. Install Dependencies
Install the required packages using pip:
```bash
pip install -r requirements.txt
```

### 3. Configure API Key (Optional)
You can create a `.env` file in the project root to pre-fill your Gemini API Key:
```env
GEMINI_API_KEY=your_actual_api_key_here
```
Otherwise, you can easily type it into the sidebar secure text field when you start the application.

---

## 🚀 Running the App

Start the Streamlit application using python module runner:

```bash
python -m streamlit run app.py
```

This will spin up a local development server and automatically open the app in your default web browser (usually at `http://localhost:8501`).

---

## 📂 Supported Formats
- **PDF Documents** (`.pdf`): Read natively using Gemini PDF processing.
- **Word Documents** (`.docx`): Read using paragraph and table extractors.
- **Spreadsheets / Text Data** (`.csv`, `.txt`): Standard structured text parsing.
- **Images** (`.png`, `.jpg`, `.jpeg`, `.webp`): Vision-based visual scanning.
