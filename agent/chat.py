from db.crud import get_latest_messages,add_message
from agent.build_agent import build_executor
from config import RECENT_MESSAGES_LIMIT
from agent.compaction import compact_if_needed,format_chat_history

def chat(connection, client, set_id, user_input) -> str:
    messages=get_latest_messages(connection=connection,set_id=set_id,n=RECENT_MESSAGES_LIMIT)
    
        
    chat_history=format_chat_history(messages)

    executor=build_executor(client=client,set_id=set_id)

    result=executor.invoke({"input":user_input,"chat_history":chat_history})

    output=result["output"]

    add_message(connection=connection,set_id=set_id,role="user",content=user_input)

    add_message(connection=connection,set_id=set_id,role="assistant",content=output)

    compact_if_needed(connection=connection,client=client,set_id=set_id)  
      
    return output
