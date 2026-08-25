from hybrid_search import load_all_chunks, build_bm25_index, vector_search, bm25_search, reciprocal_rank_fusion, rerank
from eval_set import eval_questions
from collections import defaultdict  
DEBUG=False

def precision_at_5(retrieved_ids,relevant_ids):
    if not relevant_ids:
        return None
    top_5=retrieved_ids[:5]
    hits=0
    for id in top_5:
        if id in relevant_ids:
            hits+=1
    return hits/5
def recall_at_5(retrieved_ids,relevant_ids):
    if not relevant_ids:
        return None
    top_5=retrieved_ids[:5]
    return any(id in relevant_ids for id in top_5)

if __name__ == "__main__":
    chunks = load_all_chunks()
    bm25 = build_bm25_index(chunks)
    chunk_lookup = {chunk["chunk_id"]: chunk for chunk in chunks}
    category_results = defaultdict(list) 

    for item in eval_questions:
        query = item["question"]
        vec_results = vector_search(query, n=20)
        bm25_results = bm25_search(query, bm25, chunks, n=20)
        fused = reciprocal_rank_fusion(vec_results, bm25_results)
        fused_ids = [chunk_id for chunk_id, score in fused]

        # before reranking
        p5_before = precision_at_5(fused_ids, item["relevant_chunk_ids"])
        r5_before=recall_at_5(fused_ids,item["relevant_chunk_ids"])
        # after reranking — rerank takes the fused candidates and re-scores them
        reranked_ids = rerank(query, fused_ids, chunk_lookup, top_n=5)
    
        if DEBUG and item["category"] == "numeric":
            print("GROUND TRUTH chunk text:")
            for cid in item["relevant_chunk_ids"]:
                print(chunk_lookup[cid]["text"][:500])
            print()
            print("TOP RERANKED chunk text:")
            print(chunk_lookup[reranked_ids[0][0]]["text"][:500])
        reranked_ids_only = [chunk_id for chunk_id, score in reranked_ids]
        
        p5_after = precision_at_5(reranked_ids_only, item["relevant_chunk_ids"])
        r5_after=recall_at_5(reranked_ids_only,item["relevant_chunk_ids"])
        if item["relevant_chunk_ids"]:
            category_results[item["category"]].append((p5_before,p5_after,r5_before,r5_after
                                                       ))

        print(f"Q: {query}")
        print(f"Category: {item['category']}")
        print(f"Precision@5 (before rerank): {p5_before}")
        print(f"Precision@5 (after rerank):  {p5_after}")
        print()

    print("\n=== Category Averages ===")
    for category, results in category_results.items():
        before_avg_p5 = sum(r[0] for r in results) / len(results)
        after_avg_p5 = sum(r[1] for r in results) / len(results)
        before_avg_r5 = sum(r[2] for r in results) / len(results)
        after_avg_r5 = sum(r[3] for r in results) / len(results)
        print(f"{category}: P5 before={before_avg_p5:.2f}, after={after_avg_p5:.2f} | R5 before={before_avg_r5:.2f}, after={after_avg_r5:.2f}, n={len(results)}")