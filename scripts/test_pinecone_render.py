import os
from pinecone import Pinecone

# Initialize Pinecone (new SDK v3+)
pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])

# Try listing indexes to verify connectivity
print("✅ Pinecone connected!")
print("Indexes:", pc.list_indexes().names())
