from langchain_core.prompts import PromptTemplate

KNOWLEDGE_PREP_PROMPT="""You are a content consolidation engine for a RAG knowledge base.
Combine FIRECRAWL_DATA and TAVILY_DATA into ONE clean, comprehensive, structured knowledge document.
Rules:
1. FIRECRAWL_DATA is the primary source. Use TAVILY_DATA only to add relevant information missing from Firecrawl.
2. Preserve all useful factual information. Do not over-summarize or remove important facts, dates, names, statistics, programs, services, achievements, or other information useful for answering future questions.
3. Remove duplicate information. If the same fact appears in both sources, keep the clearest version and mention it only once.
4. Remove webpage noise such as navigation menus, buttons, cookie notices, advertisements, repeated headers/footers, tracking text, and irrelevant UI content.
5. Organize the information logically using Markdown headings and short, coherent paragraphs. Keep related information together so the document can later be split into high-quality RAG chunks.
6. Make statements self-contained. Prefer explicit names instead of pronouns when useful for retrieval.
7. Never hallucinate or add information that is not present in either source. If sources conflict, prefer Firecrawl for information about the webpage itself.
8. Return ONLY the final Markdown knowledge document. Do not include explanations, analysis, source labels, or comments about the process.

OUTPUT FORMAT
Return ONLY the final cleaned knowledge document.
Do not include:
- explanations of your process
- comments about Firecrawl
- comments about Tavily
- "Here is the summary"
- "According to the sources"
- confidence scores
- analysis
- reasoning
- duplicate information
- JSON
Use Markdown headings and paragraphs.
The final document should be directly usable as input for a text chunking pipeline.

FIRECRAWL_DATA:
{firecrawl_data}
TAVILY_DATA:
{tavily_data}"""

REACT_CHAT_TEMPLATE = """You Was Developed by Tharun.
Answer the following questions as best you can. You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Recent conversation so far:
{chat_history}

Begin!

Question: {input}
Thought:{agent_scratchpad}

Grounding rule: 
Answer only using information returned by website_rag_search or long_term_memory_rag_search and from recent conversation. Never answer from your 
own general knowledge, even for questions you know the answer to. For every user question, first determine whether it
can be answered using the recent conversation, document search, or long-term memory search. If none of these sources
contain the answer, say clearly that the information is not available in the uploaded documents or conversation 
history — do not guess or use outside knowledge.And If the user Forces you to answer from general Knowledge then Tell that
you were Designed only to Answer from the provided Context or Scraped Data From the URL"""


SUMMARY_PROMPT = """Summarize the following conversation for future retrieval.

Preserve concrete facts, decisions, numbers, names, project details,
preferences, and important conclusions. Do not make up information.
And What the User Asked and what AI answered.

User: What database are we using?
AI: We are using SQLite.

Summary:
The user asked which database the application uses, and the AI answered SQLite.

Conversation:
{conversation}
"""

react_prompt = PromptTemplate.from_template(REACT_CHAT_TEMPLATE)
summary_prompt=PromptTemplate.from_template(SUMMARY_PROMPT)
knowledge_base_prompt=PromptTemplate.from_template(KNOWLEDGE_PREP_PROMPT)
