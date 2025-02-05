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

def get_urlInItems(base_url, name, paper_nums):
    # 请求头
    head = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
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
    num = 0
    flag = 0
    # 解析当前页面的HTML
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    # set_trace()
    # 找到 <a> 标签并点击
    study_button_element = driver.find_element(By.CSS_SELECTOR, "a[data-toggle='tab'][href='#studies']")
    study_button_element.click()

    # div_tag = soup.find('div', {'id': 'analysis-studies-table_info'})
    # all_num = div_tag.get_text(strip=True).split(" ")[-2]
    # 查找表格数据（根据页面的HTML结构调整）

    while num < paper_nums:
        soup = BeautifulSoup(driver.page_source, 'html.parser')  # 更新 soup
        table = soup.find('table', {'id': 'analysis-studies-table'})
        if table:
            rows = table.find_all('tr')
            for row in rows[1:]:  # 跳过表头
                cols = row.find_all('td')
                if len(cols) > 0:
                    print(num)
                    if num == paper_nums:
                        break
                    title = cols[0].get_text(strip=True)
                    author = cols[1].get_text(strip=True)
                    journal = cols[2].get_text(strip=True)
                    loading = cols[3].get_text(strip=True)
                    pmid = cols[0].find('a')['href'].split("/")[-2]
                    num += 1
                    paper_url = "https://pubmed.ncbi.nlm.nih.gov/" + pmid + "/"
                    print(title)
                    # doi, download_status = DOI(paper_url, num)
                    try:
                        doi, download_status = DOI(paper_url, name+"_"+str(num).zfill(5))
                    except:
                        doi, download_status = -1, -1
                    all_study_data.append({
                        "paper_name": name+"_"+str(num).zfill(5),
                        'paper_url': paper_url,
                        'Title': title,
                        'Author': author,
                        'Journal': journal,
                        'Loading': loading,
                        'PMID': pmid,
                        "Doi": doi,
                        "download_status": download_status
                    })
                    # set_trace()
                    # if len(all_study_data) % 200 == 0:
                    #     # 转换为 DataFrame
                    #     df = pd.DataFrame(all_study_data)
                    #     # 保存到 CSV
                    #     df.to_csv("D:/study/Python_code/BrainVLM/papers/Excels/"+name+".csv", index=False)

        # set_trace()
        # 查找是否有“下一页”按钮
        try:
            # print(all_study_data)
            # 假设下一页按钮的class为'next'，根据实际情况调整
            next_button = driver.find_element(By.CLASS_NAME, 'next')
            if next_button:
                next_button.click()
                time.sleep(3)  # 等待页面加载
            else:
                break  # 如果没有“下一页”按钮，停止翻页
        except:
            next_button = driver.find_element(By.CLASS_NAME, 'next')
            if next_button:
                next_button.click()
                time.sleep(3)  # 等待页面加载
            else:
                break  # 如果没有“下一页”按钮，停止翻页

    # 打印抓取到的数据
    for study in all_study_data:
        print("**"*20)
        print(study)
    df = pd.DataFrame(all_study_data)
    # 保存到 CSV
    df.to_csv("D:/study/Python_code/BrainVLM/papers/Excels/" + name + ".csv", index=False)
    # 关闭浏览器
    driver.quit()



def main():
    data = pd.read_csv("D:\study\Python_code\BrainVLM\papers\Items.csv")
    for i in range(100,200):
        try:
            name = data.iloc[i][0]
            paper_nums = data.iloc[i][1]
            print(name)
            # 爬取文章
            url = "https://neurosynth.org/analyses/terms/{}/".format(name)
            get_urlInItems(url, name=name, paper_nums = paper_nums)
        except:
            continue

if __name__ == '__main__':
    main()








