import pvporcupine
import pyaudio
import struct
import time
import platform

ACCESS_KEY = "qMdPEHiSGDYC26v9BS3t6HCjhRx8qvtc5eCgB7HKM68/w13kueDMCw=="   # replace with your real one
KEYWORD_FILE = "jarvis.ppn"      # path to your trained wake word file

# Create porcupine instance
porcupine = pvporcupine.create(
    access_key=ACCESS_KEY,
    keyword_paths=[KEYWORD_FILE]
)

pa = pyaudio.PyAudio()
stream = pa.open(
    rate=porcupine.sample_rate,
    channels=1,
    format=pyaudio.paInt16,
    input=True,
    frames_per_buffer=porcupine.frame_length
)

print("Say: Hey Jarvis!! (listening for 10 sec)")

end_time = time.time() + 10.0
try:
    while time.time() < end_time:
        pcm = stream.read(porcupine.frame_length, exception_on_overflow=False)
        pcm_unpacked = struct.unpack_from("h" * porcupine.frame_length, pcm)

        keyword_index = porcupine.process(pcm_unpacked)
        if keyword_index >= 0:
            print("Wake phrase detected: Hey Jarvis!")

            if platform.system() == "Windows":
                import winsound
                for _ in range(2):
                    winsound.Beep(2000, 200)

            break
    else:
        print("No wake phrase detected within 10 sec.")

except KeyboardInterrupt:
    print("\nStopped by user")

finally:
    stream.close()
    pa.terminate()
    porcupine.delete()
