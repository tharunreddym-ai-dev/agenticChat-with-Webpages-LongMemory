from langchain_core.tools import Tool
from vectorstore.ingest import embed_chunks
from vectorstore.collections import get_collection_name

TOP_K=3

def embed_query(query_text) -> list[float]:
    return embed_chunks(chunks=[query_text],input_type="query")[0]

def search_collection(client, collection_name, query_text, top_k) -> list[str]:
    
    query_vector=embed_query(query_text=query_text)

    results=client.query_points(
        collection_name=collection_name,
        query=query_vector,
        limit=top_k,
        with_payload=True
    ).points

    retrieved_chunks=[]

    if not results:
        return ["No relevant information was found."]

    for i,result in enumerate(results,start=1):
        retrieved_chunks.append(f'Result:{i} Content:{result.payload["text"]} Source:{result.payload["source"]}')
    return retrieved_chunks

def make_knowledge_tool(client, set_id):
    knowledge_name,_=get_collection_name(set_id=set_id)
    def _search(query: str) -> str:
        results=search_collection(client=client,collection_name=knowledge_name,query_text=query,top_k=TOP_K)
        return "\n\n".join(results)
    return Tool(
                name="website_rag_search",
                func=_search,
                description="""Use this tool when the user's question requires retrieving information
                               from the websites and web content provided by the user and stored
                               in the current set's RAG knowledge base.

                               Strictly do not use this tool for:
                               - Searching for live or up-to-date information on the web.
                               - Scraping or searching new websites.
                               - Retrieving previous conversation history."""
                                )

def make_memory_tool(client, set_id):
    _,memory_name=get_collection_name(set_id=set_id)
    def _search(query: str) -> str:
        if client.count(memory_name).count==0:
            return "There is no long-term memory yet for this conversation"
        results=search_collection(client=client,collection_name=memory_name,query_text=query,top_k=TOP_K)
        return "\n\n".join(results)
    return Tool(name="long_term_memory_rag_search", 
                func=_search, 
                description="""Use this when the user references or asks about something from earlier in this 
                               conversation that isn't visible in your current context.
                               This conversation will be summarized so phrase a query accordingly and it will be 
                               summarized in chronologically order
                               Do not use this tool for questions about Website.
                               For Website Related questions, use website_rag_search instead."""
                               )
