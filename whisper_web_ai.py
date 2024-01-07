import streamlit as st
import whisper
from languages import supported_languages
from deep_translator import GoogleTranslator
import speech_recognition as sr
import audioread
from pydub import AudioSegment
import librosa
import soundfile as sf
from io import BytesIO
import io
from typing import Union, AnyStr, Optional
import numpy as np
from streamlit.runtime.uploaded_file_manager import UploadedFile
import os
from subprocess import Popen, PIPE
from pathlib import Path

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

class AudioWidget:
    __default_extensions = [
        ".wav", ".aac",
        ".ogg", ".mp3",
        ".aiff", ".flac",
        ".ape", ".dsd",
        ".mqa", ".wma",
        ".m4a"
    ]

    __common_extensions = [
        "wav", "mp3",
        "ogg", "flac"
    ]

    def __init__(self,
                 min_duration: Optional[int] = None,
                 max_duration: Optional[int] = None,
                 available_formats: Optional[str] = None,
                 convert_to: Optional[str] = "wav",
                 sample_rate: Optional[int] = 22050,
                 mono: Optional[bool] = True,
                 common_extensions: Optional[list[str,]] = None,
                 ac: Optional[int] = 1
                 ):
        if not available_formats:
            available_formats = self.__default_extensions
        if not isinstance(common_extensions, list):
            common_extensions = self.__common_extensions
        self.common_extensions = common_extensions
        self.convert_to = convert_to
        self.ac = ac
        self.root_dir = os.getcwd()
        self.available_formats = available_formats
        self.min_duration = min_duration if min_duration else 0
        self.max_duration = max_duration if max_duration else int(60e+3)
        self.sample_rate = sample_rate
        self.mono = mono

    def _safe_load(self, data: io.BytesIO) -> tuple[np.ndarray, int]:
        return librosa.load(data, sr=self.sample_rate, mono=self.mono)

    def __check_duration(self, data: bytes) -> tuple[np.ndarray, int]:
        audio, sr = librosa.load(io.BytesIO(data), sr=None)
        duration = librosa.get_duration(y=audio, sr=sr)
        if (duration >= self.min_duration) and (duration <= self.max_duration):
            return self._safe_load(io.BytesIO(data))
        if duration > self.max_duration:
            st.error(
                f"Oops! Length of the heartbeat audio recording "
                f"must be less than {self.max_duration} seconds, "
                f"but the length is {round(duration, 2)} seconds. "
                f"Please try again.",
                icon="😮"
            )
        if duration < self.min_duration:
            st.error(
                f"Oops! Length of the heartbeat audio recording "
                f"must be at least {self.min_duration} seconds, "
                f"but the length is {round(duration, 2)} seconds. "
                f"Please try again.",
                icon="😮"
            )
    def convert(self, path: str | Path) -> AnyStr:
        return Popen(
            ["ffmpeg", "-hide_banner", "-i", f"{path}", "-f", f"{self.convert_to}", "-"],
            stdout=PIPE
        ).stdout.read()

    def check_extension(self, filename: str | Path) -> Union[None, str]:
        if filename.split(".")[-1] not in self.common_extensions:
            return filename

    def define_location(self, file_id: str, extension: str) -> str:
        return os.path.join(self.root_dir, f"{file_id}.{extension}")
    
    def __call__(self, source: UploadedFile) -> bytes | AnyStr:
        data = source.getvalue()
        if not self.check_extension(source.name):
            return data
        else:
            in_path = self.define_location(source.file_id, source.name.split(".")[-1])
            try:
                self.write(in_path, source.getbuffer())
                data = self.convert(in_path)
            except Exception as e:
                st.error(f"We're sorry, something happened to the server ⚡️ \n{e}")
            else:
                return data
            finally:
                if os.path.exists(in_path):
                    os.remove(in_path)

    def load_audio(self) -> Union[bytes, None]:
        data = st.file_uploader(
            label=f"Upload an audio file of your heartbeat "
                    f"that more or equal {self.min_duration} and "
                    f"less or equal {self.max_duration} seconds.",
            type=self.available_formats
        )
        if data:
            st.audio(data)
            data = self.__call__(data)
            return self.__check_duration(data)

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