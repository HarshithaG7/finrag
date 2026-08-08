import requests
from bs4 import BeautifulSoup

URL="https://www.sec.gov/files/company_tickers.json"
HEADERS={
    "User-Agent": "Harshitha/harshithaganeshkumar06@gmail.com"
    }
def get_cik(ticker):
    response=requests.get(URL, headers=HEADERS)
    data=response.json()
    for entry in data.values():
        if entry["ticker"].lower()==ticker.lower():
            return entry["cik_str"]
        pass
def get_recent_10k_filings(cik, count=3):
    cik_padded = str(cik).zfill(10)
    url = f"https://data.sec.gov/submissions/CIK{cik_padded}.json"
    response = requests.get(url, headers=HEADERS)
    data = response.json()
    
    recent = data["filings"]["recent"]
    results = []
    
    for index, form in enumerate(recent["form"]):
        if form == "10-K":
            results.append({
                "filingDate": recent["filingDate"][index],
                "accessionNumber": recent["accessionNumber"][index],
                "primaryDocument": recent["primaryDocument"][index],
            })
        if len(results) >= count:
            break
    return results
def download_filing(cik,accession_number,primary_document):
    url=f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_number.replace('-','')}/{primary_document}"
    response=requests.get(url,headers=HEADERS)
    if response.status_code==200:
        filename=f"{accession_number}_{primary_document}"
        with open(filename,"wb") as f:
            f.write(response.content)
        print(f"Downloaded filing: {filename}")
    else:
        print(f"Failed to download filing: {response.status_code}")
def extract_text_from_filing(filename):
    with open(filename,"r",encoding="utf-8") as f:
        content=f.read()
    content=BeautifulSoup(content,"html.parser")
    content=content.get_text(separator=" ",strip=True)
    return content


if __name__ == "__main__":
    ticker="MSFT"
    cik = get_cik(ticker)
    filings = get_recent_10k_filings(cik)
    print(filings)
    first_filing = filings[0]
    download_filing(cik, first_filing["accessionNumber"], first_filing["primaryDocument"])
    extracted_text=extract_text_from_filing(f"{first_filing['accessionNumber']}_{first_filing['primaryDocument']}")
    with open(f"{ticker}_extracted_text.txt","w",encoding="utf-8") as f:
        f.write(extracted_text)
    print("Extracted text saved to extracted_text.txt")