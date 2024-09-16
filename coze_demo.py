import os
from pprint import pprint
import re
import signal
import socket
import sys
import threading
import tkinter as tk
from tkinter import scrolledtext
import pyaudio
import wave
import atexit
from faster_whisper import WhisperModel
import logging
import numpy as np
import soundfile as sf
import io
import subprocess
import opencc
from openai import OpenAI
import time
from cozewrapper import CozeBotWrapper

logging.basicConfig(
    format='%(asctime)s [%(levelname)s] %(filename)s:%(funcName)s: %(message)s',
    level=logging.DEBUG,
    handlers=[
        logging.StreamHandler()  # Output logs to stdout
    ]
)

# Check if we are running on Raspberry Pi
try:
    import RPi.GPIO as GPIO
except ImportError:
    running_on_rpi = False
else:
    running_on_rpi = True

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

class LlamaPi:
    # PyAudio configurations
    AUDIO_FORMAT = pyaudio.paInt16  # Use 16-bit integer format
    AUDIO_CHANNELS = 1  # Mono channel
    SAMPLE_RATE = 16000  # Sample rate of 16000 Hz
    AUDIO_CHUNK = 1024  # Chunk size to read audio data (64KB)
    TEMP_WAV_FILE = "temp.wav"

    # GPIO button
    GPIO_BUTTON = 8
    button_pressed = False

    # Handler of the audio device
    audio = None
    audio_data = []
    audio_recording_thread = None

    asr_model = None
    t2s_converter = opencc.OpenCC('t2s')

    bot = None

    robot_arm = None

    def record_audio(self):
        logging.info("start recording")
        self.audio_data.clear()

        if not self.audio:
            logging.error("Audio device not present")
            return

        # Open stream to default mic
        stream = self.audio.open(format=self.AUDIO_FORMAT,
                            channels=self.AUDIO_CHANNELS,
                            rate=self.SAMPLE_RATE,
                            input=True,
                            frames_per_buffer=self.AUDIO_CHUNK)

        while self.button_pressed:
            try:
                data = stream.read(self.AUDIO_CHUNK)
                self.audio_data.append(data)
                self.canvas.update_idletasks()
            except KeyboardInterrupt:
                break

        logging.info("received signal, recording stopped")
        stream.stop_stream()
        stream.close()

    def say(self, text, lang='en'):
        # Create a subprocess to run the 'say' command
        args = ['say']
        if lang.startswith('en'):
            args.extend(['-v', 'Samantha'])
        elif lang.startswith('zh'):
            args.extend(['-v', 'Tingting'])
            text = self.t2s_converter.convert(text)
        else:
            logging.info("Unknown language: {}".format(lang))
            return

        logging.info(f"Speaking back: {text} in language {lang}")
        p = subprocess.Popen(args, stdin=subprocess.PIPE)
        p.stdin.write(text.encode('utf-8'))
        p.stdin.flush()
        p.stdin.close()
        p.wait()

    def piper(self, text, lang='en'):
        # Create a subprocess to run the 'say' command
        piper_args = ['./tts/piper/piper']
        if lang.startswith('en'):
            piper_args.extend(['-m', './tts/voices/en_US-amy-medium.onnx'])
            # piper_args.extend(['-m', './tts/voices/en_US-amy-low.onnx'])
        elif lang.startswith('zh'):
            # piper_args.extend(['-m', './tts/voices/zh_CN-huayan-medium.onnx', '--sentence_silence', '0.5'])
            # piper_args.extend(['-m', './tts/voices/zh_CN-huayan-x_low.onnx'])
            piper_args.extend(['-m', './tts/voices/zh_CN-huayan-medium.onnx'])
            text = self.t2s_converter.convert(text)
        else:
            logging.info("Unknown language: {}".format(lang))
            return

        piper_args.extend(['--output-raw'])

        logging.info(f"Speaking back: {text} in language {lang}")
        piper_process = subprocess.Popen(piper_args, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        aplay_process = subprocess.Popen(['aplay', '-r', '22050', '-f', 'S16_LE', '-t', 'raw', '-'], stdin=piper_process.stdout)
        # Close the stdout of the piper process in the parent process so that it knows no one else will write to it
        piper_process.stdout.close()
        piper_process.stdin.write(text.encode('utf-8'))
        piper_process.stdin.close()  # Close the stdin to signal no more data will be sent
        # Wait for the piper process to finish
        piper_process.wait()
        # Wait for the aplay process to finish
        aplay_process.wait()
    
    def speak_back(self, text, lang='en'):
        logging.debug(f"speak ({lang}): {text}")
        if len(text) == 0:
            logging.error("empty utterance")
            return
        if running_on_rpi:
            self.piper(text, lang)
        else:
            self.say(text, lang)

    def append_to_text_box(self, txt):
        self.text_box.config(state=tk.NORMAL)
        self.text_box.insert(tk.END, txt)
        self.text_box.see(tk.END)
        self.text_box.config(state=tk.DISABLED)
        self.text_box.update_idletasks()
        # self.text_box.update()
        self.canvas.update_idletasks()
    
    def save_audio(self):
        if len(self.audio_data) == 0:
            logging.error("No audio data to save")
            return None

        logging.debug(f"Saving recorded audio to temporary file {self.TEMP_WAV_FILE}")
        # Save recorded audio data to .wav file
        filename = self.TEMP_WAV_FILE
        wavefile = wave.open(filename, 'wb')
        wavefile.setnchannels(self.AUDIO_CHANNELS)
        wavefile.setsampwidth(self.audio.get_sample_size(self.AUDIO_FORMAT))
        wavefile.setframerate(self.SAMPLE_RATE)
        wavefile.writeframes(b''.join(self.audio_data))
        wavefile.close()
        return filename

    def transcribe_audio(self):
        if not self.save_audio():
            logging.error("Audio file not saved")
            return None
        
        if not self.asr_model:
            print("No ASR model, skip transcribing")
            return None

        print("Transcribing audio")
        segments, info = self.asr_model.transcribe(self.TEMP_WAV_FILE, beam_size=5)
        logging.info("Detected language '%s' with probability %f" % (info.language, info.language_probability))
        transcript = ""
        self.append_to_text_box("\nUser: ")
        for segment in segments:
            logging.info("[%.2fs -> %.2fs] %s" % (segment.start, segment.end, segment.text))
            transcript += segment.text
            self.append_to_text_box(f"{segment.text}")
            # Test: speak back
            # speak_back(segment.text, info.language)
        self.append_to_text_box("\n")

        logging.info(f"Transcript: {transcript}")
        return transcript

    def record_audio_start(self, event=None):
        logging.info(f"Recording started, event={event}")
        # Change button appearance on press
        self.canvas.itemconfig(self.push_button, fill='darkblue', outline='darkblue')
        # canvas.itemconfig(text, fill='white')
        self.canvas.scale(self.push_button, 75, 75, 0.95, 0.95)  # Slightly reduce the size

        # Start recording audio in a new thread
        self.button_pressed = True
        self.audio_recording_thread = threading.Thread(target = lambda: self.record_audio()).start()

    def record_audio_stop(self, event=None):
        logging.info(f"Recording stopped, event={event}.")
        # Revert button appearance on release
        self.canvas.itemconfig(self.push_button, fill='blue', outline='white')
        # canvas.itemconfig(text, fill='white')
        self.canvas.scale(self.push_button, 75, 75, 1/0.95, 1/0.95)  # Revert the size

        # Tell the `record_audio` thread that it should stop recording
        self.button_pressed = False
        if self.audio_recording_thread:
            self.audio_recording_thread.join()
            self.audio_recording_thread = None

        transcript = self.transcribe_audio()
    
        # TODO: chain this as a callback, so we can decouple the UI to a separate class later.
        cmd = self.llm(transcript)

        if cmd and self.robot_arm and running_on_rpi:
            if "greet" in cmd:
                logging.info("ROBOT: greeting")
                self.robot_arm.greet()
            elif "smile" in cmd:
                logging.info("ROBOT: smiling")
                self.robot_arm.smile()
            elif "pat" in cmd:
                logging.info("ROBOT: patting")
                self.robot_arm.pat()
            elif "retrieve" in cmd:
                logging.info("ROBOT: retrieving")
                self.robot_arm.retrieve()
            else:
                logging.info("ROBOT: idle")


    def cleanup(self):
        logging.info("Exiting...")
        if running_on_rpi:
            GPIO.remove_event_detect(self.GPIO_BUTTON)
            GPIO.cleanup()
        self.button_pressed = False
        if self.audio_recording_thread:
            self.audio_recording_thread.join()
            self.audio_recording_thread = None
        self.audio.terminate()

    def gpio_button_event(self, ch: int):
        logging.debug(f"Button {ch} was pressed or released")
        btn_state = GPIO.input(ch)
        logging.debug(f"Button {ch} state is {btn_state}")
        if btn_state == 0:
            self.record_audio_start()
        else:
            self.record_audio_stop()

    def llm(self, request: str):

        if len(request) < 2:
            logging.info("request empty or too short")
            return
        
        if not self.bot:
            logging.info("No LLM bot available")
            return
        
        resp = self.bot.chat(request)
        cmd = None
        if resp:
            self.append_to_text_box(resp)
            cmd = resp.split("$")[-1].strip()
            voice = resp.split("$")[:-1]
            voice = ' '.join(voice)
            logging.info(f"Command word: {cmd}")
            self.append_to_text_box(f"\nCommand: {cmd}\n")
            self.speak_back(voice)

        return cmd

    def start(self):
        # Create the main window
        self.root = tk.Tk()
        self.root.title("Coze Robot")
        self.root.geometry("800x480")

        # Create a canvas to draw the round button
        self.canvas = tk.Canvas(self.root, width=150, height=150, bg='white', highlightthickness=0)
        self.canvas.pack(pady=20)

        # Draw the round button (a circle)
        self.push_button = self.canvas.create_oval(10, 10, 140, 140, fill='blue', outline='white')

        # Add text to the button
        button_text = self.canvas.create_text(75, 75, text="Hold to Talk", fill="white", font=('Helvetica', 14, 'bold'))
        
        # Create a read-only scrolled text box
        self.text_box = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, width=56, height=10, font=("Helvetica", 16))
        self.text_box.place(relx=0.5, rely=0.7, anchor=tk.CENTER)
        self.text_box.config(state=tk.DISABLED)

        if running_on_rpi:
            # Use GPIO to trigger button push events.
            GPIO.setmode(GPIO.BOARD)
            GPIO.setup(self.GPIO_BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.add_event_detect(self.GPIO_BUTTON, GPIO.BOTH, bouncetime=100)
            GPIO.add_event_callback(self.GPIO_BUTTON, lambda ch: self.gpio_button_event(ch))
            
            try:
                from robot_arm import RobotArm
                self.robot_arm = RobotArm()
            except ImportError:
                logging.error("Robot arm not available")
                self.robot_arm = None
        else:
            # If GPIO is not available, use the GUI button instead.
            # Bind the press and release events to the functions
            self.canvas.tag_bind(self.push_button, '<ButtonPress-1>', lambda ev: self.record_audio_start(ev))
            self.canvas.tag_bind(self.push_button, '<ButtonRelease-1>', lambda ev: self.record_audio_stop(ev))
            self.canvas.tag_bind(button_text, '<ButtonPress-1>', lambda ev: self.record_audio_start(ev))
            self.canvas.tag_bind(button_text, '<ButtonRelease-1>', lambda ev: self.record_audio_stop(ev))

        self.asr_model = WhisperModel("base.en")

        api_key = os.environ["COZE_APIKEY"]
        bot_id = os.environ["COZE_BOTID"]
        self.bot = CozeBotWrapper(api_key, bot_id=bot_id, user_id='12345678')

        self.audio = pyaudio.PyAudio()

        atexit.register(lambda: self.cleanup())

        self.root.mainloop()
    
if __name__ == "__main__":
    LlamaPi().start()
