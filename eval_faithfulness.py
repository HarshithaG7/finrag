from hybrid_search import load_all_chunks, build_bm25_index, vector_search, bm25_search, reciprocal_rank_fusion, rerank
from generate import generate_answer
from verify import verify_answer
from eval_set import eval_questions
from collections import defaultdict

if __name__ == "__main__":
    chunks = load_all_chunks()
    bm25 = build_bm25_index(chunks)
    chunk_lookup = {chunk["chunk_id"]: chunk for chunk in chunks}

    category_faithfulness = defaultdict(list)  # category -> list of (verified_count, total_count) per question

    for item in eval_questions:
        query = item["question"]

        # 1. retrieve + rerank (same as eval.py)
        vec_results = vector_search(query, n=20)
        bm25_results = bm25_search(query, bm25, chunks, n=20)
        fused = reciprocal_rank_fusion(vec_results, bm25_results)
        candidate_ids = [chunk_id for chunk_id, score in fused[:20]]
        top_chunks_scored = rerank(query, candidate_ids, chunk_lookup, top_n=5)
        top_chunks = [chunk_lookup[chunk_id] for chunk_id, score in top_chunks_scored]

        # 2. generate
        answer =generate_answer(query,top_chunks)  # call generate_answer with the right args

        # 3. verify
        results =verify_answer(answer,chunk_lookup)  # call verify_answer with the right args

        # 4. compute this question's faithfulness: verified claims / total claims
        total_claims = len(results)
        verified_claims = sum(1 for r in results if r["overall_verified"])
        # what if total_claims == 0? think about that edge case before moving on

        print(f"Q: {query}")
        if total_claims > 0:
            print(f"Claims: {verified_claims}/{total_claims} verified")
        else:
            print("Claims: 0 (no citations generated — likely out-of-scope)")
        print()

        if total_claims > 0:
            category_faithfulness[item["category"]].append((verified_claims, total_claims))

    print("=== Faithfulness by Category ===")
    for category, results in category_faithfulness.items():
        total_verified = sum(v for v, t in results)
        total_claims = sum(t for v, t in results)
        rate = total_verified / total_claims if total_claims > 0 else None # total_verified / total_claims, but watch for divide-by-zero
        if rate is not None:
            print(f"{category}: {rate:.2%} ({total_verified}/{total_claims} claims)")
        else:
            print(f"{category}: N/A (no claims generated)")