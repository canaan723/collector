import json
import requests
import base64
from urllib.parse import urlparse

# 定义一个函数，用于获取并编码网站的Favicon
def get_favicon_base64(url):
    """
    获取指定URL的favicon并返回其Base64编码的字符串。
    优先尝试从根目录获取favicon.ico，失败则使用Google的API。
    """
    try:
        # 解析URL，获取域名
        parsed_url = urlparse(url)
        domain = f"{parsed_url.scheme}://{parsed_url.netloc}"
        favicon_url = f"{domain}/favicon.ico"

        # 1. 尝试直接从根目录获取favicon.ico
        print(f"尝试直接获取: {favicon_url}")
        response = requests.get(favicon_url, timeout=10, stream=True)
        response.raise_for_status()  # 如果状态码不是200，则抛出异常

        # 检查返回的内容类型，确保是图片
        content_type = response.headers.get('Content-Type', '')
        if 'image' in content_type:
            # 读取图片内容并进行Base64编码
            raw_data = response.raw.read()
            # 加上MIME类型前缀，以便在浏览器中正确显示
            return f"data:{content_type};base64,{base64.b64encode(raw_data).decode('utf-8')}"

    except requests.exceptions.RequestException as e:
        print(f"直接获取失败: {e}。尝试使用Google API...")
        # 2. 如果直接获取失败，使用Google S2 Converter服务作为备选
        # 这个服务可以帮助找到网站的图标
        google_api_url = f"https://www.google.com/s2/favicons?sz=64&domain_url={domain}"
        try:
            print(f"尝试Google API: {google_api_url}")
            response = requests.get(google_api_url, timeout=10)
            response.raise_for_status()
            
            # 获取内容类型，并进行Base64编码
            content_type = response.headers.get('Content-Type', 'image/png') # Google API通常返回PNG
            return f"data:{content_type};base64,{base64.b64encode(response.content).decode('utf-8')}"

        except requests.exceptions.RequestException as e_google:
            print(f"Google API获取失败: {e_google}")
            return "" # 如果所有方法都失败，则返回空字符串

    return "" # 默认返回空

# --- 主程序 ---

# 1. 读取JSON文件
try:
    with open('data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
except FileNotFoundError:
    print("错误：'data.json' 文件未找到。请确保文件与脚本在同一目录下。")
    exit()

# 2. 遍历数据并更新icon字段
# 假设数据结构是 [{ "title": "装机必备", "children": [...] }]
if data and 'children' in data[0]:
    websites = data[0]['children']
    for item in websites:
        # 只为icon字段为空的条目进行处理
        if 'url' in item and not item.get('icon'):
            print(f"\n正在处理: {item['title']} ({item['url']})")
            favicon_base64 = get_favicon_base64(item['url'])
            if favicon_base64:
                item['icon'] = favicon_base64
                print(f"成功为 '{item['title']}' 获取并填充了Icon。")
            else:
                print(f"未能为 '{item['title']}' 获取Icon。")

# 3. 将更新后的数据写入新的JSON文件
try:
    with open('data_with_icons.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("\n处理完成！结果已保存至 'data_with_icons.json'。")
except Exception as e:
    print(f"\n写入文件时发生错误: {e}")