from sentence_transformers import SentenceTransformer
import chromadb
model=SentenceTransformer('BAAI/bge-small-en-v1.5')
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection(name="filings")

def embed_chunks(chunks):
    list_of_texts=[chunk["text"] for chunk in chunks]
    embeddings=model.encode(list_of_texts)
    return embeddings

def store_chunks(chunks,vectors):
    collection.add(ids=[chunk["chunk_id"] for chunk in chunks],
                   metadatas=[{"company":chunk["company"],"section":chunk["section"]} for chunk in chunks],
                   documents=[chunk["text"] for chunk in chunks],
                   embeddings=[vector.tolist() for vector in vectors])
def search(query, n_results=5):
    query_vector = model.encode(query).tolist()
    results = collection.query(
        query_embeddings=[query_vector],
        n_results=n_results
    )
    return results

if __name__ == "__main__":
    import sys
    sys.path.append(".")  # so we can import from chunker.py
    from chunker import chunk_filing
    
    for ticker in ["AAPL", "TSLA", "MSFT"]:
        with open(f"{ticker}_extracted_text.txt", "r", encoding="utf-8") as f:
            text = f.read()
        
        chunks = chunk_filing(text, ticker)
        vectors = embed_chunks(chunks)
        store_chunks(chunks, vectors)
        print(f"{ticker}: stored {len(chunks)} chunks")
    
    print("Total in collection:", collection.count())
    results = search("What risks does the company face related to autonomous driving or self-driving technology?")
    for i in range(len(results["documents"][0])):
        print(f"--- Result {i+1} ---")
        print("Company:", results["metadatas"][0][i]["company"])
        print("Section:", results["metadatas"][0][i]["section"])
        print(results["documents"][0][i][:300])
        print()