import pyaudio
import numpy as np
from logger import get_logger

logger = get_logger("Analyzer")

CHUNK = 4096
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 48000
FILTER_VOLUME_THRESHOLD = 1000
FILTER_FREQ = [500, 3000]

def start_analyzer():
    p = pyaudio.PyAudio()
    
    # List available input devices
    logger.info("Available input devices:")
    for i in range(p.get_device_count()):
        device_info = p.get_device_info_by_index(i)
        if device_info.get('maxInputChannels') > 0:
            logger.info(f"  {i}: {device_info.get('name')} (channels: {device_info.get('maxInputChannels')})")
    
    # Get default input device
    default_device = p.get_default_output_device_info()
    logger.info(f"Default input device: {default_device.get('name')} (index: {default_device.get('index')})")
    
    # Use the VB-Audio Virtual Cable output as input device
    input_device_index = 27  # CABLE Output (VB-Audio Virtual Cable)
    device_info = p.get_device_info_by_index(input_device_index)
    logger.info(f"Using input device: {device_info.get('name')} (index: {input_device_index})")
    logger.info(f"Device supports {device_info.get('maxInputChannels')} input channels, default sample rate: {device_info.get('defaultSampleRate')}")
    
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, input_device_index=input_device_index, frames_per_buffer=CHUNK)
    
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