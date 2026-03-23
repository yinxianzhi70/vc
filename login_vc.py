#!/usr/bin/env python3
"""
VC 自动登录测试脚本 - 纯邮箱+密码方式

使用方法:
  1. 启动 Chrome: bash start_chrome_simple.sh
  2. 运行此脚本: python3 login_vc.py
"""

import os
import time
import sys
from dotenv import load_dotenv

load_dotenv()

USERNAME = os.getenv('VESTIAIRE_USER', 'info@trivesa.it')
PASSWORD = os.getenv('VESTIAIRE_PASSWORD', '')


def take_screenshot(tab, name):
    """截屏保存到 logs/ 目录"""
    os.makedirs('logs', exist_ok=True)
    path = f'logs/{name}.png'
    tab.get_screenshot(path)
    print(f'   📸 截屏: {path}')
    return path


def wait_cloudflare(tab, timeout=60):
    """等待 Cloudflare 验证通过"""
    print('⏳ 检查 Cloudflare...')
    start = time.time()
    while time.time() - start < timeout:
        title = tab.title.lower() if tab.title else ''
        if any(kw in title for kw in ['just a moment', 'checking your browser', 'please wait']):
            elapsed = int(time.time() - start)
            print(f'   ⏳ Cloudflare 验证中... ({elapsed}s/{timeout}s)')
            time.sleep(2)
        else:
            print('   ✅ Cloudflare 通过')
            return True
    print(f'   ❌ Cloudflare 超时 ({timeout}s)')
    return False


