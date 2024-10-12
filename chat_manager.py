from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage, AIMessage
from config import LLM_MODEL

class ChatManager:
    def __init__(self):
        self.chat_model = ChatOpenAI(model_name=LLM_MODEL)
        self.conversation_history = []

    def add_user_message(self, message):
        self.conversation_history.append(HumanMessage(content=message))

    def get_ai_response(self):
        ai_response = self.chat_model(self.conversation_history)
        self.conversation_history.append(AIMessage(content=ai_response.content))
        return ai_response.content

    def display_conversation(self):
        for message in self.conversation_history:
            if isinstance(message, HumanMessage):
                print(f"User: {message.content}")
            elif isinstance(message, AIMessage):
                print(f"AI: {message.content}")
        print()