eval_questions = [
    {
        "question": "What was Apple's total net sales for fiscal year 2024?",
        "relevant_chunk_ids": ["AAPL_Item 8._21"],
        "category": "numeric"
    },
    {
        "question": "How do Apple and Microsoft each describe risks related to government regulation?",
        "relevant_chunk_ids": ["AAPL_Item 1A._42", "MSFT_Item 1A._55"],
        "category": "cross_company"
    },
    {
        "question": "What is the company's plan to launch a cryptocurrency exchange?",
        "relevant_chunk_ids": [],
        "category": "out_of_scope"
    },
    {
        "question": "What was Apple's research and development spending for fiscal year 2024?",
        "relevant_chunk_ids": ["AAPL_Item 7._10", "AAPL_Item 8._2"],
        "category": "numeric"
    },
    {
        "question": "What is Apple's fiscal year end date?",
        "relevant_chunk_ids": ["AAPL_Item 1._0"],
        "category": "single_company_narrow"
    },
    {
        "question": "What risks does Apple describe related to its supply chain and manufacturing?",
        "relevant_chunk_ids": ["AAPL_Item 1A._15", "AAPL_Item 1A._16", "AAPL_Item 1A._17"],
        "category": "conceptual"
    },
    {
        "question": "According to Item 7, what does Apple's management discussion say about net sales trends?",
        "relevant_chunk_ids": ["AAPL_Item 7._5", "AAPL_Item 7._7"],
        "category": "section_specific"
    },
    {
        "question": "What was Microsoft's total revenue for fiscal year 2025?",
        "relevant_chunk_ids": ["MSFT_Item 8._0"],
        "category": "numeric"
    },
    {
        "question": "What was Microsoft's net income for the most recent fiscal year?",
        "relevant_chunk_ids": ["MSFT_Item 8._4"],
        "category": "numeric"
    },
    {
        "question": "What competitive risks does Microsoft describe in its cloud computing business?",
        "relevant_chunk_ids": ["MSFT_Item 1A._5", "MSFT_Item 1A._11"],
        "category": "conceptual"
    },
    {
        "question": "What products does Microsoft mention in its business overview?",
        "relevant_chunk_ids": ["MSFT_Item 1._7", "MSFT_Item 1._12", "MSFT_Item 1._16"],
        "category": "single_company_narrow"
    },
    {
        "question": "What was Tesla's total automotive revenue?",
        "relevant_chunk_ids": ["TSLA_Item 8._15"],
        "category": "numeric"
    },
    {
        "question": "What risks does Tesla describe related to battery technology and lithium-ion cells?",
        "relevant_chunk_ids": ["TSLA_Item 1A._12", "TSLA_Item 1A._13", "TSLA_Item 1A._23"],
        "category": "conceptual"
    },
    {
        "question": "What are Tesla's main risks related to autonomous driving technology?",
        "relevant_chunk_ids": ["TSLA_Item 1A._1", "TSLA_Item 1A._26"],
        "category": "conceptual"
    },
    {
        "question": "Who are Tesla's main competitors, as described in the filing?",
        "relevant_chunk_ids": ["TSLA_Item 1._31", "TSLA_Item 1._32"],
        "category": "single_company_narrow"
    },
    {
        "question": "How do Tesla and Apple describe supply chain risks?",
        "relevant_chunk_ids": ["TSLA_Item 1A._12", "TSLA_Item 1A._13", "AAPL_Item 1A._16", "AAPL_Item 1A._17"],
        "category": "cross_company"
    },
    {
        "question": "Compare how Apple and Microsoft discuss competition in their respective markets.",
        "relevant_chunk_ids": ["AAPL_Item 1A._9", "AAPL_Item 1A._12", "MSFT_Item 1A._5", "MSFT_Item 1._10"],
        "category": "cross_company"
    },
    {
        "question": "What did the company report about its involvement in commercial airline manufacturing?",
        "relevant_chunk_ids": [],
        "category": "out_of_scope"
    },
    {
        "question": "What are the company's plans for opening physical bank branches?",
        "relevant_chunk_ids": [],
        "category": "out_of_scope"
    },
]

