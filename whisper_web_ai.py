import streamlit as st
import whisper
from languages import supported_languages
from deep_translator import GoogleTranslator
import speech_recognition as sr
import audioread
from pydub import AudioSegment
import librosa
import AudioWidget
import soundfile as sf

class TranslateWords:
    def __init__(self, text_to_translate: str, language_to_translate_to: str, source_language: str = 'auto'):
        super().__init__()
        self.text_to_translate = text_to_translate
        self.language_to_translate_to = language_to_translate_to
        self.result = GoogleTranslator(source=source_language, 
                                target=self.language_to_translate_to).translate(self.text_to_translate)
    def getResult(self) -> str:
        return self.result


class TranslateRecording:
    def __init__(self, language_to_translate_to: str, audio: str, source_language: str = 'auto') -> None:
        self.language_to_translate_to = language_to_translate_to
        self.source_language = source_language
        self.audio = audio
    
    def translate_full_audio(self) -> str:
        model = whisper.load_model("base")
        transcription = model.transcribe(self.audio)
        return TranslateWords(transcription["text"], self.language_to_translate_to, self.source_language).getResult()

    def translate_part_of_the_audio(self, starting_point: float, ending_point: float) -> str:
        recognizer = sr.Recognizer()
        with sr.AudioFile(self.audio) as source:
            audio_data = recognizer.record(source, offset=starting_point,duration=ending_point)
            transcription = recognizer.recognize_whisper(audio_data)
        return TranslateWords(transcription, self.language_to_translate_to, self.source_language).getResult()

def get_duration_wave(file_path):
    with audioread.audio_open(file_path) as f:
        totalsec = f.duration 
    return totalsec

main_container = st.container()
_, center_column, _ = main_container.columns([1, 5, 1])

center_column.title("Recording Translator Option")
destination_language = center_column.selectbox(
        "Select Language",
        sorted(list(supported_languages.keys())[1:]),
        key="target_lang",
        label_visibility="hidden",
)

widget = AudioWidget()
audio = widget.load_audio()
if audio:
    sf.write('audio.wav', audio[0], audio[1])

time_of_whole_vid = get_duration_wave('audio.wav')
choice = st.text_input('Choose duration of video [beginning-end] (in seconds) or leave it as it is.', f'0-{time_of_whole_vid}')

if st.sidebar.button("Transcribe Audio"):
    if audio is not None:
        recording_translator = TranslateRecording(supported_languages[destination_language], 'audio.wav')
        starting_point, ending_point = [float(elem) for elem in choice.split("-")]
        sidebar = st.sidebar.success("Transcribing audio")
        if starting_point == 0.0 and ending_point >= time_of_whole_vid:
            st.markdown(recording_translator.translate_full_audio())
        else:
            st.markdown(recording_translator.translate_part_of_the_audio(starting_point, ending_point-starting_point))
        sidebar.success("Audio transcribed!")
    else:
        st.sidebar.error("Please upload an audio file")

st.sidebar.header("Play Original Audio File")
st.sidebar.audio('audio.wav')