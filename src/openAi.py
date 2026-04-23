from openai import OpenAI
from typing import List, Dict, Optional
from managerAi import *


class OpenAIConversation:
    def __init__(
            self, api_key: str, base_url: str = "https://api.deepseek.com",
            model: str = "deepseek-chat",
            system_message: str = "You are a helpful assistant"):
        """
        Initialize the conversation with API credentials and optional system message.

        Args:
            api_key: Your OpenAI API key
            base_url: API base URL (defaults to DeepSeek)
            model: Model to use (defaults to deepseek-chat)
            system_message: Initial system message to set behavior
        """
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model
        self.conversation_history = [
            {"role": "system", "content": system_message}
        ]

    def add_message(self, role: str, content: str) -> None:
        """
        Add a message to the conversation history.

        Args:
            role: 'system', 'user', or 'assistant'
            content: The message content
        """
        self.conversation_history.append({"role": role, "content": content})

    def get_response(self, user_message: str, stream: bool = False) -> dict:
        """
        Get a structured response from the assistant.

        Args:
            user_message: The user's message to send
            stream: Whether to stream the response

        Returns:
            A dictionary containing:
            - "success": bool (True if successful)
            - "response": str (assistant's reply)
            - "error": str (if any error occurs)
        """
        try:
            # Add user message to history
            self.add_message("user", user_message)

            # Get completion from API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.conversation_history,
                stream=stream
            )

            if stream:
                collected_chunks = []
                for chunk in response:
                    if chunk.choices[0].delta.content:
                        collected_chunks.append(chunk.choices[0].delta.content)
                assistant_response = "".join(collected_chunks)
            else:
                assistant_response = response.choices[0].message.content

            # Add assistant response to history
            self.add_message("assistant", assistant_response)

            # Return structured response
            return {
                "success": True,
                "response": assistant_response,
                "error": None
            }

        except Exception as e:
            return {
                "success": False,
                "response": None,
                "error": str(e)
            }

    def reset_conversation(self, system_message: Optional[str] = None) -> None:
        """
        Reset the conversation history, optionally with a new system message.

        Args:
            system_message: New system message (None keeps current)
        """
        if system_message is None:
            system_message = self.conversation_history[0]["content"]

        self.conversation_history = [
            {"role": "system", "content": system_message}
        ]

    def get_conversation_history(self) -> List[Dict[str, str]]:
        """
        Get the current conversation history.

        Returns:
            List of message dictionaries with role and content
        """
        return self.conversation_history


def ai_request(message="Your an soccer manager", question="what"):
    # Initialize the conversation
    chat = OpenAIConversation(
        api_key="sk-cd1084b08e6440d9a46288f0296d40c6",
        system_message=message
    )

    # First message
    response = chat.get_response(question)
    print("Assistant:", response)


def get_ai(key, message, question):
    email = (manager_decode_data(key))
    if "email" in email:
        return ai_request(message, question)
    else:
        return "Invalid Token"


if __name__ == "__main__":
    test_token = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6InRlc3QwMS5qYW5kcmVzQGdtYWlsLmNvbSJ9.DveFuC8G59RQIHxMkyxmXufO8u4bEHOKnLppZb1Hly4rG4P6xei4KRpyLfKcHWGKEhVVPzpHb09oPOTCFzekVFDyVdlq5L4WrnFjDCjgdqWApBJlnqZlME4v802bW35tyMi3Ftr7hUSv6EluhUHQMEuoevywXnLR39YjohY"
    # message = "Your an soccer manager"
    # question = "how to tell Raphina barcelona soccer play that he needs pass the ball more to the right side of the pitch"
    # get_ai(test_token, message, question)
    # get_ai()
    # pprint(get_history())