def main():
    from DrissionPage import ChromiumPage

    if not PASSWORD:
        print('❌ 请在 .env 文件中设置 VESTIAIRE_PASSWORD')
        return False

    print('=' * 60)
    print('🔐 VC 自动登录测试（邮箱+密码方式）')
    print(f'   账号: {USERNAME}')
    print('=' * 60)

    # 连接 Chrome
    print('\n1. 连接到 Chrome...')
    try:
        page = ChromiumPage(addr_or_opts='127.0.0.1:9222')
        tab = page.get_tab()
        print('   ✅ 已连接')
    except Exception as e:
        print(f'   ❌ 连接失败: {e}')
        print('   请先运行: bash start_chrome_simple.sh')
        return False

    # 步骤 1: 访问 VC 首页
    print('\n2. 访问 VC 首页...')
    tab.get('https://www.vestiairecollective.com/')
    time.sleep(8)

    if not wait_cloudflare(tab):
        take_screenshot(tab, 'cloudflare_timeout')
        return False

    # 处理 Cookie 弹窗
    try:
        cookie_btn = tab.ele('css:button[id="onetrust-accept-btn-handler"]', timeout=3)
        if cookie_btn:
            cookie_btn.click()
            print('   ✅ 已处理 Cookie 弹窗')
            time.sleep(1)
    except:
        pass

    take_screenshot(tab, 'step1_homepage')

    # 检查是否已登录
    print('\n3. 检查是否已登录...')
    for ind in ['xpath://a[contains(@href, "/sell")]', 'css:a[href*="my-account"]']:
        try:
            if tab.ele(ind, timeout=3):
                print('   ✅ 已登录！无需重新登录')
                take_screenshot(tab, 'already_logged_in')
                return True
        except:
            continue
    print('   未登录，开始登录流程')

    # 步骤 2: 点击 Sign in
    print('\n4. 点击 Sign in...')
    sign_in_selectors = [
        'xpath://span[text()="Sign in"]',
        'xpath://a[text()="Sign in"]',
        'xpath://button[text()="Sign in"]',
        'xpath://a[contains(text(), "Sign in")]',
        'xpath://button[contains(text(), "Sign in")]',
    ]

    sign_in_btn = None
    for selector in sign_in_selectors:
        try:
            sign_in_btn = tab.wait.ele_displayed(selector, timeout=10)
            if sign_in_btn:
                print(f'   找到 Sign in: {selector}')
                break
        except:
            continue

    if not sign_in_btn:
        take_screenshot(tab, 'no_sign_in_button')
        print('   ❌ 未找到 Sign in 按钮')
        return False

    sign_in_btn.click()
    print('   ✅ 已点击 Sign in')
    time.sleep(5)
    take_screenshot(tab, 'step2_modal_opened')

    # 步骤 3: 输入邮箱
    print(f'\n5. 输入邮箱: {USERNAME}...')
    email_selectors = [
        'css:input[id="welcomeEmail"]',
        'css:input[type="email"]',
        'xpath://input[@placeholder="Email"]',
        'css:input[name="email"]',
    ]

    email_input = None
    for selector in email_selectors:
        try:
            email_input = tab.wait.ele_displayed(selector, timeout=10)
            if email_input:
                print(f'   找到邮箱框: {selector}')
                break
        except:
            continue

    if not email_input:
        take_screenshot(tab, 'no_email_input')
        print('   ❌ 未找到邮箱输入框')
        return False

    email_input.clear()
    time.sleep(0.5)
    email_input.input(USERNAME)
    print('   ✅ 已输入邮箱')
    time.sleep(2)
    take_screenshot(tab, 'step3_email_entered')

    # 步骤 4: 点击 Continue
    print('\n6. 点击 Continue...')
    continue_selectors = [
        'xpath://button[text()="Continue"]',
        'xpath://button[contains(text(), "Continue")]',
        'css:button[data-testid="welcome_continue_btn"]',
        'css:button[type="submit"]',
    ]

    continue_btn = None
    for selector in continue_selectors:
        try:
            continue_btn = tab.wait.ele_displayed(selector, timeout=10)
            if continue_btn:
                print(f'   找到 Continue: {selector}')
                break
        except:
            continue

    if continue_btn:
        try:
            continue_btn.click()
        except Exception:
            tab.run_js('arguments[0].click()', continue_btn)
    else:
        print('   ⚠️ 未找到 Continue 按钮，用 JS 后备')
        tab.run_js('''
            let btns = Array.from(document.querySelectorAll('button'));
            let btn = btns.find(b => b.textContent.trim().toLowerCase() === 'continue');
            if (btn) btn.click();
        ''')

    print('   ✅ 已点击 Continue')
    time.sleep(8)
    take_screenshot(tab, 'step4_after_continue')

    # 步骤 5: 输入密码
    print('\n7. 输入密码...')
    password_selectors = [
        'css:input[id="loginPassword"]',
        'css:input[type="password"]',
        'css:input[name="password"]',
    ]

    password_input = None
    for selector in password_selectors:
        try:
            password_input = tab.wait.ele_displayed(selector, timeout=15)
            if password_input:
                print(f'   找到密码框: {selector}')
                break
        except:
            continue

    if not password_input:
        take_screenshot(tab, 'no_password_input')
        print('   ❌ 未找到密码输入框')
        # 输出当前页面信息以便调试
        print(f'   当前 URL: {tab.url}')
        print(f'   页面标题: {tab.title}')
        return False

    password_input.clear()
    time.sleep(0.5)
    password_input.input(PASSWORD)
    print('   ✅ 已输入密码')
    time.sleep(2)
    take_screenshot(tab, 'step5_password_entered')

    # 步骤 6: 点击 Log in
    print('\n8. 点击 Log in...')
    submit_selectors = [
        'xpath://button[text()="Log in"]',
        'xpath://button[contains(text(), "Log in")]',
        'css:button[type="submit"]',
    ]

    submit_btn = None
    for selector in submit_selectors:
        try:
            submit_btn = tab.wait.ele_displayed(selector, timeout=10)
            if submit_btn:
                print(f'   找到 Log in: {selector}')
                break
        except:
            continue

    if submit_btn:
        try:
            submit_btn.click()
        except Exception:
            tab.run_js('arguments[0].click()', submit_btn)
    else:
        print('   ⚠️ 未找到 Log in 按钮，模拟回车')
        password_input.input('\n')

    print('   ✅ 已点击 Log in，等待...')
    time.sleep(15)
    take_screenshot(tab, 'step6_after_login')

    # 步骤 7: 验证登录
    print('\n9. 验证登录...')
    tab.get('https://www.vestiairecollective.com/')
    time.sleep(8)
    wait_cloudflare(tab)

    # 检查是否已登录
    success_indicators = [
        'xpath://a[contains(@href, "/sell")]',
        'css:a[href*="my-account"]',
        'css:a[href*="profile"]',
    ]

    for ind in success_indicators:
        try:
            if tab.ele(ind, timeout=5):
                print('\n' + '=' * 60)
                print('✅✅✅ 登录成功！ ✅✅✅')
                print('=' * 60)
                take_screenshot(tab, 'login_success')
                return True
        except:
            continue

    # 最后检查：页面上是否还有 Sign in
    has_sign_in = tab.run_js('''
        let els = Array.from(document.querySelectorAll('a, button, span'));
        return els.some(el => el.textContent.trim() === 'Sign in');
    ''')

    if not has_sign_in:
        print('\n' + '=' * 60)
        print('✅ 登录成功（未检测到 Sign in 按钮）')
        print('=' * 60)
        take_screenshot(tab, 'login_success')
        return True

    print('\n' + '=' * 60)
    print('❌ 登录失败')
    print('=' * 60)
    print(f'   当前 URL: {tab.url}')
    print(f'   页面标题: {tab.title}')
    take_screenshot(tab, 'login_failed')
    return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
