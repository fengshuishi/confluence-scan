import requests
import xml.etree.ElementTree as ET
from urllib.parse import urlparse, parse_qs
'''本脚本获取confluence的空间pageid'''
url = "http://confluence.xxxxxxx.com/rest/spacedirectory/1/search"
params = {
    "query": "",
    "status": "current",
    "pageSize": 80
}

# 添加 Cookie
cookies = {
    'JSESSIONID': 'xxxxxxxxxx'
}

page_ids = []
start_indices = [0, 50, 100, 150, 200]  # 指定的 startIndex 值

try:
    for start_index in start_indices:
        params['startIndex'] = start_index
        response = requests.get(url, params=params, cookies=cookies)

        # 打印响应状态码
        print(f"响应状态码: {response.status_code}")

        # 打印响应内容
        print(f"响应内容: {response.text}")

        # 检查响应状态码，确保请求成功
        response.raise_for_status()  # 会抛出 HTTPError 异常

        # 尝试解析 XML
        try:
            root = ET.fromstring(response.content)  # 使用内容解析 XML
        except ET.ParseError as xml_error:
            print("解析 XML 失败:", str(xml_error))
            continue  # 继续下一次循环

        # 提取包含 pageId 的 href
        for space in root.findall('./spaces/link'):
            href = space.get('href')  # 获取 href 属性
            if href and 'pageId=' in href:  # 检查是否包含 pageId
                # 解析 URL 获取 pageId 值
                query = urlparse(href).query
                params = parse_qs(query)
                page_id = params.get('pageId', [None])[0]  # 获取 pageId

                if page_id is not None:
                    page_ids.append(page_id)

    # 输出到 txt 文件
    with open('page_ids.txt', 'w', encoding='utf-8') as f:
        for page_id in page_ids:
            f.write(f"{page_id}\n")

    print("获取到的 pageId 值已输出到 page_ids.txt 文件")

except requests.exceptions.HTTPError as e:
    print(f"HTTP error occurred: {e}")
except Exception as e:
    print(f"An error occurred: {e}")
