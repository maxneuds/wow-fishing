import pyaudio
import numpy as np
from logger import get_logger

logger = get_logger("Analyzer")

CHUNK = 4096
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
FILTER_VOLUME_THRESHOLD = 1000
FILTER_FREQ = [500, 3000]

def start_analyzer():
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
    
    logger.info("Listening... Press Ctrl+C to stop.")
    
    try:
        while True:
            data = stream.read(CHUNK, exception_on_overflow=False)
            audio_data = np.frombuffer(data, dtype=np.int16)
            
            rms = np.sqrt(np.mean(np.square(audio_data.astype(np.float32))))
            
            fft_data = np.fft.rfft(audio_data)
            fft_freqs = np.fft.rfftfreq(CHUNK, 1.0/RATE)
            peak_freq = fft_freqs[np.argmax(np.abs(fft_data))]
            
            logger.debug(f"Volume: {rms:8.2f} | Peak Frequency: {peak_freq:8.0f} Hz")
            if rms > FILTER_VOLUME_THRESHOLD and FILTER_FREQ[0] <= peak_freq <= FILTER_FREQ[1]:
                logger.info(f"Detected sound! Volume: {rms:8.2f} | Peak Frequency: {peak_freq:8.0f} Hz")
            
    except KeyboardInterrupt:
        logger.info("\nStopping analyzer.")
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()

if __name__ == "__main__":
    start_analyzer()