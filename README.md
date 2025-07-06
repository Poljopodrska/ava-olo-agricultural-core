# AVA Pinecone RAG

This project is a farming assistant using RAG (Retrieval-Augmented Generation) with Pinecone and OpenAI.

## 📂 Project Structure

- 📄 .env
- 📄 .gitignore
- 📄 Procfile
- 📄 README.md
- 📄 __init__.py
- 📁 **agent**
  - 📄 __init__.py
  - 📄 agent.py
  - 📄 debug_rag.py
  - 📄 html_rag_loader.py
  - 📄 rag_loader.py
  - 📄 test_rag_simple.py
  - 📄 test_vectorstore_query.py
- 📁 **app**
  - 📄 app.py
  - 📁 **templates**
    - 📄 index.html
- 📄 batch_index_cp_documents.py
- 📄 db.py
- 📁 **docs**
  - 📄 fis_502.html
  - 📄 fis_510.html
  - 📄 fis_520.html
  - 📄 fis_523.html
  - 📄 fis_524.html
  - 📄 fis_526.html
  - 📄 fis_534.html
  - 📄 fis_535.html
  - 📄 fis_540.html
  - 📄 fis_541.html
  - 📄 fis_542.html
  - 📄 fis_543.html
  - 📄 fis_563.html
  - 📄 fis_571.html
  - 📄 fis_573.html
- 📄 folder_structure.txt
- 📄 generate_readme.py
- 📄 main.py
- 📄 pinecone-key.pem.txt
- 📄 render.yaml
- 📄 requirements.txt
- 📄 run_uvicorn.bat
- 📁 **scripts**
  - 📄 .gitignore
  - 📄 __init__.py
  - 📄 embed_fis_to_pinecone.py
  - 📄 embed_runner.py
  - 📄 requirements.txt
  - 📄 test_pinecone_render.py
- 📁 **templates**
