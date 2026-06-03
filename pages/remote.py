# local_test.py
from playwright.sync_api import sync_playwright

# 1. 把 <远程设备IP> 替换为第一步获取到的真实 IP（例如 192.168.1.100）
# 2. 并在末尾加上你想运行的浏览器类型，例如 ?browser=chromium
REMOTE_URL = "ws://192.168.58.128:3000/?browser=chromium"

print("正在连接到远程浏览器...")

with sync_playwright() as p:
    # 连接远程服务
    browser = p.chromium.connect(REMOTE_URL)

    # 后续操作与本地完全一致
    context = browser.new_context()
    page = context.new_page()

    page.goto("https://www.baidu.com")
    print(f"成功访问！页面标题为: {page.title()}")

    # 关闭连接，远程浏览器会自动释放
    browser.close()

print("测试完成。")
