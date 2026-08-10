import chromadb
from rank_bm25 import BM25Okapi
import numpy as np
from sentence_transformers import SentenceTransformer
from sentence_transformers import CrossEncoder

reranker=CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
model = SentenceTransformer('BAAI/bge-small-en-v1.5')
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection(name="filings")

def load_all_chunks():
    results=collection.get()
    chunks=[]
    for i in range(len(results["ids"])):
        chunks.append({
            "chunk_id":results["ids"][i],
            "company":results["metadatas"][i]["company"],
            "section":results["metadatas"][i]["section"],
            "text":results["documents"][i]
        })
    return chunks

def build_bm25_index(chunks):
    tokenized_corpus=[chunk["text"].lower().split() for chunk in chunks]
    bm25=BM25Okapi(tokenized_corpus)
    return bm25

def vector_search(query,n=20):
    query_vector=model.encode(query).tolist()
    results=collection.query(
        query_embeddings=[query_vector],
        n_results=n
    )
    chunk_ids=results["ids"][0]
    return chunk_ids

def bm25_search(query,bm25,chunks,n=20):
    tokenized_query=query.lower().split()
    scores=bm25.get_scores(tokenized_query)
    top_indices=np.argsort(scores)[::-1][:n]
    chunk_ids=[chunks[idx]["chunk_id"] for idx in top_indices]
    return chunk_ids

def reciprocal_rank_fusion(vector_results,bm25_results,k=60):
    """
    vector_results: list of chunk_ids in rank order from vector search
    bm25_results: list of chunk_ids in rank order from BM25 search
    """
    scores={}
    for rank,chunk_id in enumerate(vector_results):
        scores[chunk_id]=scores.get(chunk_id,0)+1/(k+rank+1)
    for rank,chunk_id in enumerate(bm25_results):
        scores[chunk_id]=scores.get(chunk_id,0)+1/(k+rank+1)
    ranked=sorted(scores.items(),key=lambda x:x[1],reverse=True)
    return ranked

def rerank(query,candidate_chunk_ids,chunk_lookup,top_n=5):
    pairs=[(query,chunk_lookup[chunk_id]["text"]) for chunk_id in candidate_chunk_ids]
    scores=reranker.predict(pairs)
    scored=list(zip(candidate_chunk_ids,scores))
    scored.sort(key=lambda x:x[1],reverse=True)
    return scored[:top_n]

if __name__ == "__main__":
    chunks = load_all_chunks()
    print("Total chunks loaded:", len(chunks))
    bm25 = build_bm25_index(chunks)
    
    query = "digital markets act investigation"
    vec_results = vector_search(query, n=20)
    bm25_results = bm25_search(query, bm25, chunks, n=20)
    fused=reciprocal_rank_fusion(vec_results, bm25_results)
    chunk_lookup = {c["chunk_id"]: c for c in chunks}
    candidate_ids = [chunk_id for chunk_id, score in fused[:20]]
    reranked = rerank(query, candidate_ids, chunk_lookup, top_n=5)
    
    print("--- Top 5 after hybrid fusion ---")
    for chunk_id, score in fused[:5]:
        c = chunk_lookup[chunk_id]
        print(f"Score: {score:.4f} | {c['company']} | {c['section']}")
        print(c["text"][:200])
        print()
    print("--- Top 5 after reranking ---")
    for chunk_id, score in reranked:
        c = chunk_lookup[chunk_id]
        print(f"Rerank score: {score:.4f} | {c['company']} | {c['section']}")
        print(c["text"][:200])
        print() 