from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import json

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd

from ipdb import set_trace
import time

from bs4 import BeautifulSoup
import urllib.parse
import requests



def DOI(url, pdf_name):
    # 发送GET请求获取网页内容
    response = requests.get(url)

    # 如果请求成功，继续处理
    if response.status_code == 200:
        # 解析网页内容
        soup = BeautifulSoup(response.text, 'html.parser')
        # link = soup.find('a', class_='id-link')
        # if link:
            # ref_attr = link.get("ref", "")
            #
            # # 解析 URL 参数
            # parsed_params = urllib.parse.parse_qs(ref_attr)
            # # 获取 article_id
            # doi = parsed_params.get("article_id", [""])[0]

        doi_element = soup.find('span', class_='identifier doi').find('a')
        doi = doi_element.text.strip() if doi_element else -1
        print("doi:", doi)
            # getPaperPdf(doi, pdf_name)
    download_status, pdf_url = getPaperPdf(doi, pdf_name)

    return doi, download_status, pdf_url
    # try:
    #     return doi, getPaperPdf(doi, pdf_name)
    # except:
    #     set_trace()

def getPaperPdf(doi, pdf_name):
    sci_Hub_Url = "https://sci-hub.ren/"
    page_url = sci_Hub_Url + doi
    print(page_url)

    # 发送请求获取网页内容
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        # "Referer": "https://sci.bban.top/"
    }
    response = requests.get(page_url, headers=headers)

    if response.status_code == 200:
        # 解析 HTML
        soup = BeautifulSoup(response.text, "html.parser")
        # 查找 <embed> 标签
        embed_tag = soup.find("embed", {"type": "application/pdf"})
        if embed_tag:
            pdf_url = embed_tag["src"].split("#")[0]  # 去除锚点
            print(f"找到 PDF URL: {pdf_url}")

            # # 下载 PDF
            pdf_response = requests.get(pdf_url, headers=headers, stream=True)
            if pdf_response.status_code == 200:
                output = "D:\\study\\Python_code\\BrainVLM\\PDFs\\"
                with open(output + pdf_name+".pdf", "wb") as file:
                    for chunk in pdf_response.iter_content(chunk_size=1024):
                        file.write(chunk)
                print("PDF 下载成功: {}.pdf".format(pdf_name))
                return 1, pdf_url
            else:
                print(f"PDF 下载失败，状态码: {pdf_response.status_code}")
                return -1, pdf_url
        else:
            print("未找到 PDF 资源")
            return -1, -1

    else:
        print(f"网页访问失败，状态码: {response.status_code}")
        return -1, -1




def PDF_download(base_url, start, end):
    # 请求头
    head = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.117 Safari/537.36"
    }
    # 设置Selenium的浏览器配置（使用Chrome）
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # 无头模式
    # 获取 chromedriver 路径
    service = Service(ChromeDriverManager().install())
    # 启动 Chrome 浏览器
    driver = webdriver.Chrome(service=service)
    # 你可以继续使用 driver 进行网页操作
    driver.get('https://www.example.com')

    # 打开网页
    driver.get(base_url)
    # 设置等待时间，确保页面加载完毕
    time.sleep(3)

    # 存储所有抓取的数据
    all_study_data = []
    # 假设表格有分页，循环爬取多页
    page = 0
    while page < end:
        # 解析当前页面的HTML
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        # 查找表格数据（根据页面的HTML结构调整）
        table = soup.find('table', {'id': 'studies_table'})
        while page < start-1:
            # 查找是否有“下一页”按钮
            try:
                # 假设下一页按钮的class为'next'，根据实际情况调整
                page += 1
                next_button = driver.find_element(By.CLASS_NAME, 'next')
                if next_button:
                    next_button.click()
                    time.sleep(3)  # 等待页面加载
                else:
                    break  # 如果没有“下一页”按钮，停止翻页
            except:
                page += 1
                next_button = driver.find_element(By.CLASS_NAME, 'next')
                if next_button:
                    next_button.click()
                    time.sleep(3)  # 等待页面加载
                else:
                    break  # 如果没有“下一页”按钮，停止翻页

        # 解析当前页面的HTML
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        # 查找表格数据（根据页面的HTML结构调整）
        table = soup.find('table', {'id': 'studies_table'})

        if table:
            rows = table.find_all('tr')
            num_item = 0
            for row in rows[1:]:  # 跳过表头
                num_item += 1
                cols = row.find_all('td')
                if len(cols) > 0:
                    title = cols[0].get_text(strip=True)
                    author = cols[1].get_text(strip=True)
                    journal = cols[2].get_text(strip=True)
                    year = cols[3].get_text(strip=True)
                    pmid = cols[4].get_text(strip=True)
                    paper_url = "https://pubmed.ncbi.nlm.nih.gov/" + pmid + "/"
                    # print(title)
                    pdf_name = str(page*10+num_item).zfill(5)
                    doi, download_status, pdf_url = DOI(paper_url, pdf_name)
                    # if download_status == -1:
                    #     set_trace()
                    # try:
                    #     doi, download_status = DOI(paper_url, pdf_name)
                    # except:
                    #     doi, download_status = -1, -1
                    all_study_data.append({
                        "pdf_name": pdf_name,
                        "pdf_url": pdf_url,
                        'paper_url': paper_url,
                        'Title': title,
                        'Author': author,
                        'Journal': journal,
                        'Year': year,
                        'PMID': pmid,
                        "Doi": doi,
                        "download_status": download_status
                    })

        # 查找是否有“下一页”按钮
        try:
            # 假设下一页按钮的class为'next'，根据实际情况调整
            page += 1
            next_button = driver.find_element(By.CLASS_NAME, 'next')
            if next_button:
                next_button.click()
                time.sleep(3)  # 等待页面加载
            else:
                break  # 如果没有“下一页”按钮，停止翻页
        except:
            page += 1
            next_button = driver.find_element(By.CLASS_NAME, 'next')
            if next_button:
                next_button.click()
                time.sleep(3)  # 等待页面加载
            else:
                break  # 如果没有“下一页”按钮，停止翻页


        # 转换为 DataFrame
        df = pd.DataFrame(all_study_data)
        # 保存到 CSV
        df.to_csv("D:\\study\\Python_code\\BrainVLM\\PDFs\\excels\\" + str(end*10).zfill(5)+".csv", index=False)

    # 关闭浏览器
    driver.quit()

def main():

    base_url = "https://neurosynth.org/studies/"
    PDF_download(base_url,1,100)


if __name__ == '__main__':
    main()








