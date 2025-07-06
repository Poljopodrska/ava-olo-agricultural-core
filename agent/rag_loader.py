from dotenv import load_dotenv
import os
from langchain_community.document_loaders import DirectoryLoader, UnstructuredHTMLLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

load_dotenv()

HTML_DOCS_PATH = "../rag/html_source_docs"  # adjust to your HTML folder path
CHROMA_PATH = "../rag/chroma_html"

# Load HTML files
loader = DirectoryLoader(HTML_DOCS_PATH, loader_cls=UnstructuredHTMLLoader)
documents = loader.load()

print(f"Loaded {len(documents)} HTML documents.")

# Split text into chunks
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
chunks = text_splitter.split_documents(documents)

print(f"Split into {len(chunks)} chunks.")

# Embed and store in Chroma
embeddings = OpenAIEmbeddings()
vectordb = Chroma.from_documents(documents=chunks, embedding=embeddings, persist_directory=CHROMA_PATH)

print("✅ HTML RAG vectorstore created and saved.")

