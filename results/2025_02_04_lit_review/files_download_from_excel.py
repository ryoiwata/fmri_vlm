import requests
import pandas as pd
import os
from ipdb import set_trace
import time
import random
from bs4 import BeautifulSoup

def download_pdf(pdf_url, pdf_name):
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
    ]

    headers = {
        "User-Agent": random.choice(user_agents)
    }
    time.sleep(random.uniform(2,5))
    response = requests.get(pdf_url, headers=headers, stream=True)

    if response.status_code == 200:
        output = "D:\\study\\Python_code\\BrainVLM\\PDFs\\"
        with open(output + pdf_name + ".pdf", "wb") as file:
            for chunk in response.iter_content(chunk_size=1024):
                file.write(chunk)
        print("Download successful.")
        response.close()
        return 1
    else:
        print(f"Failed to download. Status code: {response.status_code}")
        response.close()
        return -1


def download_pdf_scihub(page_url, pdf_name):
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
        # set_trace()
        if embed_tag:
            pdf_url = embed_tag["src"].split("#")[0]  # 去除锚点
            print(f"找到 PDF URL: {pdf_url}")
            if "http" not in pdf_url:
                pdf_url = "http://"+pdf_url.split("//")[-1]
            # # 下载 PDF
            pdf_response = requests.get(pdf_url, headers=headers, stream=True)
            if pdf_response.status_code == 200:
                output = "D:\\study\\Python_code\\BrainVLM\\PDFs\\"
                with open(output + pdf_name + ".pdf", "wb") as file:
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

def main():
    path = "D:\\study\\Python_code\\BrainVLM\\PDFs\\excels"
    excels = os.listdir(path)
    for excel in excels:
        print(excel)
        if excel in ["01000.csv"] :
            continue
        data = pd.read_csv(path+"\\"+excel)
        data_download = data[data["download_status"]==-1]
        data1 = data.copy()
        for i in range(0, len(data_download)):
            # download_pdf()
            pdf_name = str(data_download.iloc[i][0]).zfill(5)
            pdf_url = data_download.iloc[i][1]
            if pdf_url == "-1":
                doi = data_download.iloc[i][8]
                # pdf_url = f"https://journals.plos.org/plosone/article/file?id={doi}&type=printable"
                sci_Hub_Url = "https://sci-hub.st/"
                page_url = sci_Hub_Url + doi.lower()
                # set_trace()
                download_status, pdf_url = download_pdf_scihub(page_url, pdf_name)
                # set_trace()
                # continue
            else:
                download_status = download_pdf(pdf_url, pdf_name)

            data1.iloc[int(data_download.iloc[i][0]) % 1000 - 1,-1] = download_status
            data1.iloc[int(data_download.iloc[i][0]) % 1000 - 1, 1] = pdf_url
            # set_trace()
        # data.iloc[int(data_download.iloc[i][0])%1000-1][-1] = download_status
        # set_trace()
        # 转换为 DataFrame

        # 保存到 CSV
        data1.to_csv(path+"\\"+excel, index=False)



if __name__ == '__main__':
    main()