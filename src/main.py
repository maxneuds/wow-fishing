import time
import random
import threading
import pyaudio
import numpy as np
from pynput import keyboard
from logger import get_logger

logger = get_logger("Fisherman")

# --- Configuration ---
KEY_STARTSTOP = '|'
KEY_ACTION = '\\'
DETECTION_FILTERS = {
    1: {'vol': 2000.0, 'freq_range': (500.0, 1000.0)},
    2: {'vol': 1400.0, 'freq_range': (600.0, 1500.0)}
}
WAIT_MAX = 25 # Maximum wait time to detect bobber sound in seconds

# Audio stream parameters
CHUNK = 4096
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100

# State variables
is_running = False
thread_worker = None

# Initialize the keyboard controller for sending keystrokes
py_kb = keyboard.Controller()

def wait(base_ms, mu_pct=0.10, sigma_pct=0.02):
    """
    Waits for a base duration in milliseconds, adding a randomized variance 
    calculated using a normal (Gaussian) distribution.
    """
    # Calculate mean (expected value) and standard deviation (sigma) in ms
    mu = base_ms * mu_pct
    sigma = base_ms * sigma_pct
    extra_delay = random.gauss(mu, sigma)
    total_wait_ms = (base_ms + extra_delay)
    # Enforce minimum boundary of 50% of base_ms
    min_wait_ms = base_ms * 0.5
    if total_wait_ms < min_wait_ms:
        total_wait_ms = min_wait_ms
    # Sleep for the total calculated duration
    time.sleep(total_wait_ms / 1000.0)

def interact():
    """Simulates a human-like keypress using the variance wait function."""
    logger.debug(f"Triggering action: Pressing '{KEY_ACTION}'")
    py_kb.press(KEY_ACTION)
    # Hold the key down for a brief, randomized duration (e.g., ~150ms)
    wait(150, mu_pct=0.10, sigma_pct=0.02)
    py_kb.release(KEY_ACTION)

def worker():
    """Background thread that handles the continuous audio stream and analysis."""
    logger.info("Worker started, opening audio stream...")
    p = pyaudio.PyAudio()
    # Pre-calculate the minimum volume threshold from the detection filters for performance optimization
    vol_min_detection = min(filter['vol'] for filter in DETECTION_FILTERS.values())
    is_fishing = False
    time_cast = time.time()
    try:
        while is_running:
            # Fishing start: send action key to cast the line
            # Rules:
            # - If not currently fishing, cast immediately and start monitoring
            # - If currently fishing, but more than WAIT_MAX seconds have passed since last cast, assume missed catch and recast
            time_current = time.time()
            time_elapsed = time_current - time_cast
            if not is_fishing or time_elapsed > WAIT_MAX:
                msg = "Casting line..."
                logger.info(msg)
                interact()
                is_fishing = True
                time_cast = time.time()
                # Wait a moment before starting to look for new fish
                wait(2000, mu_pct=0.10, sigma_pct=0.2)
                # Open the audio stream for listening to bobber sounds
                stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
                continue
            # Read audio data from the stream with error handling for overflow
            try:
                data = stream.read(CHUNK, exception_on_overflow=False)
            except IOError as e:
                logger.error(f"Stream error: {e}")
                continue
            audio_data = np.frombuffer(data, dtype=np.int16)
            rms = np.sqrt(np.mean(np.square(audio_data.astype(np.float32))))
            # Performance optimization: Only compute FFT if volume exceeds a certain threshold
            if rms >= vol_min_detection:
                # Compute the FFT and identify the peak frequency
                fft_data = np.fft.rfft(audio_data)
                fft_freqs = np.fft.rfftfreq(CHUNK, 1.0/RATE)
                peak_freq = fft_freqs[np.argmax(np.abs(fft_data))]
                # Check each detection filter against the current RMS and peak frequency
                for filter_id, filter_params in DETECTION_FILTERS.items():
                    vol_threshold = filter_params['vol']
                    freq_min, freq_max = filter_params['freq_range']
                    if rms >= vol_threshold and freq_min <= peak_freq <= freq_max:
                        logger.info(f"Catch sound {filter_id} detected! Vol: {rms:.2f}, Freq: {peak_freq:.0f} Hz")
                        # Reel in
                        logger.info("Reeling in...")
                        interact()
                        # Reset fishing state to wait for the next cast
                        is_fishing = False
                        # Close the audio stream to free resources before the next cast
                        stream.stop_stream()
                        stream.close()
                        # After a trigger, wait a moment
                        wait(2000, mu_pct=0.10, sigma_pct=0.2)
                        # Exit the filter loop to avoid multiple detections from the same catch sound
                        break
    except Exception as e:
        logger.error(f"Worker encountered an error: {e}")
    finally:
        is_fishing = False
        stream.stop_stream()
        stream.close()
        p.terminate()
        logger.info("Audio stream closed.")

def main():
    global is_running, thread_worker
    
    def on_press(key):
        global is_running, thread_worker
        
        # Safely extract the character from the key event
        try:
            key_char = key.char
        except AttributeError:
            key_char = None
            
        if key_char == KEY_STARTSTOP:
            if not is_running:
                logger.info(f"Starting worker thread...")
                is_running = True
                thread_worker = threading.Thread(target=worker, daemon=True)
                thread_worker.start()
                time.sleep(0.5)  # Give the worker thread a moment to start
            else:
                logger.info("Stopping worker thread. Waiting for audio to close...")
                is_running = False
                if thread_worker is not None:
                    thread_worker.join()
                thread_worker = None
                logger.info("Worker thread successfully stopped.")
                
    listener = keyboard.Listener(on_press=on_press)
    listener.start()
    
    logger.info(f"Press '{KEY_STARTSTOP}' to start or stop monitoring.")
    
    while listener.running:
        time.sleep(0.01) 

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, stopping worker thread.")
        is_running = False
        if thread_worker is not None:
            thread_worker.join()
        logger.info("Worker thread stopped. Exiting.")
        exit(0)