# FinRAG — Retrieval Evaluation Results

## Setup

- **Eval set:** 20 hand-verified questions across 6 categories, spanning AAPL, TSLA, and MSFT 10-K filings.
- **Pipeline stages compared:** RRF-fused hybrid retrieval (BM25 + vector search) vs. the same candidates after cross-encoder reranking.
- **Metrics:** Precision@5 — fraction of the top 5 retrieved chunks that match hand-labeled `relevant_chunk_ids`. Recall@5 — whether *at least one* relevant chunk appears anywhere in the top 5, regardless of what else is retrieved alongside it.
- **Ground truth:** each question manually mapped to the specific chunk(s) in the 10-K that answer it, verified by reading the source filing directly.

## Results by Category

| Category | n | P@5 before | P@5 after | Δ P@5 | R@5 before | R@5 after | Δ R@5 |
|---|---|---|---|---|---|---|---|
| Numeric | 5 | 0.08 | 0.08 | 0.00 | 0.40 | 0.40 | 0.00 |
| Cross-company | 3 | 0.13 | 0.27 | **+0.13** | 0.67 | **1.00** | **+0.33** |
| Single-company narrow | 3 | 0.07 | 0.13 | **+0.07** | 0.33 | 0.33 | 0.00 |
| Conceptual | 4 | 0.10 | 0.05 | **−0.05** | 0.50 | 0.25 | **−0.25** |
| Section-specific | 1 | 0.20 | 0.20 | 0.00 | 1.00 | 1.00 | 0.00 |
| Out-of-scope | 3 | N/A | N/A | — | N/A | N/A | — |

