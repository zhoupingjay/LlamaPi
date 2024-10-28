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
from PIL import Image, ImageTk
import google.generativeai as genai
from gemini import GeminiWrapper
from LlamaPi import LlamaPiBase

logging.basicConfig(
    format='%(asctime)s [%(levelname)s] %(filename)s:%(funcName)s: %(message)s',
    level=logging.DEBUG,
    handlers=[
        logging.StreamHandler()  # Output logs to stdout
    ]
)

class LlamaPiGemini(LlamaPiBase):

    def __init__(self):
        super().__init__()
        self.bot = None
        self.window_title = "LlamaPi Robot on Gemini"

    # Overrides the `prepare_llm` method in base class.
    def prepare_llm(self):
        self.bot = GeminiWrapper(api_key=os.environ["GEMINI_APIKEY"])
        self.bot.new_chat_session(system_inst=self.system_msg["content"])

    # Overrides the `llm` method in base class.
    def llm(self, request, warmup=False) -> str:

        if len(request) < 2:
            logging.info("request empty or too short")
            return
        
        if not self.bot:
            logging.info("No LLM bot available")
            return
        
        resp = self.bot.chat(request)
        cmd = None
        if resp:
            self.append_to_text_box("\nAssistant: ")
            # self.append_to_text_box(resp)
            cmd = resp.split("$")[-1].strip()
            voice = resp.split("$")[:-1]
            voice = ' '.join(voice)
            self.append_to_text_box(voice)
            logging.info(f"Command word: {cmd}")
            # self.append_to_text_box(f"\nCommand: {cmd}\n")
            self.speak_back(voice)

        return cmd

if __name__ == "__main__":
    LlamaPiGemini().start()
