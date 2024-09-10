import requests
# import urllib.parse

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
    def __init__(self, api_key, base_url="https://api.coze.com/v3"):
        self.api_endpoint = f"{base_url}/chat"
        self.api_key = api_key

    def send_message(self, messages):
        """
        Send a message to the Coze Bot API.

        Args:
            messages (list): A list of message objects.

        Returns:
            dict: The response from the API.
        """
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        data = {
            'model': 'gpt-3.5-turbo',  # Assuming a model similar to OpenAI's
            'messages': messages,
            'stream': False
        }
        try:
            response = requests.post(self.api_endpoint, json=data, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise CozeBotException(f"An error occurred: {e}") from e

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
# bot = CozeBotWrapper(api_key)
# messages = [{"role": "user", "content": "Hello, Coze Bot!"}]
# response = bot.send_message(messages)
# print(response)