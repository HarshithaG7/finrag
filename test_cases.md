# Stage 5 — Generation Testing Notes

Manual test queries run against the hybrid retrieval + citation-forced 
generation pipeline (Groq / llama-3.1-8b-instant), before verification 
layer (Stage 6) exists.

## Test 1: Well-scoped factual query
**Query:** "What are Tesla's main risks related to autonomous driving technology?"
**Answer:** " Tesla's main risks related to autonomous driving technology are the negative impact of unfavorable outcomes in claims and regulatory proceedings [TSLA_Item 14._67], regulatory scrutiny arising from or related to misuse or claimed failures or alleged misrepresentations of the technologies [TSLA_Item 14._67], and potential product liability claims related to the rare occasions when lithium-ion cells in their battery packs can rapidly release energy [TSLA_Item 14._67]. Additionally, there is a risk that the regulatory patchwork surrounding autonomous vehicles and an autonomous vehicle ride-hailing business in the U.S. [TSLA_Item 14._28] will hinder or complicate the development and introduction of their autonomous vehicle systems."
**Observation:** Good multi-citation answer, content is real and grounded
## Test 2:Cross-company comparison"
**Query:** "How do Apple and Microsoft describe regulatory scrutiny risks?"
**Answer:** "The technology industry, including Apple and Microsoft, is subject to intense media, political and regulatory scrutiny, which exposes the companies to increasing regulation, government investigations, legal actions and penalties [AAPL_Item 1A._42]. This scrutiny can result in changes to their business as they take actions to comply with legal and regulatory requirements, for example, implementing changes to iOS, iPadOS, the App Store, and Safari to comply with the Digital Markets Act in the EU [AAPL_Item 1A._42]."
**Observation:** Microsoft was actually not mentioned in the retrieved chunk. Flagged for future verification after stage 6.

## Test 3: Out-of-scope query (fallback test)
**Query:** "What is the company's plan to launch a cryptocurrency exchange?"
**Answer:** "No relevant information found in the context."
**Observation:** Fallback fired correctly.

## Test 4: [short label, e.g. "Precision/obscure figure query"]
**Query:** "What was Apple's total net sales for fiscal year 2024?"
**Answer:** "According to [AAPL_Item 8._15], Apple's total net sales for fiscal year 2024 was $391,035 million, and also according to [AAPL_Item 8._49] where the same figure can be found."
**Observation:** Figures retrieved accurately

## Key finding
While running the cross company query, the model retrieved info from Apple but labelled it as also from Microsoft. Though the info was accurate to Apple's records, the model added Microsoft to it which raises a concern laying the base for stage 6. Stage 6 proceeds to answer per claim whether the text in the cited chunk actually support this specific claim.

## Test 5: Longer multi-sentence answer (citation drift test)
**Query:** "What are Tesla's main risks related to autonomous driving technology?"
**Answer:** "Total net sales for fiscal year 2024 was $391,035 [AAPL_Item 8._1] [AAPL_Item 7._4] [AAPL_Item 8._15]. in Europe and other countries [TSLA_Item 14._28]. Additionally, the risk of vehicle crashes involving autonomous vehicles may lead to public attention and regulatory scrutiny, especially in light of NHTSA's Standing General Order [TSLA_Item 14._67]. Furthermore, electric vehicle adoption and market demand may be negatively affected by perception issues regarding features, quality, safety, performance, and cost [TSLA_Item 14._55]. If the market for electric vehicles does not develop as Tesla expects, it may harm their business, prospects, financial condition, and operating results. [TSLA_Item 14._67] [TSLA_Item 14._28] [TSLA_Item 14._55]."
**Observation:** Updated the prompt to require citations at the end of each sentence, immediately before the period. Most sentences followed this correctly, but on this longer, multi-sentence answer the model dropped the citation from one sentence ("If the market for electric vehicles does not develop...") and instead grouped three citations together in a dangling block at the very end, disconnected from any specific claim. This confirms that prompt instructions alone don't reliably hold formatting on longer generations, and motivates building the citation parser to tolerate this kind of drift (attaching dangling trailing citations to the preceding uncited sentence) rather than assuming strict one-citation-per-sentence formatting always holds.

## Test 6: Hallucinated chunk_id format (invalid citation test)
**Query:** "What are Tesla's main risks related to autonomous driving technology?"
**Answer:** "Tesla's main risks related to autonomous driving technology include claims and regulatory scrutiny arising from or related to misuse or claimed failures or alleged misrepresentations of the technologies that they are pioneering [TSLA_Item 67._] as well as regulatory challenges and restrictions on the testing, commercial operation, marketing, registration, and licensure of autonomous vehicles [TSLA_Item 28._]. Additionally, rapid release of energy from lithium-ion cells in Tesla's battery packs can cause fires and ignite nearby materials [TSLA_Item 67._] and could potentially harm the company's brand, growth, and operating results [TSLA_Item 55._]."
**Observation:** Running the same query multiple times can produce different citation formats — this run, the model scrambled the real chunk_id format (`TSLA_Item 14._67`) into a non-existent one (`TSLA_Item 67._`), effectively dropping the section number and reordering the parts. The parser itself extracted these citations correctly (no parsing bug), but the citations extracted do not correspond to any real chunk_id in the dataset. This is a more serious failure mode than the earlier citation-scope issue (Test 2) or citation-drift issue (Test 5), because it is silent: a chunk_id lookup on these values would simply fail. This directly motivates Stage 6's design: every citation must first be checked for existence in the chunk store (cheap check) before attempting NLI entailment (expensive check) — a citation pointing to a nonexistent chunk should be flagged immediately as invalid rather than skipped or ignored.

