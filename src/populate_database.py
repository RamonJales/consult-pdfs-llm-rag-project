import argparse
import os
import shutil
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema.document import Document
from langchain_community.embeddings.ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from get_embedding_function import get_embedding_function

from dotenv import load_dotenv
load_dotenv()

def main():

    # Check if the database should be cleared (using the --clear flag).
    parser = argparse.ArgumentParser(description='Populate the database with documents')
    parser.add_argument("--reset", action="store_true", help='Reset the database')
    args = parser.parse_args()
    if args.reset:
        print("Clearing Database")
        clear_database()

    #Create(or update) the data store
    documents = load_documents()
    chunks = split_documents(documents)
    add_to_chroma(chunks)


def load_documents():
    document_loader = PyPDFDirectoryLoader(os.getenv("DATA_PATH"))
    return document_loader.load()


def split_documents(documents: list[Document]):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=80,
        length_function=len,
        is_separator_regex=False,
    )
    return text_splitter.split_documents(documents)


def add_to_chroma(chunks):
    #load the existing database
    db = Chroma(persist_directory=os.getenv("CHROMA_PATH"), 
                embedding_function=get_embedding_function())
    
    #calculate page ids
    chunks_with_ids = calculate_chunk_ids(chunks)

    #add or update documents
    existing_items = db.get(include=[])
    existing_ids = set(existing_items["ids"])
    print(f"Number of existing documents in DB: {len(existing_ids)}")

    #only add documents that dont exist in DB
    new_chunks = []
    for chunk in chunks_with_ids:
        if chunk.metadata["id"] not in existing_ids:
            new_chunks.append(chunk)
    
    if len(new_chunks):
        print (f"Adding {len(new_chunks)} new documents to DB")
        new_chunk_ids = [chunk.metadata["id"] for chunk in new_chunks]
        db.add_documents(new_chunks, ids = new_chunk_ids)
        # db.persist() is depreceated
    else:
        print("No new documents to add to DB")


def calculate_chunk_ids(chunks):
    # This will create IDs like "data/monopoly.pdf:6:2"
    # Page Source : Page Number : Chunk Index

    last_page_id = None
    current_chunk_index = 0

    for chunk in chunks:
        source = chunk.metadata.get("source")
        page = chunk.metadata.get("page")
        current_page_id = f"{source}:{page}"

        # If the page ID is the same as the last one, increment the index.
        if current_page_id == last_page_id:
            current_chunk_index += 1
        else:
            current_chunk_index = 0
        
         # Calculate the chunk ID.
        chunk_id = f"{current_page_id}:{current_chunk_index}"
        last_page_id = current_page_id

        # Add it to the page meta-data.
        chunk.metadata["id"] = chunk_id

    return chunks

    
def clear_database():
    if os.path.exists(os.getenv("CHROMA_PATH")):
        shutil.rmtree(os.getenv("CHROMA_PATH"))


if __name__ == "__main__":
    main()
