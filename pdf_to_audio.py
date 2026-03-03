import streamlit as st
from pypdf import PdfReader
from gtts import gTTS
import tempfile
import os

st.set_page_config(page_title="Article to Audio", page_icon="📖")

def extract_text_from_pdf(pdf_file):
    try:
        reader = PdfReader(pdf_file)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text.replace('-\n', '').replace('\n', ' ') + " "
        return text.strip()
    except Exception as e:
        st.error(f"Error extracting text: {e}")
        return ""

def main():
    st.title("🎧 Article to Audio")
    st.markdown("Convert research papers into audiobooks.")

    language_option = st.selectbox(
        "Select Language",
        options=[("English", "en"), ("Portuguese", "pt"), ("Spanish", "es")],
        format_func=lambda x: x[0]
    )

    uploaded_file = st.file_uploader("Upload PDF File", type="pdf")

    if uploaded_file:
        with st.spinner('Processing PDF...'):
            text = extract_text_from_pdf(uploaded_file)

        if text:
            st.success(f"Text extracted successfully! ({len(text)} characters)")
            
            with st.expander("Preview extracted text"):
                st.write(text[:1000] + "...")

            if st.button("Generate Audio", type="primary"):
                if len(text) > 100000:
                    st.warning("Text is very long. Processing only the first 100,000 characters.")
                    text = text[:100000]

                try:
                    with st.spinner('Converting text to speech...'):
                        tts = gTTS(text=text, lang=language_option[1], slow=False)
                        
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
                            tts.save(fp.name)
                            temp_filename = fp.name

                        with open(temp_filename, "rb") as f:
                            audio_bytes = f.read()

                        st.audio(audio_bytes, format='audio/mp3')
                        st.download_button(
                            label="Download Audio (MP3)",
                            data=audio_bytes,
                            file_name=f"{uploaded_file.name.split('.')[0]}.mp3",
                            mime="audio/mp3"
                        )
                        
                        os.unlink(temp_filename)

                except Exception as e:
                    st.error(f"Error generating audio: {e}")
        else:
            st.error("Could not read text from this PDF.")

if __name__ == "__main__":
    main()