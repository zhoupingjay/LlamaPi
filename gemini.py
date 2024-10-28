import logging
from pprint import pprint
import random
import time
from typing import Dict, List, Tuple
import urllib.parse
import requests
import google.generativeai as genai

logging.basicConfig(
    format='%(asctime)s [%(levelname)s] %(filename)s:%(funcName)s: %(message)s',
    level=logging.DEBUG,
    handlers=[
        logging.StreamHandler()  # Output logs to stdout
    ]
)

class GeminiWrapper:
    def __init__(self,
                 api_key: str,
                 model_name: str = "gemini-1.5-flash"):
        self.api_key = api_key
        self.system_inst = None
        self.model_name = model_name
        self.model = None
        self.generation_config = None
        self.chat_history = None
        self.chat_session = None
    
    def new_chat_session(self, system_inst: str):
        self.system_inst = system_inst

        genai.configure(api_key=self.api_key)
        # Create the model
        self.generation_config = {
            "temperature": 1,
            "top_p": 0.95,
            "top_k": 64,
            "max_output_tokens": 8192,
            "response_mime_type": "text/plain",
        }
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            generation_config=self.generation_config,
            system_instruction=self.system_inst,
        )
        self.chat_session = self.model.start_chat()

    def chat(self, message: str) -> str:
        response = self.chat_session.send_message(message)
        return response.text
