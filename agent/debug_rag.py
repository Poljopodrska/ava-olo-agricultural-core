from langchain_community.document_loaders import DirectoryLoader, UnstructuredPDFLoader

DOCS_PATH = "../rag/source_docs"

loader = DirectoryLoader(DOCS_PATH, loader_cls=UnstructuredPDFLoader)

documents = loader.load()

for doc in documents:
    print(f"Source file: {doc.metadata['source']}")
    print(f"Content sample:\n{doc.page_content[:1000]}")  # print first 1000 chars
    print("-" * 80)