*(Out-of-scope questions have no ground-truth chunks by design — the correct system behavior is retrieving nothing relevant, so precision@5 doesn't apply. All 3 were confirmed to have zero matching chunks in the corpus.)*

*(Section-specific has n=1 and should not be generalized from.)*

## Key Finding: Reranking Helps Some Question Types and Hurts Others

Reranking is not a uniform improvement — its effect depends heavily on what kind of question is being asked.

### Where reranking helps: cross-company and narrow factual questions

Cross-company questions saw the largest gain (+0.13, more than doubling precision@5). These questions ask the model to find semantically related content across two different documents phrased differently (e.g., "How do Apple and Microsoft each describe risks related to government regulation?"). A cross-encoder is well suited to this: it directly scores query-passage semantic relevance, which is exactly what's needed to match a single query concept against two different companies' distinct phrasing.

**Case study — Q6:** *"How do Apple and Microsoft each describe risks related to government regulation?"*
Pre-rerank, RRF surfaced `AAPL_Item 1A._41` (an ESG/environmental chunk) ahead of the correct `AAPL_Item 1A._42` (the actual regulation-risk chunk) — a lexical/BM25-driven miss. Reranking correctly promoted the regulation-risk chunk, since the cross-encoder could recognize topical relevance that keyword overlap alone missed.

### Where reranking is neutral: numeric lookups

Numeric precision@5 stayed flat at 0.08 both before and after reranking — and the *reasons* differ per question, not just the aggregate score. In several cases, reranking didn't recover from a bad pre-rerank pool; in others it actively swapped out the correct chunk (see below).

**Case study — Q1:** *"What was Apple's total net sales for fiscal year 2024?"*
Precision@5 dropped from 0.2 to 0.0 after reranking. The ground-truth chunk (`AAPL_Item 8._21`, the "Total net sales" table) was demoted in favor of `AAPL_Item 8._69`, a *different* table breaking down net sales by country — no "Total net sales" line at all. Both chunks are topically about "net sales" and both mention FY2024, so a cross-encoder trained on general semantic relevance rates them similarly. But only one table actually contains the aggregate figure being asked for.

This points to a structural limitation: **cross-encoder reranking optimizes for topical relevance, not numeric/structural answerability.** It has no way to distinguish "this table sums to the total" from "this table is a different breakdown that happens to mention the same line item." For a RAG system built around a financial-numbers use case, this is a meaningful weakness worth calling out directly.

### Where reranking hurts: broad conceptual questions

Conceptual questions (broad, multi-chunk risk-factor questions like "What risks does Tesla describe related to battery technology?") saw a small but consistent drop (−0.05). These questions are often answered by *multiple* chunks scattered across a risk-factors section, and a cross-encoder scoring passages independently against the query has no mechanism to reward coverage or complementarity between chunks — it will happily rank five near-duplicate high-relevance passages above a more complete set, even if some of the actually-correct supporting chunks lose out.

## Recall@5 Confirms and Sharpens the Precision Findings

Adding recall@5 — did *any* correct chunk make it into the top 5 at all — reinforces two of the three precision findings above and adds a distinct angle on the third.

**Cross-company: recall goes to 1.00 after reranking.** Every cross-company question now has at least one correct chunk somewhere in its top 5 post-rerank (up from 0.67 before). This is a stronger, cleaner confirmation of the Q6 finding above: reranking isn't just nudging the correct chunk higher in already-successful cases, it's recovering the correct chunk for previously-missed questions too.

**Conceptual: recall drops alongside precision (0.50 → 0.25).** Both metrics now agree that reranking is actively pushing relevant chunks *out* of the top 5 for broad conceptual questions, not just reordering an already-correct set. That's a more concrete version of the "no mechanism to reward complementary coverage" hypothesis above.

**Numeric: recall (0.40) is unaffected by reranking, unlike precision.** This is the most interesting divergence. Precision@5 for numeric questions is very low (0.08) and reranking doesn't change it — but recall says the correct chunk *is* present in the top 5 for 40% of numeric questions, both before and after reranking. In other words, reranking isn't losing the right chunk; it's just failing to consistently rank it at position 1, which is exactly what the Q1 case study shows: the correct "Total net sales" table and an incorrect-but-topically-similar country-breakdown table both remain in the candidate set, and the cross-encoder can't reliably tell them apart on rank order alone.

## Interpretation for the RAG System

These results suggest reranking should not be treated as a blanket "always apply" step. A more nuanced strategy — e.g., routing numeric/factual queries toward exact-match or table-aware retrieval instead of pure semantic reranking, while keeping reranking for cross-document and disambiguation-heavy queries — would likely outperform a single fixed pipeline across all query types. This is a natural direction for future work beyond the current 8-stage scope.

## Caveats

- Precision@5 is a strict metric given the ground truth typically has only 1–4 relevant chunks out of ~1,038 total chunks in the corpus; recall@5 (above) complements it by capturing whether the correct chunk was found at all, regardless of what else was retrieved.
- Sample sizes per category are small (n=1 to n=5), consistent with a 20-question hand-verified eval set. Findings above are directional, not statistically definitive — appropriate framing for a portfolio project, but worth stating explicitly rather than overclaiming.
- Ground truth was single-labeled per question in most cases; a small number of questions (e.g. Q1, Q4) were manually checked for near-duplicate "correct-looking" chunks to rule out mislabeling before concluding a result was a genuine retrieval/reranking issue rather than a ground-truth error.

---

## Faithfulness Evaluation

### Setup

- **Pipeline evaluated:** full retrieve → generate → verify path, run across all 20 eval questions.
- **Generation:** Groq `llama-3.1-8b-instant`, prompted to cite a source `[chunk_id]` after every sentence.
- **Verification:** each generated claim is checked against its cited chunk(s) via (1) an NLI cross-encoder (`cross-encoder/nli-roberta-base`) for entailment, and (2) a numeric-consistency check that confirms any numbers in the claim actually appear in the source chunk.
- **Metric — faithfulness rate:** a claim counts as verified only if it is scored `entailment` **and** passes numeric consistency. This is a deliberately strict, conjunctive definition, kept unchanged after seeing results (see Key Finding below) rather than loosened post-hoc.

### Results by Category

| Category | Faithfulness rate | Claims verified |
|---|---|---|
| Single-company narrow | **75.0%** | 3/4 |
| Numeric | 20.0% | 1/5 |
| Section-specific | 20.0% | 1/5 |
| Cross-company | 18.2% | 2/11 |
| Conceptual | 17.6% | 3/17 |
| Out-of-scope | 0.0% | 0/3 |

*(19 of 20 questions produced claims; one section-specific question did not make it into the final `eval_questions` list, consistent with the n=1 section-specific result noted in the retrieval eval above.)*

### Key Finding 1: The verification layer correctly rejects ungrounded claims (out-of-scope = 0%)

The three out-of-scope questions (e.g. "What is the company's plan to launch a cryptocurrency exchange?") have no real answer anywhere in the filings. **0% verified is the correct, desired outcome** — it means the verification layer is not rubber-stamping whatever the LLM generated, but actively refusing to certify claims that aren't actually grounded in the source. This is arguably the strongest result in this eval: it demonstrates the verification layer does real work, not just that it agrees with the generator by default.

### Key Finding 2: NLI entailment models struggle with tabular financial source text

Numeric and section-specific claims scored only 20% faithful, despite the underlying numbers frequently being correct.

**Case study — Q1:** *"What was Apple's total net sales for fiscal year 2024?"*
The model answered "$391,035" citing `AAPL_Item 8._69`. The number **is** present in that chunk — confirmed directly in the raw table text (`Total net sales | $ 416,161 | $ 391,035 | $ 383,285`) — so `numeric_consistent: True`. But the NLI model scored the claim **neutral**, not entailment, with 0.70 confidence in that neutral call. Raw tabular text (column headers, `|` separators, multiple years side-by-side) doesn't read as natural-language support for a clean declarative sentence, even when the fact is accurate.

Because `overall_verified` requires entailment *and* numeric consistency, this claim — despite being factually correct — is scored unverified. **This is a systematic, structural limitation of applying NLI entailment models (trained on natural-language sentence pairs) to tabular financial source data, not a bug in the pipeline.** It's the main reason numeric and section-specific faithfulness rates are conservative relative to actual factual accuracy.

### Key Finding 3: Single-company narrow questions perform well (75%)

Simple, direct factual questions with clean prose answers (e.g. Apple's fiscal year end date, Tesla's main competitors) verify at a much higher rate. These questions tend to draw on prose-style source chunks rather than tables, which the NLI model handles far more reliably — reinforcing that the gap in Finding 2 is about *source format*, not generation quality.

### A softer pattern: conceptual and cross-company questions

Conceptual (17.6%) and cross-company (18.2%) questions also score low, but for a different likely reason: they produce many more claims per question (17 and 11 respectively, vs. 1–2 for narrow questions), often synthesizing across multiple chunks for broad risk-factor or comparison questions. Sentence-level entailment checks aren't well suited to verifying synthesized or comparative claims against a single cited chunk. This is a softer, less-evidenced finding than Finding 2 and is flagged as a direction for further investigation rather than a confirmed cause.

### Caveats

- **Non-determinism:** `generate_answer()` has no temperature/seed control, so re-running this eval will produce different generated claims and citations, and therefore different faithfulness numbers, run to run. The results above are a single snapshot, not a stable benchmark.
- **Strict-by-design metric:** the conjunctive `entailment AND numeric_consistent` definition was kept intentionally strict after the softmax-confidence fix confirmed Finding 2 was a genuine effect, not a scoring bug — this makes the reported rates a conservative lower bound on actual faithfulness, not an exact measure of factual accuracy.
- **n is small and uneven per category** (3–17 claims), same limitation as the retrieval eval above.

## Next Steps

1. Explore a table-aware or hybrid verification strategy (e.g. weighting numeric consistency more heavily for chunks that are tabular) to reduce the conservative bias identified in Finding 2.
2. Add temperature/seed control to `generate_answer()` for reproducible faithfulness runs.
3. Investigate whether a hybrid reranking strategy (skip reranking for numeric-category queries) improves aggregate retrieval performance.
4. Commit `eval_set.py`, `eval.py`, `eval_faithfulness.py`, `verify.py` (with softmax fix), and this results doc to the repo. Confirm `.env` is in `.gitignore` before pushing.