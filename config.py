from dotenv import load_dotenv
import os

load_dotenv()

required_keys=["GROQ_API_KEY",
               "NVIDIA_API_KEY",
               "GROQ_CHAT_MODEL",
               "GEMINI_API_KEY",
               "GEMINI_CHAT_MODEL",
               "EMBEDDING_MODEL",
               "EMBEDDING_MODEL_URL",
               "QDRANT_PATH",
               "SQLITE_CONNECTION_PATH",
               "EMBEDDING_MODEL_DIMENSION",
               "RECENT_MESSAGES_LIMIT",
               "FIRECRAWL_API_KEY",
               "TAVILY_API_KEY",
               "MAX_CHUNKS"
               ]

missing=[k for k in required_keys if not os.getenv(k)]

if missing:
    raise EnvironmentError(f"Missing required environment variables: {missing}")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GEMINI_API_KEY=os.getenv("GEMINI_API_KEY")
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")
GEMINI_CHAT_MODEL=os.getenv("GEMINI_CHAT_MODEL")
GROQ_CHAT_MODEL = os.getenv("GROQ_CHAT_MODEL")
EMBEDDING_MODEL= os.getenv("EMBEDDING_MODEL")
EMBEDDING_MODEL_URL= os.getenv("EMBEDDING_MODEL_URL")
EMBEDDING_MODEL_DIMENSION=int(os.getenv("EMBEDDING_MODEL_DIMENSION"))
QDRANT_PATH = os.getenv("QDRANT_PATH")
SQLITE_CONNECTION_PATH=os.getenv("SQLITE_CONNECTION_PATH")
RECENT_MESSAGES_LIMIT=int(os.getenv("RECENT_MESSAGES_LIMIT"))
FIRECRAWL_API_KEY=os.getenv("FIRECRAWL_API_KEY")
TAVILY_API_KEY=os.getenv("TAVILY_API_KEY")
MAX_CHUNKS=int(os.getenv("MAX_CHUNKS"))
