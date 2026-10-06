from fastapi import APIRouter,HTTPException
from config import SQLITE_CONNECTION_PATH,MAX_CHUNKS,RECENT_MESSAGES_LIMIT
from db.database import get_connection
from db.crud import create_set,list_sets,get_message_count,add_knowledges,list_knowledges,delete_knowledge_by_set,delete_messages_by_set,delete_set,get_latest_messages
from vectorstore.qdrant_client import get_qdrant_client
from vectorstore.collections import create_set_collections, get_collection_name,delete_set_collections
from vectorstore.ingest import embed_and_upsert_chunks,make_knowledge_base,chunk_text
from agent.chat import chat as run_chat
from scarping.get_content import validate_url,getting_extra_data_through_tavily,scarping_website_using_firecrawl,URLValidationError,TavilyError,ScrapingError
from urllib.parse import urlparse

router=APIRouter()

_qdrant_client=get_qdrant_client()
from pydantic import BaseModel, Field

class SetCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=10000)

def _get_db_connection():
    """Fresh SQLite connection per request, closed at the end of the request."""
    return get_connection(path=SQLITE_CONNECTION_PATH)

def _set_exists(connection,set_id:int):
    sets=list_sets(connection=connection)
    return any(row[0]==set_id for row in sets)

@router.post("/sets")
def create_new_set(payload:SetCreate):
    name=payload.name
    if not name:
        raise HTTPException(status_code=400,detail="'name' is required")

    connection=_get_db_connection()

    try:
        set_id=create_set(connection=connection,name=name)
        try:
            create_set_collections(client=_qdrant_client,set_id=set_id)

        except Exception as e:
            delete_set(connection=connection, set_id=set_id)
            raise HTTPException(status_code=500,detail="Set created in database but Qdrant collection Failed")

        return {"id":set_id,"name":name}

    finally:
        connection.close()

@router.get("/sets")
def get_all_sets():
    connection=_get_db_connection()
    try:
        rows=list_sets(connection=connection)
        return [
            {
                "id":row[0],"name":row[1],"create_at":row[2]
             } for row in rows
        ]

    finally:
        connection.close()

@router.post("/sets/{set_id}/documents")
def upload_url(set_id:int,url:str):
    connection=_get_db_connection()
    try:
        if not _set_exists(connection=connection,set_id=set_id):
            raise HTTPException(status_code=404,detail=f"Set {set_id}  not found")
    finally:
        connection.close()

    try:
        url=validate_url(url=url)
        tavily_data=getting_extra_data_through_tavily(url=url)
        firecrawl_data,page_title=scarping_website_using_firecrawl(url)
        knowledge=make_knowledge_base(firecrawl_data=firecrawl_data,tavily_data=tavily_data)

        new_chunks=chunk_text(knowledge)

        knowledge_name,_=get_collection_name(set_id=set_id)
        current_count=_qdrant_client.count(knowledge_name).count

        if current_count+len(new_chunks)>MAX_CHUNKS:
            raise HTTPException(
            status_code=400,
            detail=f"This set has reached its capacity ({MAX_CHUNKS} chunks). Start a new set for additional material.",
        )

        parsed=urlparse(url)
 
        url_name=page_title or parsed.hostname
        embed_and_upsert_chunks(client=_qdrant_client,set_id=set_id,chunks=new_chunks,url_name=url_name)

        connection=_get_db_connection()
        try:
            add_knowledges(connection=connection,set_id=set_id,url_name=url_name,source_url=url,chunk_count=len(new_chunks))

        finally:
            connection.close()

        total_chunks=current_count+len(new_chunks)

        return{
            "status":"scraped",
            "set_id":set_id,
            "url_name":url_name,
            "source_url":url,
            "chunks_added":len(new_chunks),
            "total_chunks":total_chunks
        }
        
    except URLValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except ScrapingError as e:
        raise HTTPException(status_code=502, detail=str(e))

    except TavilyError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Document ingestion failed: {e}")

@router.get("/sets/{set_id}/knowledges")
def get_set_knowledge(set_id: int):
    connection = _get_db_connection()
    try:
        if not _set_exists(connection=connection, set_id=set_id):
            raise HTTPException(status_code=404, detail=f"Set {set_id} not found")

        rows = list_knowledges(connection=connection, set_id=set_id)
        return [
            {
                "url_name": row[0],
                "source_url": row[1],
                "chunk_count": row[2],
                "uploaded_at": row[3]
            }
            for row in rows
        ]
    finally:
        connection.close()

@router.get("/sets/{set_id}/messages")
def get_set_messages(set_id: int):
    """Returns the currently-buffered recent messages for a set (whatever is
    still in SQLite — older turns already compacted into that set's Qdrant
    _memory collection aren't returned here, since they're no longer meant
    to be replayed verbatim, only recalled by the agent's memory tool)."""
    connection = _get_db_connection()
    try:
        if not _set_exists(connection=connection, set_id=set_id):
            raise HTTPException(status_code=404, detail=f"Set {set_id} not found")

        rows = get_latest_messages(connection=connection, set_id=set_id, n=RECENT_MESSAGES_LIMIT)
        return [{"role": role, "content": content} for role, content in rows]
    finally:
        connection.close()

@router.post("/sets/{set_id}/chat")
def chat_with_set(set_id: int, payload: ChatRequest):
    user_input = payload.message
    if not user_input:
        raise HTTPException(status_code=400, detail="'message' is required")

    connection = _get_db_connection()
    try:
        if not _set_exists(connection=connection, set_id=set_id):
            raise HTTPException(status_code=404, detail=f"Set {set_id} not found")

        try:
            answer = run_chat(
                connection=connection,
                client=_qdrant_client,
                set_id=set_id,
                user_input=user_input,
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Chat failed: {e}")

        return {"answer": answer}
    finally:
        connection.close()


@router.get("/sets/{set_id}/status")
def set_status(set_id: int):
    """Small helper endpoint the frontend can use to know if a set has any
    knowledge_based/messages yet, and to show chunk-capacity usage for the set."""
    connection = _get_db_connection()
    try:
        if not _set_exists(connection=connection, set_id=set_id):
            raise HTTPException(status_code=404, detail=f"Set {set_id} not found")
        message_count = get_message_count(connection=connection, set_id=set_id)
        docs_name, _ = get_collection_name(set_id)
        chunk_count = _qdrant_client.count(docs_name).count
        return {
            "set_id": set_id,
            "message_count": message_count,
            "chunk_count": chunk_count,
            "chunk_limit": MAX_CHUNKS,
        }
    finally:
        connection.close()

@router.delete("/sets/{set_id}")
def remove_set(set_id:int):
    connection=_get_db_connection()
    try:
        if not _set_exists(connection=connection,set_id=set_id):
            raise HTTPException(status_code=404,detail=f"Set {set_id} not found")

        delete_messages_by_set(connection=connection,set_id=set_id)
        delete_knowledge_by_set(connection=connection,set_id=set_id)
        delete_set(connection=connection,set_id=set_id)
        try:
            delete_set_collections(client=_qdrant_client,set_id=set_id)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Set Deleted in database but deletion of Qdrant collections failed: {e}",
            )
        return {"status":"deleted","set_id":set_id}
    finally:
        connection.close()
