from config import QDRANT_PATH
from qdrant_client import QdrantClient

def get_qdrant_client():
    return QdrantClient(path=QDRANT_PATH)
