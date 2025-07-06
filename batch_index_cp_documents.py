import os
from dotenv import load_dotenv
from langchain_community.document_loaders import BSHTMLLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

# Load environment variables from .env file
load_dotenv()

# Path to the folder containing FIS HTML documents
docs_folder = "docs"  # Change if needed
persist_directory = "rag/fis_chroma"

# Gather all .html files from the docs folder
html_files = [
    os.path.join(docs_folder, f)
    for f in os.listdir(docs_folder)
    if f.lower().endswith(".html")
]

all_docs = []
for path in html_files:
    try:
        loader = BSHTMLLoader(path)
        docs = loader.load()
        all_docs.extend(docs)
        print(f"✅ Loaded: {os.path.basename(path)}")
    except Exception as e:
        print(f"⚠️ Failed to load {os.path.basename(path)}: {e}")

# Split documents
splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
split_docs = splitter.split_documents(all_docs)

# Create vectorstore
embedding = OpenAIEmbeddings()
vectordb = Chroma.from_documents(split_docs, embedding=embedding, persist_directory=persist_directory)
vectordb.persist()

print(f"\n✅ Indexed {len(split_docs)} chunks from {len(html_files)} documents.")
