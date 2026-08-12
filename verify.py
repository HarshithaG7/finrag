from sentence_transformers import CrossEncoder

from generate import parse_citations
nli_model=CrossEncoder("cross-encoder/nli-roberta-base")
import re

def check_entailment(premise,hypothesis):
    result=nli_model.predict([(premise,hypothesis)])
    scores=result[0]
    labels=["contradiction","entailment","neutral"]
    best_index=scores.argmax()
    best_label=labels[best_index]
    confidence=scores[best_index]
    return best_label,confidence

def verify_claim(claim_dict,chunk_lookup):
    claim=claim_dict["claim"]
    citation_result=[]
    for chunk_id in claim_dict["citations"]:
        if chunk_id not in chunk_lookup:
            citation_result.append({
                "chunk_id":chunk_id,
                "status":"invalid_chunk_id"
            })
            continue
        premise=chunk_lookup[chunk_id]["text"]
        label,confidence=check_entailment(premise,claim)
        numeric_consistent, mismatches = check_numeric_consistency(premise, claim)
        citation_result.append({
            "chunk_id": chunk_id,
            "status": label,
            "confidence": float(confidence),
            "numeric_consistent": numeric_consistent,
            "numeric_mismatches": mismatches
        })
    overall_verified = any(
        r["status"] == "entailment" and r.get("numeric_consistent", True)
        for r in citation_result
    )
    return {
        "claim":claim,
        "citations":citation_result,
        "overall_verified":overall_verified
    }

def verify_answer(answer_text,chunk_lookup):
    parsed_claims=parse_citations(answer_text)
    verification_results=[]
    for claim_dict in parsed_claims:
        result=verify_claim(claim_dict,chunk_lookup)
        verification_results.append(result)
    return verification_results

def extract_numbers(text):
    raw_matches=re.findall(r'\$?\d[\d,]*\.?\d*', text)
    return raw_matches

def normalize_number(num_str):
    return num_str.replace("$", "").replace(",", "")

def check_numeric_consistency(premise, claim):
    claim_numbers = extract_numbers(claim)
    premise_numbers = extract_numbers(premise)
    
    normalized_premise = [normalize_number(n) for n in premise_numbers]
    
    if not claim_numbers:
        return True, []
    
    mismatches = []
    for num in claim_numbers:
        if normalize_number(num) not in normalized_premise:
            mismatches.append(num)
    
    consistent = len(mismatches) == 0
    return consistent, mismatches

if __name__ == "__main__":
    from hybrid_search import load_all_chunks
    from generate import generate_answer, build_prompt, parse_citations

    # confirm NLI label order (already verified, kept here for reference)
    print(nli_model.model.config.id2label)

    chunks = load_all_chunks()
    chunk_lookup = {chunk["chunk_id"]: chunk for chunk in chunks}

    print("--- Full pipeline test: real query with a number ---")
    from hybrid_search import build_bm25_index, vector_search, bm25_search, reciprocal_rank_fusion, rerank

    bm25 = build_bm25_index(chunks)
    query = "What was Apple's total net sales for fiscal year 2024?"

    vec_results = vector_search(query, n=20)
    bm25_results = bm25_search(query, bm25, chunks, n=20)
    fused = reciprocal_rank_fusion(vec_results, bm25_results)
    candidate_ids = [chunk_id for chunk_id, score in fused[:20]]
    top_chunks_scored = rerank(query, candidate_ids, chunk_lookup, top_n=5)
    top_chunks = [chunk_lookup[chunk_id] for chunk_id, score in top_chunks_scored]

    answer = generate_answer(query, top_chunks)
    print("Generated answer:", answer)
    print()

    real_results = verify_answer(answer, chunk_lookup)
    for r in real_results:
        print(r)
        print()
    