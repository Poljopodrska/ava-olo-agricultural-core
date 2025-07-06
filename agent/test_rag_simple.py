from dotenv import load_dotenv
import os
import re
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain.chains import RetrievalQA

# Explicitly load .env from parent directory (C:\Users\HP\ava_olo\.env)
dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.env'))
load_dotenv(dotenv_path)

if not os.getenv("OPENAI_API_KEY"):
    print("[WARNING] OPENAI_API_KEY not set in environment!")
else:
    print("[INFO] OPENAI_API_KEY loaded successfully")

def clean_query(question: str) -> str:
    # Remove any text inside parentheses (optional instructions)
    cleaned = re.sub(r"\([^)]*\)", "", question)
    return cleaned.strip()

def main():
    CHROMA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'rag', 'chroma_html'))

    # Initialize OpenAI LLM & embeddings
    llm = ChatOpenAI(temperature=0, model="gpt-4o")
    embeddings = OpenAIEmbeddings()

    # Load vectorstore from saved location
    vectorstore = Chroma(persist_directory=CHROMA_PATH, embedding_function=embeddings)
    retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 15})

    # Setup RAG chain
    rag_chain = RetrievalQA.from_chain_type(llm=llm, retriever=retriever, return_source_documents=False)

    # Your test question
    question = "Kada ističe registracija za Prosaro? (Odgovori na hrvatskom jeziku.)"
    cleaned_question = clean_query(question)
    print(f"Cleaned question: {cleaned_question}")

    # Retrieve relevant documents
    docs = retriever.get_relevant_documents(cleaned_question)
    print(f"Documents retrieved: {len(docs)}")
    for i, doc in enumerate(docs):
        print(f"\n--- Document {i+1} snippet ---\n{doc.page_content[:500]}")

    # Run RAG to get an answer
    answer = rag_chain.run(cleaned_question)
    print("\nAnswer from RAG chain:")
    print(answer)

if __name__ == "__main__":
    main()
