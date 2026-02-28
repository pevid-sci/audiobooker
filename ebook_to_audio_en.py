import streamlit as st
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import edge_tts
import asyncio
import os
import re
import io
import zipfile

# Page Config
st.set_page_config(page_title="EPUB to Audiobook Converter", page_icon="🎧")

st.title("🎧 EPUB to Audiobook Converter")
st.markdown("Convert your ebook chapters into high-quality AI voice files.")

# --- Sidebar ---
st.sidebar.header("Audio Settings")
voice_options = {
    "Portuguese (BR) - Antônio (M)": "pt-BR-AntonioNeural",
    "Portuguese (BR) - Francisca (F)": "pt-BR-FranciscaNeural",
    "English (US) - Guy (M)": "en-US-GuyNeural",
    "English (US) - Aria (F)": "en-US-AriaNeural",
    "Spanish (ES) - Alvaro (M)": "es-ES-AlvaroNeural"
}
selected_voice_label = st.sidebar.selectbox("Select Voice / Language", list(voice_options.keys()))
SELECTED_VOICE = voice_options[selected_voice_label]

rate = st.sidebar.slider("Speaking Rate", 0.5, 2.0, 1.0, 0.1)
rate_str = f"{'+' if rate >= 1 else ''}{int((rate-1)*100)}%"

def clean_html(content):
    soup = BeautifulSoup(content, 'html.parser')
    for script in soup(["script", "style"]):
        script.extract()
    return soup.get_text().strip()

def get_chapters(epub_book):
    chapters = []
    for item in epub_book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            text = clean_html(item.get_content())
            if len(text) > 400:
                soup = BeautifulSoup(item.get_content(), 'html.parser')
                title_tag = soup.find(['h1', 'h2', 'h3', 'title'])
                title = title_tag.get_text().strip() if title_tag else f"Chapter {len(chapters) + 1}"
                chapters.append({"title": title, "text": text})
    return chapters

async def generate_audio(text, voice, rate_setting):
    communicate = edge_tts.Communicate(text, voice, rate=rate_setting)
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
    return audio_data

# --- Main Interface ---
uploaded_file = st.file_uploader("Upload your .epub file", type=["epub"])

if uploaded_file:
    with open("temp_book.epub", "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    # O bloco TRY começa aqui
    try:
        book = epub.read_epub("temp_book.epub")
        chapters = get_chapters(book)
        st.success(f"Found {len(chapters)} sections.")

        # --- Bulk Actions Section (Dentro do Try) ---
        st.divider()
        st.subheader("Bulk Actions")
        
        if st.button("Prepare Full Book (.ZIP)"):
            zip_buffer = io.BytesIO()
            total_chapters = len(chapters)
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED) as zip_file:
                for i, ch in enumerate(chapters):
                    progress_bar.progress((i + 1) / total_chapters)
                    status_text.text(f"Processing chapter {i+1} of {total_chapters}...")
                    
                    audio = asyncio.run(generate_audio(ch['text'], SELECTED_VOICE, rate_str))
                    clean_name = re.sub(r'[^\w\s-]', '', ch['title']).strip().replace(' ', '_')
                    zip_file.writestr(f"{i+1:02d}_{clean_name}.mp3", audio)
            
            status_text.success("✅ All chapters processed!")
            st.download_button("⬇️ Download ZIP", data=zip_buffer.getvalue(), file_name="audiobook.zip")

        # --- Individual Chapters ---
        st.divider()
        st.subheader("Individual Chapters")
        for i, chapter in enumerate(chapters):
            with st.expander(f"📦 {i+1:02d} - {chapter['title'][:60]}"):
                if st.button(f"Generate Audio", key=f"btn_{i}"):
                    audio_bytes = asyncio.run(generate_audio(chapter['text'], SELECTED_VOICE, rate_str))
                    st.audio(audio_bytes, format="audio/mp3")
                    st.download_button("Download MP3", data=audio_bytes, file_name=f"ch_{i+1}.mp3", key=f"dl_{i}")

    except Exception as e:
        st.error(f"Error processing EPUB: {e}")
    
    finally:
        # Garante que o arquivo temporário seja deletado, dando erro ou não
        if os.path.exists("temp_book.epub"):
            os.remove("temp_book.epub")
else:
    st.info("Please upload an EPUB file to begin.")