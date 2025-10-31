#!/usr/bin/env python3
"""
简化版发布测试 - 手动控制每一步
"""

from DrissionPage import ChromiumPage
import time
import json

page = ChromiumPage(addr_or_opts='127.0.0.1:9222')
tab = page.get_tab()

# 读取产品数据
with open('queue/001.json', 'r') as f:
    data = json.load(f)

print('=' * 60)
print('📦 产品:', data['Title'])
print('=' * 60)

def screenshot(name):
    path = f'logs/{name}.png'
    tab.get_screenshot(path)
    print(f'   📸 {path}')
    return path

# 步骤 1: 访问发布页面
print('\n步骤 1: 访问发布页面...')
tab.get('https://www.vestiairecollective.com/sell-clothes-online/')
time.sleep(8)
screenshot('step1_page_loaded')
print('   ✅ 页面已加载')

# 步骤 2: 选择 Gender
print(f'\n步骤 2: 选择 Gender ({data["Gender"]})...')
gender = tab.ele(f'xpath://span[text()="{data["Gender"]}"]', timeout=10)
if gender:
    gender.click()
    print('   ✅ 已点击')
    time.sleep(1)
    screenshot('step2_gender_selected')
else:
    print('   ❌ 未找到')
    screenshot('step2_error')
    exit(1)

# 步骤 3: 选择 Category
print(f'\n步骤 3: 选择 Category ({data["Category"]})...')
category_select = tab.ele('css:select#preductAddCategory', timeout=10)
if category_select:
    category_select.select.by_text(data['Category'])
    print('   ✅ 已选择')
    time.sleep(1)
    screenshot('step3_category_selected')
else:
    print('   ❌ 未找到下拉框')
    screenshot('step3_error')
    exit(1)

# 步骤 4: 输入 Brand
print(f'\n步骤 4: 输入 Brand ({data["Brand"]})...')
brand_input = tab.ele('css:input#depositForm__form__brands-input', timeout=10)
if brand_input:
    brand_input.clear()
    time.sleep(0.5)
    brand_input.input(data['Brand'])
    print(f'   ✅ 已输入: {data["Brand"]}')
    time.sleep(2)
    screenshot('step4_brand_typed')
    
    # 等待下拉选项出现
    print('   等待品牌下拉选项...')
    time.sleep(2)
    
    # 点击第一个匹配的选项
    brand_option = tab.ele(f'xpath://button[text()="{data["Brand"].title()}"]', timeout=5)
    if not brand_option:
        brand_option = tab.ele(f'xpath://button[contains(text(), "{data["Brand"]}")]', timeout=5)
    
    if brand_option:
        print(f'   找到品牌选项: {brand_option.text}')
        brand_option.click()
        print('   ✅ 已点击品牌')
        time.sleep(1)
        screenshot('step4_brand_selected')
    else:
        print('   ⚠️  未找到品牌选项，继续...')
        screenshot('step4_no_option')
else:
    print('   ❌ 未找到输入框')
    exit(1)

# 步骤 5: 点击 Continue
print('\n步骤 5: 点击 Continue...')
continue_btn = tab.ele('css:button#vc-preduct-add-submit', timeout=10)
if continue_btn:
    disabled = continue_btn.attr('disabled')
    print(f'   Continue 按钮状态: disabled={disabled}')
    
    if disabled and disabled != '':
        print('   ⚠️  按钮被禁用，等待启用...')
        time.sleep(3)
    
    continue_btn.click()
    print('   ✅ 已点击')
    time.sleep(5)
    screenshot('step5_after_continue')
else:
    print('   ❌ 未找到按钮')
    exit(1)

# 步骤 6: 检查是否进入详细信息页面
print('\n步骤 6: 检查页面跳转...')
upload_btn = tab.ele("xpath://button[contains(@class, 'FileUploader')]", timeout=10)
if upload_btn:
    print('   ✅✅✅ 成功进入详细信息页面！')
    screenshot('step6_success')
else:
    print('   ❌ 页面没有跳转')
    screenshot('step6_failed')
    
    # 分析为什么没跳转
    print('\n   当前页面元素:')
    labels = tab.eles('tag:label')[:10]
    for label in labels:
        print(f'     - {label.text}')

print('\n' + '=' * 60)
print('测试完成')
print('=' * 60)
EOF