## Key finding (updated)
Across Stages 5-6 testing, three distinct citation failure modes were found: (1) a citation pointing to a real chunk that only partially supports the claim's scope (Test 2 — Microsoft over-attribution), (2) citations drifting to the end of a long answer, disconnected from their originating sentence (Test 5), and (3) a citation format that is entirely hallucinated and points to no real chunk at all (Test 6). Together these motivated a verification pipeline that checks, per citation: chunk_id validity first (cheap), then NLI entailment against the cited chunk's actual text (expensive) — rather than trusting the presence of a citation as proof of grounding.

## Test 7: End-to-end verification pipeline (parse -> existence check -> NLI)
**Query:** (same Test 2 answer, reused as a known test case)
**Answer:** "The technology industry, including Apple and Microsoft, is subject to intense media, political and regulatory scrutiny, which exposes the companies to increasing regulation, government investigations, legal actions and penalties [AAPL_Item 1A._42]. This scrutiny can result in changes to their business as they take actions to comply with legal and regulatory requirements, for example, implementing changes to iOS, iPadOS, the App Store, and Safari to comply with the Digital Markets Act in the EU [AAPL_Item 1A._42]."

**Verification results (model: cross-encoder/nli-roberta-base):**
- Claim 1 ("...including Apple and Microsoft..."): **neutral**, overall_verified = False
- Claim 2 ("...changes to iOS, iPadOS, the App Store, and Safari to comply with the DMA..."): **neutral**, overall_verified = False

**Observation:** Ran the full verify_answer pipeline (parse_citations -> chunk_id 
existence check -> NLI entailment) against the known Test 2 answer for the first 
time end to end.

Claim 1 is a correct catch: the cited chunk (AAPL_Item 1A._42) never mentions 
Microsoft, so "neutral" is the right call — this confirms the pipeline correctly 
catches citation scope mismatches automatically, without manual chunk reading.

