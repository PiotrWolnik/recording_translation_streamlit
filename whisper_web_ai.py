import streamlit as st
import whisper
from languages import supported_languages
from deep_translator import GoogleTranslator
import wave
import speech_recognition as sr

import librosa
import soundfile as sf

class TranslateWords:
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
    
    def translate_full_audio(self) -> str:
        model = whisper.load_model("base")
        transcription = model.transcribe(self.audio)
        return TranslateWords(transcription["text"], self.language_to_translate_to).getResult()

    def translate_part_of_the_audio(self, starting_point: float, ending_point: float) -> str:
        recognizer = sr.Recognizer()
        with sr.AudioFile(self.audio) as source:
            audio_data = recognizer.record(source, offset=starting_point,duration=ending_point)
            transcription = recognizer.recognize_google(audio_data)
        return TranslateWords(transcription, self.language_to_translate_to).getResult()

def get_duration_wave(file_path):
    x,_ = librosa.load(file_path, sr=16000)
    sf.write('tmp.wav', x, 16000)
    wave.open('tmp.wav','r')
    with wave.open('tmp.wav', 'r') as audio_file:
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
    choice = st.text_input('Choose duration of video [beginning-end] (in seconds) or leave it as it is.', f'0-{time_of_whole_vid}')

if st.sidebar.button("Transcribe Audio"):
    if audio_file is not None:
        recording_translator = TranslateRecording(supported_languages[destination_language], audio_file.name)
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
st.sidebar.audio(audio_file)