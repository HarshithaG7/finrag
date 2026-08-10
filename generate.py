import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
client=Groq(api_key=os.environ.get("GROQ_API_KEY"))


def build_prompt(query,chunks):
    context=""
    for chunk in chunks:
        context+=f"[{chunk['chunk_id']}]: {chunk['text']}\n\n"

    prompt=f"""
    You are a helpful assistant that answers questions ONLY using the given context chunks. After every factual claim, cite the chunk_id it came from, in square bracket, Cite using the exact chunk_id shown in brackets before each context passage, e.g. [AAPL_Item 3._0]. If the answer combines two or more chunks, cite all relevant chunk_ids, e.g. [AAPL_Item 3._0] [MSFT_Item 5._2]. If the context does not contain the answer, say "No relevant information found in the context." Do not make up any information.

    Context:
    {context}
    Question: {query}
    Answer:
    """
    return prompt

def generate_answer(query,chunks):
    prompt=build_prompt(query,chunks)
    response=client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content

if __name__ =="__main__":
    from hybrid_search import load_all_chunks,build_bm25_index, vector_search, bm25_search, reciprocal_rank_fusion, rerank
    chunks = load_all_chunks()
    bm25=build_bm25_index(chunks)
    chunk_lookup={chunk["chunk_id"]:chunk for chunk in chunks}

    query="What was Apple's total net sales for fiscal year 2024?"
    vec_results=vector_search(query,n=20)
    bm25_results=bm25_search(query,bm25,chunks,n=20)
    fused=reciprocal_rank_fusion(vec_results,bm25_results)

    candidate_ids=[chunk_id for chunk_id,score in fused[:20]]
    top_chunks_stored=rerank(query,candidate_ids,chunk_lookup,top_n=5)

    top_chunks=[chunk_lookup[chunk_id] for chunk_id,score in top_chunks_stored]
    answer=generate_answer(query,top_chunks)
    print("Answer:",answer)
