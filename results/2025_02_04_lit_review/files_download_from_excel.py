#!/usr/bin/env python3
"""
A script to manage PDF downloads from direct URLs or Sci-Hub. 
It reads CSV files listing PDFs to download, tries to fetch them, 
and updates the CSV with the download status and final URL.

Author: [Your Name]
Date: [Optional: YYYY-MM-DD]
"""

import os
import time
import random
import requests
import pandas as pd
from bs4 import BeautifulSoup
from ipdb import set_trace


def download_pdf(pdf_url: str, pdf_name: str) -> int:
    """
    Download a PDF directly from a given URL, saving it with pdf_name.

    Args:
        pdf_url (str): Direct URL to the PDF resource.
        pdf_name (str): Filename to use for saving the PDF (without '.pdf').

    Returns:
        int: 1 if successful, -1 otherwise.
    """
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
    ]
    headers = {
        "User-Agent": random.choice(user_agents)
    }

    # Sleep randomly between 2 and 5 seconds to avoid server suspicion
    time.sleep(random.uniform(2, 5))

    response = requests.get(pdf_url, headers=headers, stream=True)
    if response.status_code == 200:
        output_dir = "./proc/paper_pdfs"
        pdf_path = os.path.join(output_dir, f"{pdf_name}.pdf")
        with open(pdf_path, "wb") as file_obj:
            for chunk in response.iter_content(chunk_size=1024):
                file_obj.write(chunk)

        print("Download successful.")
        response.close()
        return 1
    else:
        print(f"Failed to download. Status code: {response.status_code}")
        response.close()
        return -1


def download_pdf_scihub(page_url: str, pdf_name: str) -> tuple:
    """
    Attempt to download a PDF from Sci-Hub by first scraping the Sci-Hub page,
    finding the <embed type="application/pdf">, and then saving the PDF.

    Args:
        page_url (str): The Sci-Hub URL which should contain an embedded PDF.
        pdf_name (str): Filename to save the PDF as (excluding '.pdf').

    Returns:
        (int, str):
            - int: 1 if successful, -1 otherwise
            - str: The final PDF URL or -1 if none found
    """
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

            # Ensure pdf_url is fully qualified (has http/https)
            if "http" not in pdf_url:
                pdf_url = "http://" + pdf_url.split("//")[-1]

            pdf_response = requests.get(pdf_url, headers=headers, stream=True)
            if pdf_response.status_code == 200:
                output_dir = "./proc/paper_pdfs"
                pdf_path = os.path.join(output_dir, f"{pdf_name}.pdf")
                with open(pdf_path, "wb") as file_obj:
                    for chunk in pdf_response.iter_content(chunk_size=1024):
                        file_obj.write(chunk)

                print(f"PDF downloaded successfully: {pdf_name}.pdf")
                return 1, pdf_url
            else:
                print(f"PDF download failed, status code: {pdf_response.status_code}")
                return -1, pdf_url
        else:
            print("No PDF resource (<embed>) found on the page.")
            return -1, -1
    else:
        print(f"Page access failed, status code: {response.status_code}")
        return -1, -1


def main():
    """
    Main workflow:
    1. For each CSV in a given directory, load it into a DataFrame.
    2. Filter rows with download_status == -1, indicating the PDF wasn't previously downloaded.
    3. Try to download:
       - If pdf_url != '-1', attempt direct download (download_pdf).
       - Otherwise, parse Sci-Hub URL using the stored DOI and call download_pdf_scihub.
    4. Update the CSV with the download status and final URL.
    """
    path = "./proc/term_csv"
    excels = os.listdir(path)

    for excel_file in excels:
        print(f"Processing: {excel_file}")
        # Skip certain files if needed
        if excel_file == "01000.csv":
            continue

        csv_path = os.path.join(path, excel_file)
        data = pd.read_csv(csv_path)
        data_copy = data.copy()

        # Filter entries where download_status == -1
        entries_to_download = data[data["download_status"] == -1]

        for i in range(len(entries_to_download)):
            pdf_name = str(entries_to_download.iloc[i][0]).zfill(5)
            pdf_url_candidate = entries_to_download.iloc[i][1]

            if pdf_url_candidate == "-1":
                # Means we do not have a direct PDF link, so we must use Sci-Hub
                doi_val = entries_to_download.iloc[i][8]
                scihub_base_url = "https://sci-hub.st/"
                page_url = scihub_base_url + doi_val.lower()

                download_status, final_pdf_url = download_pdf_scihub(page_url, pdf_name)
            else:
                # We have a direct PDF link
                download_status = download_pdf(pdf_url_candidate, pdf_name)
                final_pdf_url = pdf_url_candidate

            # # Update the DataFrame
            # row_index = (int(entries_to_download.iloc[i][0]) % 1000) - 1
            # data_copy.iloc[row_index, -1] = download_status  # update download_status column
            # data_copy.iloc[row_index, 1] = final_pdf_url     # update pdf_url column

        # Save the updated DataFrame
        # data_copy.to_csv(csv_path, index=False)


if __name__ == '__main__':
    main()
