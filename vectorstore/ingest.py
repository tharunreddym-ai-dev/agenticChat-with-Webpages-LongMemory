import requests
import time
from langchain_groq import ChatGroq
from scarping.clean import clean_text
from qdrant_client.models import PointStruct
from config import GROQ_CHAT_MODEL,GROQ_API_KEY,NVIDIA_API_KEY,EMBEDDING_MODEL,EMBEDDING_MODEL_URL
from agent.prompts import knowledge_base_prompt
from langchain_text_splitters import RecursiveCharacterTextSplitter
from vectorstore.collections import get_collection_name
from uuid import uuid4

CHUNK_SIZE=1000
CHUNK_OVERLAP=200
MAX_TRIES=3

def make_knowledge_base(firecrawl_data,tavily_data):
    firecrawl_data_cleaned=clean_text(firecrawl_data)
    tavily_data_cleaned=clean_text(tavily_data)

    llm=ChatGroq(model=GROQ_CHAT_MODEL,
                 api_key=GROQ_API_KEY)
    

    prompt=knowledge_base_prompt.invoke(
        {
            "firecrawl_data":firecrawl_data_cleaned,
            "tavily_data":tavily_data_cleaned
        }
    )

    results=llm.invoke(prompt)

    knowledge = results.content.strip()

    if "<think>" in knowledge:
        if "</think>" in knowledge:
            knowledge=knowledge.split("</think>", 1)[1].strip()
        else:
            knowledge=knowledge.split("<think>", 1)[0].strip()
            
    return knowledge

def chunk_text(text):
    splitter=RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len
    )

    chunks=splitter.split_text(text=text)

    return chunks

def embed_chunks(chunks,input_type):
    headers={
        "Authorization":f"Bearer {NVIDIA_API_KEY}",
        "Content-Type":"application/json"
    }

    body={
        "model":EMBEDDING_MODEL,
        "input":chunks,
        "encoding_format":"float",
        "input_type":input_type
    }

    for attempt in range(MAX_TRIES):
        try:
            response=requests.post(url=EMBEDDING_MODEL_URL,headers=headers,json=body)
            if response.status_code!=200:
                raise Exception(f"API Error {response.text} with code {response.status_code}")
            data=response.json()

            if "data" not in data:
                raise Exception(f"Unexpected response {data}")
            
            embds=[item["embedding"] for item in data["data"]]
            return embds
        
        except Exception as e:
            if attempt==MAX_TRIES-1:
                raise e
            wait=2**attempt
            time.sleep(wait)
            print(f"Attempt- {attempt+1} Failed, Retrying in {wait} Seconds...")

def embed_and_upsert_chunks(client,set_id,chunks,url_name):
    embeddings=embed_chunks(chunks=chunks,input_type="passage")
    knowledge_name,_=get_collection_name(set_id=set_id)

    points=[]

    for i,(chunk,embedding) in enumerate(zip(chunks,embeddings)):
        points.append(
            PointStruct(
                id=str(uuid4()),
                vector=embedding,
                payload={
                    "text":chunk,
                    "source":url_name+" and tavily",
                    "chunk_index":i
                }
            )
        )     

    client.upsert(
        collection_name=knowledge_name,
        points=points
    )
