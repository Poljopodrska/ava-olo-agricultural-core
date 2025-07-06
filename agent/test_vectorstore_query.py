from dotenv import load_dotenv
import os

load_dotenv()

from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

CHROMA_PATH = "rag/chroma_html"
embeddings = OpenAIEmbeddings()
vectorstore = Chroma(persist_directory=CHROMA_PATH, embedding_function=embeddings)

queries = [
    "Prosaro",
    "registracija",
    "kada ističe registracija",
    "fungicid Prosaro"
]

for query in queries:
    print(f"\n=== Query: '{query}' ===")
    docs = vectorstore.similarity_search(query, k=10)
    print(f"Docs found: {len(docs)}")
    for i, d in enumerate(docs):
        print(f"\n--- Doc {i+1} snippet ---\n{d.page_content[:500]}")
