#!/usr/bin/env python3
"""
Scrapes study metadata from neurosynth.org term analysis pages, 
including PubMed PMIDs, and optionally fetches DOIs. 

Output is saved to a CSV for each term listed in a local CSV file (Items.csv).
"""

import os
import time
import urllib.parse
import requests
import pandas as pd

from bs4 import BeautifulSoup
from ipdb import set_trace

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


# NOTE: This function "DOI(...)" is referenced but not defined in the snippet.
# You must provide or import it from elsewhere in your codebase.
# Example placeholder:
def DOI(paper_url, pdf_prefix):
    """
    Placeholder for a function that returns:
       - doi (str or int)
       - download_status (int)
    based on a PubMed URL (paper_url).

    Args:
        paper_url (str): A string URL to a PubMed page
        pdf_prefix (str): Some prefix or unique identifier for the PDF file

    Returns:
        (doi, download_status):
            doi (str or int): Identified DOI or -1 if not found
            download_status (int): 1 if downloaded successfully, -1 otherwise
    """
    return -1, -1  # TODO: Replace with actual logic.


def fetch_study_items(base_url, term_name, paper_count):
    """
    Scrape the 'studies' table from a neurosynth.org analysis page (or similar),
    capturing up to 'paper_count' studies. The script navigates through 
    pagination until it either reaches the required number of papers or 
    runs out of pages.

    Args:
        base_url (str): 
            The URL of the neurosynth page that includes a "studies" tab, e.g., 
            "https://neurosynth.org/analyses/terms/<term>/".
        term_name (str): 
            The name or ID used to label the CSV output (e.g., 'pain' or 'memory').
        paper_count (int): 
            The number of studies/papers to capture from the table.

    Returns:
        None. A CSV file is written to "D:/study/Python_code/BrainVLM/papers/Excels/<term_name>.csv".
    """
    # Configure Selenium to run in headless mode (no visible browser)
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    # Open a placeholder page, then navigate to the target
    driver.get("https://www.example.com")
    driver.get(base_url)
    time.sleep(3)  # allow time for page to load

    all_study_data = []
    scraped_count = 0

    # Access the 'Studies' tab via its CSS selector
    # (adjust the find_element logic if the actual structure changes)
    study_button = driver.find_element(By.CSS_SELECTOR, "a[data-toggle='tab'][href='#studies']")
    study_button.click()

    while scraped_count < paper_count:
        # Parse current page with BeautifulSoup
        soup = BeautifulSoup(driver.page_source, "html.parser")
        studies_table = soup.find("table", {"id": "analysis-studies-table"})

        if studies_table:
            rows = studies_table.find_all("tr")
            # Skip the header row
            for row in rows[1:]:
                cols = row.find_all("td")
                if len(cols) > 0:
                    if scraped_count == paper_count:
                        break

                    title = cols[0].get_text(strip=True)
                    author = cols[1].get_text(strip=True)
                    journal = cols[2].get_text(strip=True)
                    loading_info = cols[3].get_text(strip=True)

                    # Extract PMID from the 'href'
                    pmid_link = cols[0].find("a")["href"]
                    pmid = pmid_link.split("/")[-2]  # e.g., .../12345678/

                    scraped_count += 1
                    paper_url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
                    print(f"{scraped_count}. Title: {title}")

                    # Attempt to retrieve the DOI (and possibly download the PDF)
                    try:
                        doi_val, download_status_val = DOI(paper_url, f"{term_name}_{str(scraped_count).zfill(5)}")
                    except Exception as e:
                        print("Error calling DOI function:", e)
                        doi_val, download_status_val = -1, -1

                    all_study_data.append({
                        "paper_name": f"{term_name}_{str(scraped_count).zfill(5)}",
                        "paper_url": paper_url,
                        "Title": title,
                        "Author": author,
                        "Journal": journal,
                        "Loading": loading_info,
                        "PMID": pmid,
                        "Doi": doi_val,
                        "download_status": download_status_val
                    })

        # Attempt to click "Next" page
        try:
            next_button = driver.find_element(By.CLASS_NAME, "next")
            if next_button:
                next_button.click()
                time.sleep(3)  # wait for page load
            else:
                break
        except:
            # If there's no next button or it fails, break out
            break

        if scraped_count >= paper_count:
            break

    # Print scraped results (debugging)
    for study_item in all_study_data:
        print("*" * 40)
        print(study_item)

    # Write to a local CSV file
    csv_filename = f"./proc/term_csv/{term_name}.csv"
    df = pd.DataFrame(all_study_data)
    df.to_csv(csv_filename, index=False)

    driver.quit()


def main():
    """
    Main loop that:
    1) Reads a local CSV file 'Items.csv' with rows like [term_name, paper_count].
    2) For each row in the CSV, constructs a neurosynth URL and calls 'fetch_study_items' to scrape data.
    """
    items_csv = "./items.csv"
    data = pd.read_csv(items_csv)

    # Iterate through the rows of the CSV
    for index, row in data.iterrows():
        try:
            term_name = row[0]  # Assuming 'term_name' is in the first column
            paper_nums = int(row[1])  # Assuming 'paper_count' is in the second column
            print(f"Scraping term: {term_name}")

            # Build the neurosynth term analysis URL
            url = f"https://neurosynth.org/analyses/terms/{term_name}/"

            # Make sure the argument names match the signature of fetch_study_items()
            fetch_study_items(base_url=url, term_name=term_name, paper_count=paper_nums)

        except Exception as e:
            print(f"Error on row {index} with term {term_name}: {e}")
            continue


if __name__ == "__main__":
    main()
