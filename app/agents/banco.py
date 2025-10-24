import chromadb
from chromadb.config import Settings

client = chromadb.Client(Settings(persist_directory="/docs/my_db"))

collection = client.create_collection(name="chat_context")

count = collection.count()
print(count)