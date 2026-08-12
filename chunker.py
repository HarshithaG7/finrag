import re

def find_section_boundaries(text):
    section_boundaries = []
    section_titles = ["Item 1.","Item 1A.","Item 1B.","Item 2.","Item 3.","Item 4.","Item 5.","Item 6.","Item 7.","Item 7A.","Item 8.","Item 9.","Item 9A.","Item 10.","Item 11.","Item 12.","Item 13.","Item 14."]
    
    for title in section_titles:
        # escape the period so it's treated literally, not as regex wildcard
        pattern = re.escape(title)
        matches = list(re.finditer(pattern, text, re.IGNORECASE))
        if matches:
            start_index = matches[-1].start()  # last match, same intent as rfind
            section_boundaries.append((title, start_index))
    
    section_boundaries.sort(key=lambda x: x[1])
    section_boundaries_with_end = []
    for i in range(len(section_boundaries)):
        start_title, start_index = section_boundaries[i]
        end_index = section_boundaries[i+1][1] if i < len(section_boundaries)-1 else len(text)
        section_boundaries_with_end.append((start_title, start_index, end_index))
    return section_boundaries_with_end


def chunk_section_text(text,max_chars=1200,overlap_chars=200):
    """
    Chunk the text into smaller sections of max_chars length, with overlap of overlap_chars.
    Returns a list of tuples (chunk_text, start_index, end_index).
    """
    text=" ".join(text.split())
    max_words=max_chars//6
    overlap_words=overlap_chars//6
    words=text.split()
    chunks=[]
    start=0
    while start<len(words):
        end=min(start+max_words,len(words))
        chunk_words=words[start:end]
        chunk_text=" ".join(chunk_words)
        start_index=text.find(chunk_text)
        end_index=start_index+len(chunk_text)
        chunks.append((chunk_text,start_index,end_index))
        start+=max_words-overlap_words
    return chunks

def chunk_filing(text,company):
    """
    Chunk the filing text into sections based on the company and section boundaries.
    Returns a dictionary with section titles as keys and lists of chunks as values.
    """
    boundaries=find_section_boundaries(text)
    all_chunks=[]
    for title,start,end in boundaries:
        section_text=text[start:end]
        chunks=chunk_section_text(section_text)
        for index,chunk in enumerate(chunks):
            chunk_text,chunk_start,chunk_end=chunk
            all_chunks.append({"company":company,"section":title,"text":chunk_text,"chunk_id":f"{company}_{title}_{index}"})
    return all_chunks

if __name__ == "__main__":
    all_data = {}
    for ticker in ["AAPL", "TSLA", "MSFT"]:
        with open(f"{ticker}_extracted_text.txt", "r", encoding="utf-8") as f:
            text = f.read()
        all_data[ticker] = chunk_filing(text, ticker)
        print(f"{ticker}: {len(all_data[ticker])} chunks")