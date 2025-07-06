from dotenv import load_dotenv
import os
from langchain_community.document_loaders import DirectoryLoader, UnstructuredHTMLLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

# Load .env variables (for OPENAI_API_KEY etc)
load_dotenv()

# Absolute path to your HTML docs folder
HTML_DOCS_PATH = r"C:\Users\HP\ava_olo\docs"  # <-- Change if needed

# Where to save your vectorstore for HTML RAG
CHROMA_PATH = r"C:\Users\HP\ava_olo\rag\chroma_html"

print(f"Loading HTML docs from: {HTML_DOCS_PATH}")

# Load all HTML files in the folder
loader = DirectoryLoader(HTML_DOCS_PATH, loader_cls=UnstructuredHTMLLoader)
documents = loader.load()

print(f"Loaded {len(documents)} HTML documents.")

# Print sample content from first few docs to verify
for i, doc in enumerate(documents[:3]):
    print(f"\n--- Document {i+1} sample ---\n{doc.page_content[:500]}")

# Split documents into chunks with overlap for better embedding context
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=300)
chunks = text_splitter.split_documents(documents)

print(f"Split documents into {len(chunks)} chunks.")

# Create embeddings and save vectorstore
embeddings = OpenAIEmbeddings()
vectorstore = Chroma.from_documents(
    documents=chunks,
    embedding=embeddings,
    persist_directory=CHROMA_PATH
)

print(f"✅ HTML RAG vectorstore created and saved at: {CHROMA_PATH}")
