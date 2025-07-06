import os
import re
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Add parent directory to path for config import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DATABASE_URL, DB_POOL_SETTINGS

from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from langchain_community.agent_toolkits.sql.base import create_sql_agent
from langchain_community.utilities.sql_database import SQLDatabase
from langchain.agents.agent_types import AgentType
from langchain.chains import RetrievalQA
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

# Load environment
dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.env'))
load_dotenv(dotenv_path)

# === Shared Config ===
RUN_RAG = os.getenv("RUN_RAG", "false").lower() == "true"
print(f"[DEBUG] Using PostgreSQL URL: {DATABASE_URL}")
print(f"[DEBUG] RAG enabled: {RUN_RAG}")

# === SQL Agent Setup - PostgreSQL ONLY ===
engine = create_engine(DATABASE_URL, **DB_POOL_SETTINGS)
db = SQLDatabase(engine)

llm_sql = ChatOpenAI(temperature=0, model="gpt-4o")
llm_friendly = ChatOpenAI(temperature=0.5, model="gpt-4o")

schema_description = """..."""  # Replace with your schema description

sql_toolkit = SQLDatabaseToolkit(db=db, llm=llm_sql)
sql_agent_executor = create_sql_agent(
    llm=llm_sql,
    toolkit=sql_toolkit,
    agent_type=AgentType.OPENAI_FUNCTIONS,
    verbose=True,
    prefix=schema_description,
    agent_executor_kwargs={"handle_parsing_errors": True}
)

# === Optional RAG Setup ===
rag_chain = None

if RUN_RAG:
    try:
        from pinecone import Pinecone
        from langchain_pinecone import PineconeVectorStore

        pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        index = pc.Index(os.getenv("PINECONE_INDEX_NAME"))
        embeddings = OpenAIEmbeddings()
        vectorstore = PineconeVectorStore(index=index, embedding=embeddings, text_key="text")
        retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 15})
        rag_chain = RetrievalQA.from_chain_type(llm=llm_sql, retriever=retriever, return_source_documents=False)

        print("[DEBUG] Pinecone RAG chain initialized successfully.")
    except Exception as e:
        print(f"[ERROR] Failed to initialize Pinecone RAG: {e}")
        rag_chain = None

# === Classification Logic ===

def is_cp_question_llm(question: str) -> bool:
    classification_prompt = f"""
You are deciding if a question is about **crop protection**, such as pesticide use, herbicides, fungicides, insecticides, FIS documents, or registration details.

Questions that mention product names like "Prosaro", "Decis", "Fandango", etc., and ask about:
- dose
- use instructions
- active substance
- waiting period (karenca)
- number of treatments
- registration expiry

...are all considered crop protection (CP) questions.

Now decide if the following question is a CP question. Answer with only YES or NO.

Question: "{question}"
"""
    try:
        response = llm_sql.invoke(classification_prompt).content.strip().lower()
        print(f"[ROUTING] LLM classified as CP: {response}")
        return "yes" in response
    except Exception as e:
        print(f"[ERROR] LLM routing failed: {e}")
        return False

# === Core Handler ===

def ask_agent(question: str) -> str:
    if is_cp_question_llm(question) and rag_chain:
        print("[ASK_AGENT] Routing to RAG (documents)...")
        try:
            docs = rag_chain.retriever.get_relevant_documents(question)
            print(f"[RAG] Docs retrieved: {len(docs)}")
            for i, d in enumerate(docs):
                print(f"\n--- Doc {i+1} snippet ---\n{d.page_content[:500]}")

            answer = rag_chain.invoke({"query": question})
            print("[RAG] Answer:", answer)
            return str(answer).strip()

        except Exception as e:
            print(f"[ERROR] RAG error: {e}")
            try:
                with engine.connect() as conn:
                    conn.execute(
                        text("INSERT INTO unanswered_questions (question, error_message) VALUES (:q, :e)"),
                        {"q": question, "e": str(e)}
                    )
            except Exception as db_err:
                print(f"[ERROR] Failed to log error to DB: {db_err}")
            return "I'll provide the answer in a short time."

    else:
        print("[ASK_AGENT] Routing to SQL agent...")
        try:
            return sql_agent_executor.run(question)
        except Exception as e:
            print(f"[ERROR] SQL Agent failed: {e}")
            return "Sorry, I couldn't find the answer right now."
