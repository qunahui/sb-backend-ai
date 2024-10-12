from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
from langchain.schema import HumanMessage, AIMessage

load_dotenv(".env")

llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
)


def llm_chat(messages) -> str:
    invoke_messages = []
    for message in messages:
        if message.get("role") == "user":
            invoke_messages.append(HumanMessage(message.get("content")))
        elif message.get("role") == "assistant":
            invoke_messages.append(AIMessage(message.get("content")))

    return llm.invoke(invoke_messages)
