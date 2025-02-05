#!/usr/bin/env python3
"""
Script to download a PDF from Sci-Hub given a DOI. 
First tries https://sci-hub.ren, and if that fails, tries https://sci-hub.se.

Author: [Your Name]
Date: [Optional: YYYY-MM-DD]
"""

import requests
from bs4 import BeautifulSoup
import os

def download_paper_pdf(doi, output_dir="."):
    """
    Attempt to retrieve a paper's PDF from Sci-Hub using the provided DOI.
    
    1) Build a Sci-Hub URL by appending the DOI.
    2) Parse the resulting page for an <embed> tag that has a PDF 'src'.
    3) Download the PDF in chunks and save it locally.

    Args:
        doi (str): The paper's DOI, e.g., "10.1002/hbm.22811".
        output_dir (str): Local path where the PDF will be saved.

    Returns:
        None
    """
    sci_hub_url = "https://sci-hub.ren/"
    page_url = sci_hub_url + doi
    print("Attempting URL:", page_url)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) \
AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    response = requests.get(page_url, headers=headers)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        embed_tag = soup.find("embed", {"type": "application/pdf"})
        if embed_tag:
            pdf_url = embed_tag["src"].split("#")[0]
            print(f"Found PDF URL: {pdf_url}")

            pdf_response = requests.get(pdf_url, headers=headers, stream=True)
            if pdf_response.status_code == 200:
                if not os.path.exists(output_dir):
                    os.makedirs(output_dir)

                # Extract a filename from the DOI (anything after the last dot).
                pdf_filename = doi.split('.')[-1] + ".pdf"
                save_path = os.path.join(output_dir, pdf_filename)

                with open(save_path, "wb") as file:
                    for chunk in pdf_response.iter_content(chunk_size=1024):
                        if chunk:
                            file.write(chunk)
                print(f"PDF downloaded successfully: {pdf_filename}")
            else:
                print(f"Failed to download PDF, status code: {pdf_response.status_code}")
        else:
            print("Could not find any PDF resource on the page.")
    else:
        print(f"Page access failed, status code: {response.status_code}")


if __name__ == "__main__":
    """
    Example usage:
    1) We set a single DOI.
    2) Attempt to download from sci-hub.ren
    3) If it fails, try from sci-hub.se
    """
    doi = "10.1002/hbm.22811"
    print("DOI:", doi)

    # First Attempt
    try:
        download_paper_pdf(doi)
    except Exception as e:
        print("First attempt (sci-hub.ren) failed:", e)

        # Second Attempt
        print("Attempting alternate domain: sci-hub.se")
        try:
            # Temporarily modify the function to use the other domain
            # or replicate the logic internally:
            backup_url = "https://sci-hub.se/" + doi
            download_paper_pdf(backup_url)
        except Exception as e2:
            print("Second attempt (sci-hub.se) also failed:", e2)
