import streamlit as st
import whisper
from languages import supported_languages
from abc import ABC, abstractmethod
from deep_translator import GoogleTranslator
import wave
import speech_recognition as sr

class ITranslateWords(ABC):
    def __init__(self):
        super().__init__()

    @abstractmethod
    def getResult(self) -> str:
        pass

class TranslateWords(ITranslateWords):
    def __init__(self, text_to_translate: str, language_to_translate_to: str):
        super().__init__()
        self.text_to_translate = text_to_translate
        self.language_to_translate_to = language_to_translate_to
        self.result = GoogleTranslator(source='auto', 
                                target=self.language_to_translate_to).translate(self.text_to_translate)
    def getResult(self) -> str:
        return self.result


class TranslateRecording:
    def __init__(self, language_to_translate_to: str, audio: str) -> None:
        self.language_to_translate_to = language_to_translate_to
        self.audio = audio
    
    def translate_audio(self) -> str:
        model = whisper.load_model("base")
        transcription = model.transcribe(self.audio)
        return TranslateWords(transcription["text"], self.language_to_translate_to).getResult()


def get_duration_wave(file_path):
   with wave.open(file_path, 'r') as audio_file:
      frame_rate = audio_file.getframerate()
      n_frames = audio_file.getnframes()
      duration = n_frames / float(frame_rate)
      return duration

main_container = st.container()
_, center_column, _ = main_container.columns([1, 5, 1])

center_column.title("Recording Translator Option")
destination_language = center_column.selectbox(
        "Select Language",
        sorted(list(supported_languages.keys())[1:]),
        key="target_lang",
        label_visibility="hidden",
)

audio_file = st.file_uploader("Upload Audio", type=["wav", "mp3", "m4a"])


if audio_file is not None:
    time_of_whole_vid = get_duration_wave(audio_file.name)
    choice = st.number_input(f"Pick a duration of video you want to translate (in seconds) [0-{time_of_whole_vid}]")

if st.sidebar.button("Transcribe Speech"):
    if audio_file is not None:
        if choice >= time_of_whole_vid:
            recording_translator = TranslateRecording(supported_languages[destination_language], audio_file.name)
            st.sidebar.success("Transcribing Audio")
            st.markdown(recording_translator.translate_audio())
        else:
            recognizer = sr.Recognizer()
            st.sidebar.success("Transcribing Audio")
            print(audio_file.name)
            with sr.AudioFile(audio_file.name) as source:
                audio_data = recognizer.record(source, offset=0,duration=choice)
                transcription = recognizer.recognize_google(audio_data)
            st.sidebar.success("Transcribing Audio")
            st.markdown(TranslateWords(transcription, supported_languages[destination_language]).getResult())
    else:
        st.sidebar.error("Please upload an audio file")

st.sidebar.header("Play Original Audio File")
st.sidebar.audio(audio_file)