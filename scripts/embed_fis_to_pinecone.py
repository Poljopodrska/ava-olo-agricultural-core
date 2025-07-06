import os
from dotenv import load_dotenv
from langchain_community.document_loaders import DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Pinecone as PineconeVectorStore

def embed_documents():
    # === Load environment ===
    dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.env'))
    load_dotenv(dotenv_path)

    index_name = os.getenv("PINECONE_INDEX_NAME")
    if not index_name:
        raise ValueError("PINECONE_INDEX_NAME not set in .env")

    # === Load and split HTML files ===
    fis_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'rag', 'fis_html'))
    print(f"[INFO] Loading HTML files from: {fis_folder}")
    loader = DirectoryLoader(fis_folder, glob="*.html")
    docs = loader.load()

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    splits = splitter.split_documents(docs)
    print(f"[INFO] Split into {len(splits)} chunks.")

    # === Embed and upload ===
    embeddings = OpenAIEmbeddings()

    vectorstore = PineconeVectorStore.from_documents(
        documents=splits,
        embedding=embeddings,
        index_name=index_name,  # ✅ just the string
    )

    print(f"[✅] Upload complete: {len(splits)} chunks to index '{index_name}'")
