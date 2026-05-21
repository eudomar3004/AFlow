import io
import os
from groq import Groq
from config import GROQ_MODEL, WHISPER_LANGUAGE


class Transcriber:
    def __init__(self):
        self._client: Optional[Groq] = None

    def _client_instance(self) -> Groq:
        if self._client is None:
            key = os.getenv("GROQ_API_KEY", "")
            if not key:
                raise ValueError("GROQ_API_KEY no configurada")
            self._client = Groq(api_key=key, timeout=10.0)
        return self._client

    def transcribe(self, wav_buffer: io.BytesIO) -> str:
        wav_buffer.seek(0)
        data = wav_buffer.read()
        if len(data) < 100:
            return ""
        result = self._client_instance().audio.transcriptions.create(
            file=("audio.wav", data),
            model=GROQ_MODEL,
            language=WHISPER_LANGUAGE,
            response_format="text",
            temperature=0.0,
        )
        text = result if isinstance(result, str) else str(result)
        return text.strip()
