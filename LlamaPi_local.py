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
from LlamaPi import LlamaPiBase

logging.basicConfig(
    format='%(asctime)s [%(levelname)s] %(filename)s:%(funcName)s: %(message)s',
    level=logging.DEBUG,
    handlers=[
        logging.StreamHandler()  # Output logs to stdout
    ]
)

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def split_into_sentences(resp):
    # Split the response into sentences.
    parts = re.split(r'([.;:!?])\s*', resp)

    # Separators will be in the list at odd indices, sentences at even indices
    separators = [parts[i] for i in range(1, len(parts), 2)]
    logging.debug(f"separators: {separators}")

    # Remove empty strings from the list
    # sentences = [s for s in sentences if s]
    sentences = [parts[i] for i in range(0, len(parts), 2) if parts[i]]
    logging.debug(f"sentences: {sentences}")
    
    # Append the separators to the back of each sentence, might be better for TTS.
    for i in range(len(sentences)):
        # Just to be safe... there should be same # of seperators and sentences.
        if i < len(separators):
            sentences[i] += separators[i]
    
    return sentences

class LlamaPi(LlamaPiBase):

    def __init__(self):
        super().__init__()
        self.LLM_PORT = 8000
        self.llm_server_process = None
        self.llm_server_config_file = 'server_config.json'
        self.chat_history = []

    def cleanup(self):
        super().cleanup()
        # Additional cleanup: kill the local LLM server process.
        if self.llm_server_process:
            logging.info("killing the LLM server")
            self.llm_server_process.kill()

    def process_partial_response(self, resp: str, cur_idx: int):
        sentences = split_into_sentences(resp) 
        logging.debug(f"sentences: {sentences}")

        # The last sentence might be incomplete
        if(cur_idx > len(sentences)-1): return 0, None, None

        num_processed = 0
        cmd = None
        # sentences_processed = []
        for s in sentences[cur_idx:-1]:
            if "$" in s:
                cmd =  s.split("$")[-1]
                s = s.split("$")[:-1]
                s = ' '.join(s)
                logging.debug(f"Command (might be partial): {cmd}")
            # sentences_processed.append(s)
            # append_to_text_box(f"{s}\n")
            if len(s) > 0: self.speak_back(s)
            num_processed += 1
        
        return cur_idx + num_processed, cmd, sentences

    def launch_llm(self):
        if not is_port_in_use(self.LLM_PORT):
            logging.info("Launching LLM server")
            # from llm_server import launch_llama_cpp_server
            # self.llm_server_thread = threading.Thread(target=launch_llama_cpp_server).start()
            # time.sleep(20)
            cmd_line = f"{sys.executable} -m llama_cpp.server --config_file {self.llm_server_config_file}"
            self.llm_server_process = subprocess.Popen(cmd_line, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            logging.info(f"LLM server process: {self.llm_server_process.pid}")
            while True:
                if self.llm_server_process.stderr.readable():
                    output_line = self.llm_server_process.stderr.readline().decode()
                    if len(output_line) > 0:
                        print(output_line, end="")
                        if 'Uvicorn running on' in output_line:
                            logging.info("LLM server successfully started")
                            break
        else:
            logging.info("LLM server already launched on port {}".format(self.LLM_PORT))
    
    # Overrides the `prepare_llm` method in base class.
    def prepare_llm(self):
        self.launch_llm()
        self.llm_client = OpenAI(
            base_url=f"http://127.0.0.1:8000/v1",
            api_key = "sk-no-key-required"
        )
        # Warmup so we don't wait long time to prefill the system prompt.
        self.llm("what is your name?", warmup=True)
    
    # Overrides the `llm` method in base class.
    def llm(self, request, warmup=False) -> str:

        if len(request) < 4:
            logging.info("request empty or too short")
            return

        # print("========== HISTORY ==========")
        # for h in chat_history:
        #     print(h)
        # print("========== END OF HISTORY ==========")
        # Send the query to LLM.
        messages = [ self.system_msg ]
        # Uncomment this to include chat history
        messages.extend(self.chat_history)
        messages.append({"role": "user", "content": request})
        completion = self.llm_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages = messages,
            stream=True,
            # temperature = 0.6,
        )
        # print("LLM response: ")
        # print("=========================")
        # acc = ""
        resp = ""
        # stop_tts = False
        sentences = []
        sentences_idx = 0
        cmd = None
        if not warmup: self.append_to_text_box("Skyler: ")
        for chunk in completion:
            txt = chunk.choices[0].delta.content
            resp += txt or ""
            if txt is None:
                time.sleep(0.05)
            elif warmup:
                # Do nothing
                logging.info(f"WARMING UP, IGNORE OUTPUT {txt}")
            else:
                self.append_to_text_box(txt)
                sentences_idx, cmd, sentences = self.process_partial_response(resp, sentences_idx)
        
        # Process the remaining sentences, but skip the command word.
        for s in sentences[sentences_idx:]:
            if "$" in s:
                cmd = s.split("$")[-1]
                s = s.split("$")[:-1]
                s = ' '.join(s)
            self.speak_back(s)
            if cmd: break
        
        if cmd:
            logging.info(f"Command word: {cmd}")
            self.append_to_text_box(f"\nCommand: {cmd}\n")

        # Save the response in history
        if not warmup:
            self.chat_history.append({"role": "user", "content": request})
            self.chat_history.append({"role": "assistant", "content": resp})
            # Restrict the history to 2 rounds
            if len(self.chat_history) > 4:
                self.chat_history = self.chat_history[2:]
        # print("========== END OF RESPONSE ==========")

        return cmd

if __name__ == "__main__":
    LlamaPi().start()
