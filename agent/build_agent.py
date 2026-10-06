from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_classic.agents import AgentExecutor,create_react_agent
from config import GEMINI_API_KEY,GEMINI_CHAT_MODEL
from agent.tools import make_knowledge_tool,make_memory_tool
from agent.prompts import react_prompt

TEMPERATURE=0.1
MAX_TRIES=10

llm = ChatGoogleGenerativeAI(
    model=GEMINI_CHAT_MODEL,
    google_api_key=GEMINI_API_KEY,
    temperature=TEMPERATURE
)



def build_executor(client,set_id):         
    tools=[make_knowledge_tool(client=client,set_id=set_id),make_memory_tool(client=client,set_id=set_id)]

    agent=create_react_agent(llm=llm,
                             tools=tools,
                             prompt=react_prompt)
    
    executor=AgentExecutor(agent=agent,
                           tools=tools,
                           verbose=True,
                           handle_parsing_errors=True,
                           max_iterations=MAX_TRIES
                           )

    return executor
