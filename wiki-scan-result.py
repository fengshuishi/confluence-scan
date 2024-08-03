import requests
import re
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

# 配置
confluence_base_url = "http://confluence.xxxxxxxxx.com"  # Confluence 基础 URL
cookie = {"JSESSIONID": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"}  # 替换为您的实际 Cookie
search_keywords = ['密码', '账号:', 'root']  # 首先检查的关键字
keywords = ['admin', '123456', 'bw', 'abc', 'aaa', 'bbb','root','username=','password','accessKeySecret', '账号密码:', '用户名密码:', '账号/密码', '用户名/密码', '用户/密码']

def fetch_page_content(page_id, retries=3):
    session = requests.Session()
    session.cookies.update(cookie)
    url = f"{confluence_base_url}/pages/viewpage.action?pageId={page_id}"

    for attempt in range(retries):
        try:
            response = session.get(url, timeout=10)  # 设置超时
            response.raise_for_status()  # 检查请求是否成功
            print(f"请求成功，路径: {url}")
            return response.text, url
        except requests.RequestException as e:
            print(f"获取内容失败: {e}，页面ID: {page_id}，尝试次数: {attempt + 1}")
            time.sleep(2)  # 等待 2 秒后重试
            if attempt == retries - 1:
                return None, url

def contains_keywords(text, keywords):
    return any(keyword in text for keyword in keywords)

def remove_domain_content(text):
    return re.sub(r'\bhttps?://[^\s]+|www\.[^\s]+\.[^\s]+\b', '', text)

def extract_relevant_info(html_content):
    relevant_info = []
    soup = BeautifulSoup(html_content, 'html.parser')
    main_content = soup.find('div', id='main-content', class_='wiki-content')

    if main_content:
        texts = main_content.find_all(string=True)
        if any(contains_keywords(text.strip(), search_keywords) for text in texts):
            for text in texts:
                cleaned_text = text.strip()
                if cleaned_text:
                    cleaned_text = remove_domain_content(cleaned_text)
                    for keyword in keywords:
                        keyword_lower = keyword.lower()
                        index = cleaned_text.lower().find(keyword_lower)
                        while index != -1:
                            if keyword in ['账号密码:', '用户名密码:', '账号/密码', '用户名/密码', '用户/密码']:
                                end_index = min(index + len(keyword) + 10, len(cleaned_text))
                                snippet = f"{keyword}{cleaned_text[index + len(keyword):end_index].strip()}"
                            else:
                                start_index = max(index - 10, 0)
                                end_index = min(index + len(keyword) + 10, len(cleaned_text))
                                snippet = f"{cleaned_text[start_index:index + len(keyword)]}{cleaned_text[index + len(keyword):end_index].strip()}"

                            if snippet:
                                relevant_info.append(snippet)
                            index = cleaned_text.lower().find(keyword_lower, index + 1)

    return relevant_info

def main():
    output_file = 'relevant_info.txt'

    with open('page_ids.txt', 'r') as file:
        page_ids = [line.strip() for line in file if line.strip()]

    results = []  # 存储所有结果

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(fetch_page_content, page_id): index for index, page_id in enumerate(page_ids)}

        for future in as_completed(futures):
            index = futures[future]
            try:
                html_content, request_url = future.result()
                if html_content:
                    relevant_info = extract_relevant_info(html_content)
                    if relevant_info:
                        results.append((len(results) + 1, request_url, relevant_info))
            except Exception as e:
                print(f"请求编号: {index + 1} 处理失败，错误: {e}")

    # 按顺序写入文件
    with open(output_file, 'a') as out_file:
        for request_number, request_url, relevant_info in results:
            out_file.write(f" {request_number}")
            out_file.write(f"请求地址: {request_url}\n")
            for line in relevant_info:
                out_file.write(f"{line}\n")
            out_file.write("\n")

if __name__ == "__main__":
    main()
