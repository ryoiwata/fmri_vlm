#!/usr/bin/env python3
"""
A script to:
1) Scrape study information from a paginated table at neurosynth.org (or another site).
2) Extract the PMID for each study.
3) Build a PubMed URL for each PMID, parse the resulting page for a DOI, 
4) Attempt to download the PDF via Sci-Hub.

The results are saved in a CSV file, while PDFs are stored locally if found.
"""

import requests
import time
import pandas as pd
from bs4 import BeautifulSoup
from ipdb import set_trace

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


def get_pdf_from_doi(doi, pdf_name):
    """
    Attempt to download a paper's PDF from Sci-Hub using the given DOI.
    
    Args:
        doi (str): The paper's DOI.
        pdf_name (str): Filename prefix used for saving the PDF.
        
    Returns:
        (status_code, pdf_url): 
            status_code = 1 if PDF successfully downloaded, -1 otherwise
            pdf_url = The direct PDF link or -1 if none found.
    """
    sci_hub_url = "https://sci-hub.ren/"
    page_url = sci_hub_url + doi
    print(f"Visiting Sci-Hub page: {page_url}")

    headers = {
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/120.0.0.0 Safari/537.36")
    }
    response = requests.get(page_url, headers=headers)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        embed_tag = soup.find("embed", {"type": "application/pdf"})
        if embed_tag:
            pdf_url = embed_tag["src"].split("#")[0]  # remove any anchor
            print(f"Found PDF URL: {pdf_url}")

            pdf_response = requests.get(pdf_url, headers=headers, stream=True)
            if pdf_response.status_code == 200:
                output_dir = "D:\\study\\Python_code\\BrainVLM\\PDFs\\"
                pdf_path = f"{output_dir}{pdf_name}.pdf"

                with open(pdf_path, "wb") as file_obj:
                    for chunk in pdf_response.iter_content(chunk_size=1024):
                        file_obj.write(chunk)

                print(f"PDF downloaded successfully: {pdf_name}.pdf")
                return 1, pdf_url
            else:
                print(f"PDF download failed, status code: {pdf_response.status_code}")
                return -1, pdf_url
        else:
            print("No <embed> PDF resource found on the page.")
            return -1, -1
    else:
        print(f"Failed to access Sci-Hub, status code: {response.status_code}")
        return -1, -1


def extract_doi_from_pubmed(paper_url, pdf_name):
    """
    Given a PubMed page URL, parse for the DOI, then attempt to download the PDF via Sci-Hub.

    Args:
        paper_url (str): The full PubMed URL (e.g., "https://pubmed.ncbi.nlm.nih.gov/<PMID>/").
        pdf_name (str): Filename prefix for saving the downloaded PDF.

    Returns:
        (doi, download_status, pdf_url):
            doi (str or int): Extracted DOI, or -1 if not found
            download_status (int): 1 if PDF downloaded, -1 otherwise
            pdf_url (str or int): Direct PDF link or -1 if not available
    """
    response = requests.get(paper_url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')

        # Attempt to find the DOI in a <span class="identifier doi"><a> structure
        doi_span = soup.find('span', class_='identifier doi')
        if doi_span:
            doi_anchor = doi_span.find('a')
            if doi_anchor:
                doi_text = doi_anchor.text.strip()
                print("Found DOI:", doi_text)
                download_status, pdf_url = get_pdf_from_doi(doi_text, pdf_name)
                return doi_text, download_status, pdf_url

        print("No DOI element found in PubMed page.")
        return -1, -1, -1
    else:
        print(f"Failed to access PubMed page, status code: {response.status_code}")
        return -1, -1, -1


def pdf_download(base_url, start_page, end_page):
    """
    Scrape study data from a table at 'base_url' across multiple pages, 
    then parse each study's PMID to get its PubMed page. Next, attempt 
    to extract and download the PDF via Sci-Hub.

    Args:
        base_url (str): The initial URL containing the table of studies (e.g., neurosynth.org/studies/).
        start_page (int): The first page index to begin scraping.
        end_page (int): The maximum page index to scrape up to.
    """
    # Set Selenium to run in headless mode
    chrome_options = Options()
    chrome_options.add_argument("--headless")

    # Initialize Chrome driver
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    # Navigate to the base URL
    driver.get(base_url)
    time.sleep(3)  # wait for page load

    all_study_data = []
    current_page = 0

    while current_page < end_page:
        # Step 1: skip to the start_page if needed
        while current_page < (start_page - 1):
            try:
                current_page += 1
                next_button = driver.find_element(By.CLASS_NAME, 'next')
                if next_button:
                    next_button.click()
                    time.sleep(3)  # wait for next page
                else:
                    break
            except:
                # Attempt again or break
                current_page += 1
                try:
                    next_button = driver.find_element(By.CLASS_NAME, 'next')
                    if next_button:
                        next_button.click()
                        time.sleep(3)
                    else:
                        break
                except:
                    break

        # Step 2: parse the current page
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        studies_table = soup.find('table', {'id': 'studies_table'})
        if studies_table:
            rows = studies_table.find_all('tr')
            row_index = 0

            for row in rows[1:]:  # skip header
                row_index += 1
                cells = row.find_all('td')
                if len(cells) > 0:
                    title = cells[0].get_text(strip=True)
                    author = cells[1].get_text(strip=True)
                    journal = cells[2].get_text(strip=True)
                    year = cells[3].get_text(strip=True)
                    pmid = cells[4].get_text(strip=True)

                    paper_url = "https://pubmed.ncbi.nlm.nih.gov/" + pmid + "/"
                    pdf_name = str(current_page * 10 + row_index).zfill(5)

                    doi_val, status_val, pdf_url_val = extract_doi_from_pubmed(paper_url, pdf_name)
                    all_study_data.append({
                        "pdf_name": pdf_name,
                        "pdf_url": pdf_url_val,
                        "paper_url": paper_url,
                        "Title": title,
                        "Author": author,
                        "Journal": journal,
                        "Year": year,
                        "PMID": pmid,
                        "Doi": doi_val,
                        "download_status": status_val
                    })

        # Step 3: move to the next page
        try:
            current_page += 1
            next_button = driver.find_element(By.CLASS_NAME, 'next')
            if next_button:
                next_button.click()
                time.sleep(3)
            else:
                break
        except:
            current_page += 1
            try:
                next_button = driver.find_element(By.CLASS_NAME, 'next')
                if next_button:
                    next_button.click()
                    time.sleep(3)
                else:
                    break
            except:
                break

        # Save partial progress to CSV
        df = pd.DataFrame(all_study_data)
        csv_filename = f"D:\\study\\Python_code\\BrainVLM\\PDFs\\excels\\{str(end_page*10).zfill(5)}.csv"
        df.to_csv(csv_filename, index=False)

    driver.quit()


def main():
    """
    Main entry point. 
    Example usage: scrape studies from neurosynth.org/studies/, 
    from page 1 through page 100.
    """
    base_url = "https://neurosynth.org/studies/"
    pdf_download(base_url, start_page=1, end_page=100)


if __name__ == "__main__":
    main()
