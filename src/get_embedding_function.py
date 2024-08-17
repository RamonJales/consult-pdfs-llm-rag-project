from langchain_community.embeddings.ollama import OllamaEmbeddings
import os
from dotenv import load_dotenv
load_dotenv()


def get_embedding_function():
    embeddings = OllamaEmbeddings(model=os.getenv("EMBEDDING_MODEL"))

    return embeddings