Claim 2 is a false negative: manually re-reading the chunk text shows it contains 
a near word-for-word match for the claim ("...the Company has implemented changes 
to iOS, iPadOS, the App Store and Safari® in the EU as it seeks to comply with 
the Digital Markets Act ('DMA')..."). This should have scored as entailment. 
Likely cause: the cited chunk is a multi-sentence paragraph covering several 
unrelated points (general regulatory scrutiny, U.S. App Store changes, then the 
EU/DMA point), and the one sentence that actually supports the claim may be 
getting diluted by the surrounding, unrelated sentences in the premise. This is 
a known limitation of chunk-level NLI verification rather than a bug in the 
pipeline logic (parsing, existence checking, and wiring all functioned correctly).

## Key finding (updated again)
The end-to-end verification pipeline (parse -> chunk_id validity -> NLI 
entailment) correctly caught the Test 2 scope-mismatch bug automatically, 
confirming the core approach works. It also surfaced a new, honest limitation: 
NLI entailment can produce false negatives on long, multi-topic chunks where 
the supporting sentence is only a small part of the premise — a real tradeoff 
of verifying at chunk granularity rather than sentence granularity, worth 
noting as a known limitation rather than a design flaw.

## Test 8: Number extraction regex — edge case with "10-K"
**Test input:** extract_numbers() run against two strings:
1. "Total net sales for fiscal year 2024 was $391,035 million"
2. "10-K | 13 The technology industry, including, in some instances, the Company"

**Output:**
1. ['2024', '$391,035']
2. ['10', '13']

**Observation:** The regex `\$?\d[\d,]*\.?\d*` correctly extracts real financial 
figures like $391,035, but has two known limitations:
1. It also extracts plain years (e.g. "2024") as numbers, which are not 
   financial figures worth numeric-consistency checking — low risk, but adds 
   noise to comparisons.
2. It incorrectly splits "10-K" (a document type name, not a number) into the 
   standalone number "10", since the regex has no way to distinguish a number 
   followed by a letter (forming a term) from a genuine standalone figure.

This is a known limitation, not yet fixed. Risk is currently low because "10-K" 
has only appeared in premise/chunk boilerplate text so far, not inside any 
LLM-generated claim tested to date — but if a future claim referenced "10-K" 
directly, this could cause a spurious number-match false positive in the 
consistency check. Documented here as a candidate future improvement 
(e.g. excluding number-letter compound terms via a negative lookahead) rather 
than fixed now, to keep Stage 6 moving.

## Test 9: Numeric consistency fix + persistent NLI dilution limitation
**Query:** "What was Apple's total net sales for fiscal year 2024?"
**Generated answer:** "Total net sales for fiscal year 2024 was $391,035 [AAPL_Item 8._49] [AAPL_Item 7._4]."

**Before fix:** check_numeric_consistency flagged $391,035 as a mismatch against 
a real chunk (AAPL_Item 8._1) that does contain this figure. Root cause: the 
chunk's raw text came from a flattened financial statement table where dollar 
signs are stripped during extraction ("Total net sales 416,161 391,035383,285"), 
so the premise's number appeared as bare "391,035" with no "$", while the claim's 
number appeared as "$391,035" (added by the LLM's own phrasing). The exact string 
comparison failed on the "$" difference alone.

**Fix applied:** added normalize_number() to strip "$" and "," from both claim 
and premise numbers before comparing, so "$391,035" and "391,035" are correctly 
recognized as the same figure.

**After fix:** numeric_consistent: True for both citations — the correct result, 
confirming the real figure is accurately reflected in the generated claim.

**Remaining limitation (not fixed, documented):** overall_verified is still 
False, because both citations returned NLI status "neutral" rather than 
"entailment" — the same dilution pattern first found in Test 7. The chunks here 
are dense financial statement tables covering many line items (net sales, cost 
of sales, operating income, EPS, etc.), and the NLI model does not confidently 
recognize a single correct figure buried in that density as full entailment. 
This means the pipeline can now correctly confirm a number is accurate 
(numeric check) while still under-scoring the claim's overall verification 
status (NLI check) — a mismatch between the two checks that's worth being 
explicit about rather than silently averaging away.

## Key finding (final, Stage 6)
Stage 6's two-check design (NLI entailment + numeric consistency) catches 
distinct, real failure modes independently: NLI catches scope/context 
mismatches (Test 2, Test 7) that numeric checking would miss entirely, while 
numeric checking catches exact-figure errors (validated via the corrected 
$400,000 mismatch test) that NLI's semantic flexibility can miss. However, 
both checks have known, documented limitations: NLI produces false negatives 
on long, dense, multi-topic premises (Tests 7 and 9), and numeric extraction 
can be defeated by upstream text-extraction artifacts like merged table 
columns (Test 9). These limitations are inherent to the underlying models and 
raw filing data, not bugs in the verification logic itself, and are documented 
here as known, honestly-reported constraints of the system rather than hidden 
or silently patched over.

## Test 10: Section-boundary case-sensitivity bug (Tesla Item 14 mislabeling, resolved)
**Background:** Since Stage 2, Tesla's autonomous driving / FSD / Robotaxi content 
was consistently mislabeled as "Item 14." instead of its correct section 
(Item 1 / Item 1A), and this was documented as an accepted known limitation. 
Investigated properly while fixing the Stage 1 table-extraction bug.

**Root cause:** `find_section_boundaries` searched for exact-case section titles 
like "Item 14." using `text.rfind()`. Tesla's actual 10-K writes section headers 
in all-caps (e.g. "ITEM 14. PRINCIPAL ACCOUNTANT FEES AND SERVICES"), which never 
matches a mixed-case search string. The only place "Item 14." (mixed case) 
appeared anywhere in the document was inside the Table of Contents — so `.rfind()` 
fell back to that early, incorrect position every time, and everything from there 
until the next successfully-matched section got swept into "Item 14," including 
large amounts of real Item 1/Item 1A content (autonomous driving, FSD, Robotaxi, 
risk factors).

**Fix:** replaced the exact-match `.rfind()` search with a case-insensitive 
`re.finditer(re.escape(title), text, re.IGNORECASE)`, taking the last match 
(`matches[-1]`) to preserve the original intent of avoiding the Table of Contents 
occurrence in sections where a later, correctly-cased real header exists.

**Verification:** re-ran chunker.py and embed_store.py (after deleting and 
rebuilding chroma_db — see note below) and re-ran the same autonomous-driving 
search query used in Stage 3's original validation. All 5 top results are now 
correctly labeled Item 1. or Item 1A., with zero Item 14. mislabeling.

**Side lesson (Chroma rebuild):** re-running `embed_store.py` without first 
deleting the existing `chroma_db` folder appends new chunks on top of old ones 
rather than replacing them, since `store_chunks` only calls `collection.add()`. 
This caused a temporary duplicate/stale-data issue (1721 chunks instead of the 
expected 1038) until `chroma_db` was deleted and rebuilt fresh. Going forward, 
`chroma_db` must be deleted before any re-run of `embed_store.py` following a 
change to chunking or extraction logic.

## Key finding (final)
A limitation accepted early in the project (Stage 2) turned out to have a real, 
fixable root cause — case sensitivity in section-header matching — once properly 
investigated rather than left as a documented workaround. This is a good example 
of revisiting "acceptable" limitations when the underlying system evolves (in 
this case, prompted by fixing an unrelated extraction bug), rather than assuming 
early technical debt is permanent.