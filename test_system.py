#!/usr/bin/env python3
"""
VC 系统测试脚本 - 简化版
测试 Chrome 连接和图片查找功能
"""

import sys
import os
import json
from pathlib import Path

# 添加当前目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("🧪 VC 系统测试")
print("=" * 60)
print()

# 测试 1: 检查 Python 模块
print("📦 测试 1: 检查 Python 模块...")
try:
    from DrissionPage import Chromium
    print("   ✅ DrissionPage 已安装")
except ImportError:
    print("   ❌ DrissionPage 未安装")
    print("   请运行: pip3 install DrissionPage")
    sys.exit(1)

try:
    import pics_odoo
    print("   ✅ pics_odoo 模块正常")
except ImportError as e:
    print(f"   ❌ pics_odoo 导入失败: {e}")
    sys.exit(1)

print()

# 测试 2: 检查图片查找功能
print("📸 测试 2: 检查图片查找功能...")
queue_dir = Path(__file__).parent / 'queue'
if not queue_dir.exists() or not list(queue_dir.glob('*.json')):
    print("   ❌ 队列目录为空")
    sys.exit(1)

json_file = list(queue_dir.glob('*.json'))[0]
print(f"   使用测试文件: {json_file.name}")

with open(json_file, 'r') as f:
    test_data = json.load(f)

print(f"   产品: {test_data.get('Title', 'Unknown')}")
print(f"   External reference: {test_data.get('External reference', 'Unknown')}")

# 测试图片查找
saved_paths = pics_odoo.save_all_pics(test_data)
if saved_paths:
    print(f"   ✅ 找到 {len(saved_paths)} 张图片")
else:
    print("   ❌ 未找到图片")
    sys.exit(1)

print()

# 测试 3: 检查 Chrome 连接
print("🌐 测试 3: 连接到 Chrome...")
print("   ⚠️  请确保 Chrome 已启动（端口 9222）")
print()

try:
    from DrissionPage import ChromiumPage
    page = ChromiumPage(addr_or_opts='127.0.0.1:9222')
    tab = page.get_tab()
    
    print(f"   ✅ 成功连接到 Chrome")
    print(f"   当前 URL: {tab.url}")
    print(f"   页面标题: {tab.title}")
    
    # 测试访问 VC 网站
    print()
    print("   测试访问 VC 网站...")
    tab.get('https://www.vestiairecollective.com/')
    tab.wait(3)
    
    # 检查登录状态
    print("   检查登录状态...")
    login_indicators = [
        'xpath://a[contains(@href, "/sell")]',
        'xpath://button[contains(text(), "Sell")]',
    ]
    
    is_logged_in = False
    for indicator in login_indicators:
        try:
            if tab.ele(indicator, timeout=2):
                is_logged_in = True
                break
        except:
            continue
    
    if is_logged_in:
        print("   ✅ 已登录到 VC")
    else:
        print("   ⚠️  未检测到登录状态")
        print("   请在 Chrome 中手动登录 VC (info@trivesa.it)")
    
except Exception as e:
    print(f"   ❌ 连接失败: {e}")
    print()
    print("   💡 解决方法:")
    print("   1. 打开新的终端窗口")
    print("   2. 复制粘贴以下命令启动 Chrome:")
    print()
    print("/Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome \\")
    print("  --user-data-dir=\"$HOME/Library/Application Support/Google/Chrome\" \\")
    print("  --profile-directory=\"Profile 7\" \\")
    print("  --remote-debugging-port=9222 \\")
    print("  --no-first-run \\")
    print("  --no-default-browser-check &")
    print()
    print("   3. 等待 Chrome 打开后，重新运行此脚本")
    sys.exit(1)

print()
print("=" * 60)
print("✅ 所有测试通过！系统已就绪")
print("=" * 60)
print()
print("🚀 下一步:")
print("   如果要发布产品，运行:")
print("   python3 process_queue.py")
print()

