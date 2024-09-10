import logging
from pprint import pprint
import random
import time
from typing import Dict, List, Tuple
import urllib.parse
import requests

logging.basicConfig(
    format='%(asctime)s [%(levelname)s] %(filename)s:%(funcName)s: %(message)s',
    level=logging.DEBUG,
    handlers=[
        logging.StreamHandler()  # Output logs to stdout
    ]
)

class CozeBotException(Exception):
    """
    Custom exception class for CozeBot errors.
    """

    def __init__(self, message):
        """
        Initialize the CozeBotException.

        Args:
            message (str): The error message.
        """
        super().__init__(message)
        self.message = message

    def __str__(self):
        """
        Return a string representation of the exception.

        Returns:
            str: The error message.
        """
        return self.message

class CozeBotWrapper:
    """
    A wrapper class for interacting with the Coze Bot API.
    """
    def __init__(
        self,
        api_key: str,
        bot_id: str,
        user_id: str,
        base_url: str = "https://api.coze.com/v3",
    ):
        self.api_endpoint = f"{base_url}/chat"
        self.api_key = api_key
        self.bot_id = bot_id
        self.user_id = user_id
        self.conversation_id = None

    def _send_request(self, query = None, data = None, method = 'POST'):
        """
        Sends a request to the Coze API with authentication and JSON data.
        
        Args:
            query (str): Optional query added to the URL (default: None).
            data (dict): Optional JSON payload for the request (default: None).
            method (str): Optional request method (POST or GET) to use (default: 'POST').

        Returns:
            dict: The parsed JSON response from the API.
        
        Raises:
            CozeBotException: If an error occurs during the request process.
        """
        url = self.api_endpoint + query if query else self.api_endpoint
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        try:
            if method == 'POST' or data:
                response = requests.post(url, json=data, headers=headers, timeout=10)
            else:
                response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise CozeBotException(f"An error occurred: {e}") from e

    def start_chat(self, messages: List[str], conversation_id: str = None) -> Tuple[str, str]:
        """
        Create a chat conversation with the Coze Bot.

        Args:
            messages (list): A list of message objects ("role", "content", "content_type").

        Returns:
            dict: The response from the API.

        Example (https://www.coze.com/open):
        curl --location --request POST 'https://api.coze.com/v3/chat' 
            --header 'Authorization: Bearer <API KEY>' 
            --header 'Content-Type: application/json' 
            --data-raw '{
                "bot_id": "<BOT ID>",
                "user_id": "<USER ID>",
                "stream": false,
                "auto_save_history":true,
                "additional_messages":[
                    {
                        "role": "user",
                        "content": "<User message>",
                        "content_type": "text"
                    }
                ]
            }'
        Return:
        {   'code': 0,
            'data': {'bot_id': '<BOT ID>',
                    'conversation_id': '<CONVERSATION ID>',
                    'created_at': <timestamp>,
                    'id': '<CHAT ID>',
                    'last_error': {'code': 0, 'msg': ''},
                    'status': 'in_progress'},
            'msg': ''
        }
        """
        data = {
            "bot_id": self.bot_id,
            "user_id":  self.user_id,
            'stream': False,
            "auto_save_history": True,
            'additional_messages': messages,
        }
        query = urllib.parse.urlencode({'conversation_id': conversation_id}) if conversation_id else None
        resp = self._send_request(data = data,
                                  query=f"?{query}" if query else None)
        if not 'data' in resp:
            logging.error(f"No data in response:\n{resp}")
            return None, None
        if not 'id' in resp['data']:
            logging.error(f"No chat_id in response:\n{resp}")
            return None, None

        # assert(resp['data']['bot_id'] == self.bot_id)
        # assert(resp['data']['status'] == 'in_progress')
        # Returns: <CONVERSATION_ID>, <CHAT_ID>
        return resp['data']['conversation_id'], resp['data']['id']

    def chat_status(self, conversation_id, chat_id) -> bool:
        """
        Example (https://www.coze.com/open):
        curl --location --request POST 'https://api.coze.com/v3/chat/retrieve?chat_id=<CHAT_ID>&conversation_id=<CONVERSATION_ID>'  
             --header 'Authorization: Bearer <API KEY>' 
             --header 'Content-Type: application/json'
        """
        query = urllib.parse.urlencode({
            'chat_id': chat_id,
            'conversation_id': conversation_id
        })
        resp = self._send_request(query = f"/retrieve?{query}")
        if not 'data' in resp:
            logging.error(f"No data in response:\n{resp}")
            return False
        if not 'status' in resp['data']:
            logging.error(f"No status in response:\n{resp}")
            return False
        # assert(resp['data']['bot_id'].strip() == self.bot_id)
        # assert(resp['data']['id'].strip() == chat_id)
        # assert(resp['data']['conversation_id'].strip() == conversation_id)
        return resp['data']['status'].strip() == 'completed'

    def get_messages(self, conversation_id, chat_id) -> List[Dict]:
        """
        Example (https://www.coze.com/open):
        curl --location --request POST 'https://api.coze.com/v3/chat/message/list?chat_id=<CHAT_ID>&conversation_id=<CONVERSATION_ID>' 
            --header 'Authorization: Bearer <API KEY>' \
            --header 'Content-Type: application/json' \
        Returns a list of message objects like this:
        [
            {
                "bot_id": "<BOT_ID>",
                "chat_id": "<CHAT_ID>",
                "content": "........",
                "content_type": "text",
                "conversation_id": "<CONVERSATION_ID>",
                "id": "<MESSAGE_ID>",
                "role": "assistant",
                "type": "answer"
            },
            {
                "bot_id": "<BOT_ID>",
                "chat_id": "<CHAT_ID>",
                "content": "{\"msg_type\":\"generate_answer_finish\",\"data\":\"{\\\"finish_reason\\\":0}\",\"from_module\":null,\"from_unit\":null}",
                "content_type": "text",
                "conversation_id": "<CONVERSATION_ID>",
                "id": "<MESSAGE_ID>",
                "role": "assistant",
                "type": "verbose"
            },
            {
                "bot_id": "<BOT_ID>",
                "chat_id": "<CHAT_ID>",
                "content": ".....",
                "content_type": "text",
                "conversation_id": "<CONVERSATION_ID>",
                "id": "<MESSAGE_ID>",
                "role": "assistant",
                "type": "follow_up"
            },
            ...
        ]
        """
        query = urllib.parse.urlencode({
            'chat_id': chat_id,
            'conversation_id': conversation_id
        })
        resp = self._send_request(query = f"/message/list?{query}")
        if 'data' in resp:
            return resp['data']
        else:
            logging.error(f"No data in response:\n{resp}")
            return None

    def chat(self, message: str) -> str:
        """
        Start or continue a chat with the bot by sending a message.

        Args:
            message (str): The message to send to the chat.
        
        Returns:
            str: The response from the bot.
        """
        self.conversation_id, self.chat_id = self.start_chat(
            messages=[{"role": "user", "content": message, "content_type": "text"}],
            conversation_id=self.conversation_id,
        )
        if not self.chat_id:
            logging.error("Failed to start a chat, please try again")
            return None

        # Poll for the request to be completed.
        time.sleep(random.uniform(0.8, 1.5))
        for _ in range(20):
            if self.chat_status(conversation_id=self.conversation_id, chat_id=self.chat_id):
                break
            else:
                time.sleep(random.uniform(1,3))

        # Get response messages.
        resp_msgs = self.get_messages(
            conversation_id=self.conversation_id, chat_id=self.chat_id
        )
        if not resp_msgs:
            return None
        for msg in resp_msgs:
            if msg['type'] == 'answer':
                # pprint(msg)
                # assert(msg['role'] == 'assistant')
                # assert(msg['conversation_id'] == self.conversation_id)
                return msg['content']
                # print(f"Assistant: {msg['content']}")
        
        return None

    def check_connection(self):
        """
        Check the connection to the Coze Bot API.

        Raises:
            CozeBotException: If the connection check fails.
        """
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        try:
            response = requests.get(self.api_endpoint, headers=headers, timeout=10)
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            raise CozeBotException(f"Connection check failed: {e}") from e


# Example usage:
# api_key = "your_api_key_here"
# bot = CozeBotWrapper(api_key, bot_id="<your_bot_id>", user_id="<user_id>")
# response = bot.chat("Hello")
# print(response)
