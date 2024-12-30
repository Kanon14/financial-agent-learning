import typer
from typing import Optional, List
# from phi.assistant import Assistant
from phi.agent import Agent
from phi.model.groq import Groq
from phi.model.ollama import Ollama
from phi.storage.agent.postgres import PgAgentStorage
from phi.knowledge.pdf import PDFUrlKnowledgeBase
from phi.vectordb.pgvector import PgVector2
from phi.embedder.ollama import OllamaEmbedder

import os
from dotenv import load_dotenv
load_dotenv()

os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")
db_url = "postgresql+psycopg://ai:ai@localhost:5532/ai"

# Initialize the knowledge base with the PDF file
knowledge_base = PDFUrlKnowledgeBase(
    urls=["https://phi-public.s3.amazonaws.com/recipes/ThaiRecipes.pdf"],
    vector_db=PgVector2(collection="recipes", db_url=db_url, 
                        embedder=OllamaEmbedder()) # embedder default to OpenAIEmbedder(); Groq don't have embedder
)

knowledge_base.load()

storage = PgAgentStorage(table_name="pdf_assistant", db_url=db_url)

def pdf_assistant(new: bool = False, user: str = "user"): # Linked to the storage table_name
    run_id: Optional[str] = None
    
    if not new:
        existing_run_ids: List[str] = storage.get_all_session_ids(user)
        if len(existing_run_ids) > 0:
            run_id = existing_run_ids[0]
            
    agent = Agent(
        model=Ollama(id="llama3.2"),
        run_id=run_id,
        user_id=user, 
        knowledge_base=knowledge_base,
        storage=storage,
        # Show tool calls in the response
        show_tool_calls=True,
        # Enable the agent to search the knowledge base 
        search_knowledge=True,
        # Enable the agent to read the chat history
        read_chat_history=True,
    )
    if run_id is None:
        run_id = agent.run_id
        print(f"Started Run: {run_id}\n")
    else:
        print(f"Resuming Run: {run_id}\n")
        
    agent.cli_app(markdown=True)
    
if __name__ == "__main__":
    typer.run(pdf_assistant)