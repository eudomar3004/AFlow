import io
import wave
import queue
import time
from typing import Optional

import numpy as np
import sounddevice as sd

from config import SAMPLE_RATE, CHANNELS, AUDIO_DTYPE, BLOCK_SIZE


class AudioRecorder:
    def __init__(self):
        self.audio_queue: queue.Queue = queue.Queue()
        self._frames: list[np.ndarray] = []
        self._stream: Optional[sd.InputStream] = None
        self._start_time: float = 0.0

    def _callback(self, indata: np.ndarray, frames: int, time_info, status):
        chunk = indata.copy()
        self.audio_queue.put(chunk)
        self._frames.append(chunk)

    def start(self):
        self._frames.clear()
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except queue.Empty:
                break
        self._start_time = time.time()
        self._stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype=AUDIO_DTYPE,
            blocksize=BLOCK_SIZE,
            callback=self._callback,
        )
        self._stream.start()

    def stop(self) -> float:
        duration = time.time() - self._start_time
        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None
        return duration

    def get_wav_buffer(self) -> io.BytesIO:
        if not self._frames:
            return io.BytesIO()
        audio = np.concatenate(self._frames, axis=0)
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(2)
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(audio.tobytes())
        buf.seek(0)
        return buf

    def get_duration(self) -> float:
        if not self._frames:
            return 0.0
        total = sum(f.shape[0] for f in self._frames)
        return total / SAMPLE_RATE
