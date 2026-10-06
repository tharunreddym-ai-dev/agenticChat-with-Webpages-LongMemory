from fastapi import FastAPI

from config import SQLITE_CONNECTION_PATH
from db.database import create_table
from api.routes import router

app = FastAPI(title="Multi-Set Web RAG Chatbot")

app.include_router(router)


@app.on_event("startup")
def on_startup():
    create_table(path=SQLITE_CONNECTION_PATH)
