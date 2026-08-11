from sentence_transformers import CrossEncoder

from generate import parse_citations
nli_model=CrossEncoder("cross-encoder/nli-roberta-base")

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
        citation_result.append({
            "chunk_id":chunk_id,
            "status":label,
            "confidence":float(confidence)
        })
    overall_verified=any(r["status"] == "entailment" for r in citation_result)
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

if __name__ == "__main__":
    print(nli_model.model.config.id2label)
    from hybrid_search import load_all_chunks
    from generate import generate_answer, build_prompt, parse_citations  # whatever you need to produce a real answer
        
    chunks = load_all_chunks()
    chunk_lookup = {chunk["chunk_id"]: chunk for chunk in chunks}
        
        # reuse one of your real test answers, e.g. paste in the Test 2 answer directly
        # rather than regenerating it, so you're checking against a KNOWN case:
    answer_text = "The technology industry, including Apple and Microsoft, is subject to intense media, political and regulatory scrutiny, which exposes the companies to increasing regulation, government investigations, legal actions and penalties [AAPL_Item 1A._42]. This scrutiny can result in changes to their business as they take actions to comply with legal and regulatory requirements, for example, implementing changes to iOS, iPadOS, the App Store, and Safari to comply with the Digital Markets Act in the EU [AAPL_Item 1A._42]."
        
    results = verify_answer(answer_text, chunk_lookup)
    for r in results:
        print(r)
        print()