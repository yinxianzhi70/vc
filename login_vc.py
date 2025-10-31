#!/usr/bin/env python3
"""
VC 自动登录脚本 - 带完整截屏监控
"""

from DrissionPage import ChromiumPage
import time
import sys

def take_screenshot(tab, name):
    """截屏并显示提示"""
    path = f'logs/{name}.png'
    tab.get_screenshot(path)
    print(f'   📸 截屏: {path}')
    return path

def main():
    print('=' * 60)
    print('🔐 VC 自动登录（邮箱密码方式）')
    print('=' * 60)
    
    # 连接 Chrome
    print('\n连接到 Chrome...')
    try:
        page = ChromiumPage(addr_or_opts='127.0.0.1:9222')
        tab = page.get_tab()
        print('✅ 已连接')
    except Exception as e:
        print(f'❌ 连接失败: {e}')
        return False
    
    # 步骤 1: 访问页面
    print('\n步骤 1: 访问 VC 网站...')
    tab.get('https://www.vestiairecollective.com/sell-clothes-online/')
    print('   等待页面加载...')
    
    for i in range(15):
        time.sleep(1)
        print(f'   等待 {i+1}/15 秒...')
        
        # 尝试查找邮箱输入框
        try:
            email_input = tab.ele('xpath://input[contains(@placeholder, "Email")] | xpath://label[text()="Email"]/following-sibling::input', timeout=1)
            if email_input:
                print(f'   ✅ 找到邮箱输入框（{i+1}秒后）')
                break
        except:
            continue
    else:
        take_screenshot(tab, 'timeout_no_email_input')
        print('\n❌ 15秒后仍未找到邮箱输入框')
        return False
    
    take_screenshot(tab, 'step1_page_loaded')
    
    # 步骤 2: 输入邮箱
    print('\n步骤 2: 输入邮箱...')
    try:
        email_input.clear()
        time.sleep(0.5)
        email_input.input('info@trivesa.it')
        print('   ✅ 已输入: info@trivesa.it')
        time.sleep(2)
        take_screenshot(tab, 'step2_email_entered')
    except Exception as e:
        print(f'   ❌ 错误: {e}')
        take_screenshot(tab, 'step2_error')
        return False
    
    # 步骤 3: 点击 Continue
    print('\n步骤 3: 点击 Continue...')
    try:
        continue_btn = tab.ele('xpath://button[text()="Continue"]', timeout=5)
        if continue_btn:
            continue_btn.click()
            print('   ✅ 已点击')
            time.sleep(5)
            take_screenshot(tab, 'step3_after_continue')
        else:
            print('   ⚠️  未找到按钮，按 Enter')
            email_input.input('\n')
            time.sleep(5)
    except Exception as e:
        print(f'   ⚠️  {e}')
    
    # 步骤 4: 输入密码
    print('\n步骤 4: 输入密码...')
    for i in range(10):
        try:
            password_input = tab.ele('css:input[type="password"]', timeout=1)
            if password_input:
                print(f'   ✅ 找到密码输入框（{i+1}秒后）')
                password_input.clear()
                time.sleep(0.5)
                password_input.input('Florijnlaan@17@Solari@41')
                print('   ✅ 已输入密码')
                time.sleep(2)
                take_screenshot(tab, 'step4_password_entered')
                break
        except:
            time.sleep(1)
            print(f'   等待密码框 {i+1}/10 秒...')
    else:
        print('   ❌ 未找到密码输入框')
        take_screenshot(tab, 'step4_no_password')
        return False
    
    # 步骤 5: 点击登录
    print('\n步骤 5: 点击登录...')
    try:
        login_btn = tab.ele('xpath://button[contains(text(), "Log in")] | xpath://button[@type="submit"]', timeout=5)
        if login_btn:
            login_btn.click()
            print('   ✅ 已点击登录')
        else:
            password_input.input('\n')
            print('   ⚠️  按 Enter 登录')
        
        print('   等待登录完成...')
        time.sleep(10)
        take_screenshot(tab, 'step5_after_login')
    except Exception as e:
        print(f'   ⚠️  {e}')
    
    # 步骤 6: 验证登录
    print('\n步骤 6: 验证登录状态...')
    tab.get('https://www.vestiairecollective.com/')
    time.sleep(5)
    
    if tab.ele('xpath://a[contains(@href, "/sell")]', timeout=5):
        print('\n' + '=' * 60)
        print('✅✅✅ 登录成功！ ✅✅✅')
        print('=' * 60)
        take_screenshot(tab, 'login_success')
        return True
    else:
        print('\n' + '=' * 60)
        print('❌ 登录失败')
        print('=' * 60)
        take_screenshot(tab, 'login_failed')
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)

