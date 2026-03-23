import time
import smart
import pics_odoo as pics  # 使用新的 Odoo 图片处理模块
import platform
import os
import sys
import subprocess
import re

from loguru import logger
from DrissionPage.common import Keys
from DrissionPage import ChromiumPage, ChromiumOptions, SessionPage, SessionOptions
from dotenv import load_dotenv


def _wait_cloudflare(tab, timeout=60):
    """等待 Cloudflare 验证通过"""
    logger.info("⏳ 检查 Cloudflare 验证...")
    start = time.time()
    while time.time() - start < timeout:
        title = tab.title.lower() if tab.title else ''
        if any(kw in title for kw in ['just a moment', 'checking your browser', 'please wait']):
            elapsed = int(time.time() - start)
            logger.info(f"⏳ Cloudflare 验证中... ({elapsed}s/{timeout}s)")
            tab.wait(2)
        else:
            logger.info("✅ Cloudflare 验证通过")
            return True
    logger.error(f"❌ Cloudflare 验证超时 ({timeout}s)")
    return False


def _dismiss_popups(tab):
    """处理 Cookie 弹窗和购物偏好弹窗"""
    # Cookie 弹窗
    cookie_selectors = [
        'css:button[id="onetrust-accept-btn-handler"]',
        'xpath://button[contains(text(), "Accept")]',
        'xpath://button[contains(text(), "Accept all")]',
    ]
    for selector in cookie_selectors:
        try:
            btn = tab.ele(selector, timeout=3)
            if btn:
                btn.click()
                logger.debug(f"✅ 已处理 Cookie 弹窗: {selector}")
                tab.wait(1)
                break
        except:
            continue

    # 购物偏好弹窗 (有时会出现 "Select shopping preference" → Continue)
    try:
        pref_btn = tab.ele('xpath://button[contains(text(), "Continue")]', timeout=3)
        if pref_btn:
            pref_btn.click()
            logger.debug("✅ 已处理购物偏好弹窗")
            tab.wait(2)
    except:
        pass


def login(tab, username, password, max_retries=3):
    """登录到 Vestiaire Collective（纯邮箱+密码方式）"""

    # ── 第0步：检查是否已经登录 ──
    logger.info("检查是否已经登录...")
    try:
        tab.get('https://www.vestiairecollective.com/')
        tab.wait(10)
        _wait_cloudflare(tab)
        _dismiss_popups(tab)

        logged_in_indicators = [
            'xpath://a[contains(@href, "/sell")]',
            'xpath://button[contains(text(), "Sell")]',
            'css:a[href*="my-account"]',
            'css:a[href*="profile"]',
        ]
        for ind in logged_in_indicators:
            try:
                if tab.ele(ind, timeout=3):
                    logger.info(f"✅ 已登录（检测到: {ind}），无需重新登录")
                    return True
            except:
                continue
        logger.info("未检测到已登录状态，开始登录流程")
    except Exception as e:
        logger.warning(f"检查登录状态时出错: {e}")

    # ── 开始登录重试循环 ──
    for attempt in range(max_retries):
        try:
            logger.info(f'🔐 开始登录 (第 {attempt + 1}/{max_retries} 次尝试)')

            # ── 第1步：访问首页并等待 Cloudflare ──
            tab.get('https://www.vestiairecollective.com/')
            tab.wait(8)
            if not _wait_cloudflare(tab):
                logger.warning("Cloudflare 未通过，重试...")
                tab.wait(10)
                continue

            _dismiss_popups(tab)
            tab.wait(2)

            logger.debug(f'当前 URL: {tab.url}')
            logger.debug(f'页面标题: {tab.title}')

            # ── 第2步：点击 "Sign in" 打开登录模态框 ──
            logger.info("步骤 1: 点击 Sign in...")
            sign_in_selectors = [
                'xpath://span[text()="Sign in"]',
                'xpath://a[text()="Sign in"]',
                'xpath://button[text()="Sign in"]',
                'css:a[href*="login"]',
                'css:button[data-testid="header-login-button"]',
                'xpath://button[contains(text(), "Sign in")]',
                'xpath://a[contains(text(), "Sign in")]',
                'xpath://button[contains(text(), "Log in")]',
            ]

            sign_in_btn = None
            for selector in sign_in_selectors:
                try:
                    sign_in_btn = tab.wait.ele_displayed(selector, timeout=10)
                    if sign_in_btn:
                        logger.debug(f"找到 Sign in 按钮: {selector}")
                        break
                except:
                    continue

            if not sign_in_btn:
                logger.error("❌ 未找到 Sign in 按钮")
                if attempt < max_retries - 1:
                    tab.wait(15)
                    continue
                raise Exception("未找到 Sign in 按钮")

            sign_in_btn.click()
            logger.info("✅ 已点击 Sign in")
            tab.wait(5)

            # ── 第3步：在模态框中输入邮箱 ──
            logger.info("步骤 2: 输入邮箱...")
            email_selectors = [
                'css:input[id="welcomeEmail"]',
                'css:input[type="email"]',
                'xpath://input[@placeholder="Email"]',
                'css:input[name="email"]',
            ]

            email_input = None
            for selector in email_selectors:
                try:
                    email_input = tab.wait.ele_displayed(selector, timeout=15)
                    if email_input:
                        logger.debug(f"找到邮箱输入框: {selector}")
                        break
                except:
                    continue

            if not email_input:
                logger.error("❌ 未找到邮箱输入框")
                if attempt < max_retries - 1:
                    tab.wait(15)
                    continue
                raise Exception("未找到邮箱输入框")

            email_input.clear()
            tab.wait(0.5)
            email_input.input(username)
            logger.info(f"✅ 已输入邮箱: {username}")
            tab.wait(2)

            # ── 第4步：点击 Continue ──
            logger.info("步骤 3: 点击 Continue...")
            continue_selectors = [
                'css:button[data-testid="welcome_continue_btn"]',
                'xpath://button[text()="Continue"]',
                'xpath://button[contains(text(), "Continue")]',
                'css:button[type="submit"]',
            ]

            continue_btn = None
            for selector in continue_selectors:
                try:
                    continue_btn = tab.wait.ele_displayed(selector, timeout=10)
                    if continue_btn:
                        logger.debug(f"找到 Continue 按钮: {selector}")
                        break
                except:
                    continue

            if not continue_btn:
                # JavaScript 后备
                logger.warning("未找到 Continue 按钮，尝试 JavaScript 点击")
                clicked = tab.run_js('''
                    let btns = Array.from(document.querySelectorAll('button'));
                    let btn = btns.find(b => b.textContent.trim().toLowerCase() === 'continue');
                    if (!btn) btn = document.querySelector('form button[type="submit"]');
                    if (btn) { btn.click(); return true; }
                    return false;
                ''')
                if not clicked:
                    logger.error("❌ 无法点击 Continue")
                    if attempt < max_retries - 1:
                        tab.wait(15)
                        continue
                    raise Exception("无法点击 Continue")
            else:
                try:
                    continue_btn.click()
                except Exception:
                    tab.run_js('arguments[0].click()', continue_btn)

            logger.info("✅ 已点击 Continue")
            tab.wait(8)  # 等待密码输入框出现

            # ── 第5步：输入密码 ──
            logger.info("步骤 4: 输入密码...")
            password_selectors = [
                'css:input[id="loginPassword"]',
                'css:input[type="password"]',
                'css:input[name="password"]',
                'xpath://input[@type="password"]',
            ]

            password_input = None
            for selector in password_selectors:
                try:
                    password_input = tab.wait.ele_displayed(selector, timeout=15)
                    if password_input:
                        logger.debug(f"找到密码输入框: {selector}")
                        break
                except:
                    continue

            if not password_input:
                # JavaScript 后备：强制显示隐藏的密码框
                tab.run_js('''
                    let inp = document.querySelector('input[type="password"]');
                    if (inp) {
                        inp.style.display = 'block';
                        inp.style.visibility = 'visible';
                        inp.style.opacity = '1';
                    }
                ''')
                tab.wait(2)
                for selector in password_selectors:
                    try:
                        password_input = tab.wait.ele_displayed(selector, timeout=5)
                        if password_input:
                            break
                    except:
                        continue

            if not password_input:
                logger.error("❌ 未找到密码输入框")
                if attempt < max_retries - 1:
                    tab.wait(15)
                    continue
                raise Exception("未找到密码输入框")

            password_input.clear()
            tab.wait(0.5)
            password_input.input(password)
            logger.info("✅ 已输入密码")
            tab.wait(3)

            # ── 第6步：点击 Log in ──
            logger.info("步骤 5: 点击 Log in...")
            submit_selectors = [
                'xpath://button[text()="Log in"]',
                'xpath://button[contains(text(), "Log in")]',
                'css:button[type="submit"]',
                'css:button[data-testid="login-submit"]',
            ]

            submit_btn = None
            for selector in submit_selectors:
                try:
                    submit_btn = tab.wait.ele_displayed(selector, timeout=10)
                    if submit_btn:
                        logger.debug(f"找到 Log in 按钮: {selector}")
                        break
                except:
                    continue

            if submit_btn:
                try:
                    submit_btn.click()
                except Exception:
                    tab.run_js('arguments[0].click()', submit_btn)
            else:
                # 后备：按回车
                logger.warning("未找到 Log in 按钮，模拟回车")
                password_input.input('\n')

            logger.info("✅ 已点击 Log in，等待登录完成...")
            tab.wait(15)

            # ── 第7步：验证登录成功 ──
            logger.info("步骤 6: 验证登录...")

            # 先检查 URL 是否已跳转离开登录页
            current_url = tab.url
            logger.debug(f"当前 URL: {current_url}")

            # 再查找已登录标志
            success_indicators = [
                'xpath://a[contains(@href, "/sell")]',
                'css:a[href*="my-account"]',
                'css:a[href*="profile"]',
                'xpath://button[contains(text(), "Sell")]',
                'xpath://span[contains(text(), "Sell an item")]',
            ]

            login_success = False
            for ind in success_indicators:
                try:
                    if tab.ele(ind, timeout=5):
                        login_success = True
                        break
                except:
                    continue

            # 如果在当前页面没找到，尝试访问首页再检查
            if not login_success:
                tab.get('https://www.vestiairecollective.com/')
                tab.wait(8)
                _wait_cloudflare(tab)
                for ind in success_indicators:
                    try:
                        if tab.ele(ind, timeout=5):
                            login_success = True
                            break
                    except:
                        continue

            # 最终检查：页面上是否还有 "Sign in" 按钮
            if not login_success:
                try:
                    has_sign_in = tab.run_js('''
                        let els = Array.from(document.querySelectorAll('a, button, span'));
                        return els.some(el => el.textContent.trim() === 'Sign in');
                    ''')
                    if not has_sign_in:
                        login_success = True
                        logger.info("未检测到 Sign in 按钮，判定为已登录")
                except:
                    pass

            if login_success:
                logger.info('=' * 50)
                logger.info('✅✅✅ 登录成功！ ✅✅✅')
                logger.info('=' * 50)
                return True
            else:
                # 检查错误消息
                try:
                    error_el = tab.ele('css:div[class*="error"], div[class*="alert"]', timeout=3)
                    if error_el:
                        logger.error(f"登录失败，错误信息: {error_el.text}")
                except:
                    pass
                logger.error("❌ 登录失败，未检测到成功标志")
                if attempt < max_retries - 1:
                    tab.wait(15)
                    continue
                raise Exception("登录失败")

        except Exception as e:
            logger.error(f"登录过程中出错: {e}")
            if attempt < max_retries - 1:
                logger.info(f"等待 15 秒后重试...")
                tab.wait(15)
            continue

    logger.error(f"❌ 登录失败，已尝试 {max_retries} 次")
    return False


def goto_the_position(tab, type, cat, brand):
    """Go to the position where the bot can start to collect data"""
    logger.debug(f'Go to the Sell an Item page, and choose the category')

    try:
        # 截屏：开始
        screenshot_path = f'logs/screenshot_start_{int(time.time())}.png'
        os.makedirs('logs', exist_ok=True)
        
        tab.listen.start('https://collector.vestiairecollective.com/com.snowplowanalytics.snowplow/tp2')
        tab.get('https://www.vestiairecollective.com/sell-clothes-online/')

        tab.listen.wait()
        
        # 截屏：页面加载后
        tab.get_screenshot(screenshot_path)
        logger.debug(f'Category page is loaded, screenshot: {screenshot_path}')

        # 处理Welcome弹窗（优先处理，在最顶层）
        try:
            welcome_close_selectors = [
                'xpath://button[contains(@aria-label, "Close")]',
                'xpath://button[contains(@class, "close")]//ancestor::div[contains(@class, "welcome") or contains(@class, "Welcome") or contains(@class, "popin")]',
                'css:div[class*="popin"] button[class*="close"]',
                'css:div[class*="welcome"] button',
                'xpath://div[contains(@class, "ModalContainer")]//button',
                'xpath://button[contains(text(), "×")]',
                'css:button[aria-label="Close"]',
            ]
            
            welcome_closed = False
            for selector in welcome_close_selectors:
                try:
                    close_button = tab.ele(selector, timeout=2)
                    if close_button and close_button.attr('type') != 'submit':
                        close_button.click()
                        welcome_closed = True
                        logger.debug(f'✅ 已关闭Welcome弹窗（关闭按钮）')
                        tab.wait(2)
                        break
                except:
                    continue
        except Exception as e:
            logger.debug(f'处理Welcome弹窗关闭按钮时出错: {e}')

        # 处理Cookie同意弹窗
        try:
            # 先尝试Accept按钮（黑色按钮在右侧）
            cookie_selectors = [
                'xpath://button[text()="Accept"]',
                'xpath://button[contains(text(), "Accept")]',
                'css:button[class*="accept"]',
                'css:button[id*="accept"]',
                'xpath://button[contains(text(), "接受")]',
            ]
            
            cookie_clicked = False
            for selector in cookie_selectors:
                try:
                    cookie_button = tab.ele(selector, timeout=2)
                    if cookie_button:
                        cookie_button.click()
                        cookie_clicked = True
                        logger.debug(f'✅ 已点击Cookie Accept按钮')
                        tab.wait(2)
                        break
                except:
                    continue
            
            if not cookie_clicked:
                # 尝试查找"Continue without accepting"链接
                try:
                    continue_link = tab.ele('xpath://a[contains(text(), "Continue without accepting")]', timeout=2)
                    if continue_link:
                        continue_link.click()
                        logger.debug(f'✅ 已点击"Continue without accepting"')
                        tab.wait(2)
                except:
                    pass
        except Exception as e:
            logger.debug(f'处理Cookie弹窗时出错: {e}')

        # 处理隐私政策弹窗
        try:
            tab.ele('button#popin_tc_privacy_button_2', timeout=3).click()
            logger.debug('✅ 已处理隐私政策弹窗')
            tab.wait(1)
        except:
            pass

        # Choose the category
        tab.wait.ele_displayed("css:input[data-role='search']", timeout=15)
        tab.wait(1)

        logger.debug(f'Click the Type: {type}')
        
        # 尝试多个选择器，包括更多可能的元素类型
        selectors = [
            # 原始选择器
            f"xpath://span[contains(@class, 'universe-selector_depositForm__form__universeLabel') and text()='{type}']",
            f"xpath://span[contains(@class, 'universeLabel') and text()='{type}']",
            f"xpath://span[text()='{type}']",
            # 扩展选择器 - button类型
            f"xpath://button[contains(text(), '{type}')]",
            f"xpath://button[contains(@class, 'universe') and contains(text(), '{type}')]",
            # div类型
            f"xpath://div[contains(@class, 'universe') and contains(text(), '{type}')]",
            f"xpath://div[contains(text(), '{type}')]",
            # label类型
            f"xpath://label[contains(text(), '{type}')]",
            # 通用文本匹配（不区分大小写）
            f"xpath://*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{type.lower()}')]",
            # 查找所有包含text的span元素
            f"xpath://span[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{type.lower()}')]",
        ]
        
        gender_clicked = False
        for selector in selectors:
            try:
                element = tab.ele(selector, timeout=3)
                if element:
                    # 尝试点击
                    try:
                        element.click()
                    except:
                        # 如果直接点击失败，尝试JavaScript点击
                        tab.run_js('arguments[0].click()', element)
                    
                    gender_clicked = True
                    logger.debug(f'✅ 成功点击 Gender: {type} (使用选择器: {selector[:50]}...)')
                    tab.wait(2)  # 等待页面响应
                    break
            except Exception as e:
                logger.debug(f'选择器失败: {selector[:50]}... - {str(e)[:50]}')
                continue
        
        # 如果所有选择器都失败，尝试查找页面上所有可能的Gender选项
        if not gender_clicked:
            logger.warning(f'所有选择器都失败，尝试查找页面上所有Gender选项...')
            try:
                # 查找所有包含Gender文本的元素
                all_elements = tab.eles('xpath://*[contains(text(), "Womenswear") or contains(text(), "Menswear") or contains(text(), "Girlswear") or contains(text(), "Boyswear")]')
                logger.debug(f'找到 {len(all_elements)} 个可能的Gender元素')
                
                for elem in all_elements[:10]:  # 只检查前10个
                    try:
                        elem_text = elem.text.strip() if elem.text else ''
                        if type.lower() in elem_text.lower():
                            logger.debug(f'找到匹配元素: {elem_text}')
                            try:
                                elem.click()
                            except:
                                tab.run_js('arguments[0].click()', elem)
                            gender_clicked = True
                            logger.debug(f'✅ 成功点击 Gender: {type}')
                            tab.wait(2)
                            break
                    except:
                        continue
            except Exception as e:
                logger.debug(f'查找所有元素失败: {e}')
        
        if not gender_clicked:
            # 截屏：找不到元素
            error_screenshot = f'logs/error_gender_{int(time.time())}.png'
            tab.get_screenshot(error_screenshot)
            
            # 尝试输出页面HTML用于调试
            try:
                page_html = tab.html[:2000]  # 前2000字符
                logger.debug(f'页面HTML片段: {page_html[:500]}')
            except:
                pass
            
            logger.error(f'❌ 找不到 Gender 按钮，截屏: {error_screenshot}')
            raise Exception(f'Cannot find Gender button: {type}')

        tab.wait(1)

        logger.debug(f'Choose the Category: {cat}')
        
        # Category 映射（VC 网站上的实际类别名称）
        category_mapping = {
            'Slippers': 'Mules & Clogs',
            'Sneakers': 'Trainers',
            'Boots': 'Boots',
            'Sandals': 'Sandals',
            'Flats': 'Flats',
            'Heels': 'Heels',
            'Handbags': 'Handbags',
            'Bags': 'Handbags',
            'Shoes': 'Trainers',  # 如果Category是Shoes，默认映射到Trainers
        }
        
        vc_category = category_mapping.get(cat, cat)
        
        # 等待Category选择框出现
        tab.wait(2)  # 等待页面响应
        
        # 尝试多个Category选择器
        category_selectors = [
            'css:select#preductAddCategory',
            'css:#preductAddCategory',
            'css:select[id*="Category"]',
            'css:select[name*="category"]',
            'css:select[class*="category"]',
            'xpath://select[@id="preductAddCategory"]',
            'xpath://select[contains(@id, "Category")]',
        ]
        
        category_select = None
        for selector in category_selectors:
            try:
                category_select = tab.ele(selector, timeout=5)
                if category_select:
                    logger.debug(f'✅ 找到Category选择框: {selector}')
                    break
            except:
                continue
        
        if category_select:
            # 先尝试用文本选择
            try:
                category_select.select.by_text(vc_category)
                logger.debug(f'✅ 已选择 Category: {vc_category}')
            except:
                # 如果失败，用 JavaScript 强制设置
                logger.debug(f'Select by text 失败，用 JavaScript 设置...')
                # 查找 value
                try:
                    options = category_select.eles('tag:option')
                    target_value = None
                    for opt in options:
                        opt_text = opt.text.strip() if opt.text else ''
                        if vc_category.lower() in opt_text.lower() or opt_text.lower() in vc_category.lower():
                            target_value = opt.attr('value')
                            logger.debug(f'找到匹配选项: {opt_text} -> {target_value}')
                            break
                    
                    if target_value:
                        # 使用选择框的实际ID或选择器
                        select_id = category_select.attr('id') or 'preductAddCategory'
                        tab.run_js(f'''
                            const select = document.querySelector('#{select_id}');
                            if (select) {{
                                select.value = '{target_value}';
                                select.dispatchEvent(new Event('change', {{ bubbles: true }}));
                                select.dispatchEvent(new Event('input', {{ bubbles: true }}));
                            }}
                        ''')
                        logger.debug(f'✅ 用 JavaScript 设置 Category: {vc_category} (value={target_value})')
                    else:
                        logger.warning(f'⚠️  未找到 Category: {vc_category}')
                except Exception as e:
                    logger.warning(f'⚠️  处理Category选项时出错: {e}')
        else:
            # 如果找不到选择框，尝试截屏并输出页面信息用于调试
            error_screenshot = f'logs/error_category_select_{int(time.time())}.png'
            tab.get_screenshot(error_screenshot)
            logger.error(f'❌ 未找到 Category 下拉框，截屏: {error_screenshot}')
            
            # 尝试输出页面上的所有select元素
            try:
                all_selects = tab.eles('css:select')
                logger.debug(f'页面上找到 {len(all_selects)} 个select元素')
                for i, sel in enumerate(all_selects[:5]):  # 只显示前5个
                    sel_id = sel.attr('id') or '无ID'
                    sel_name = sel.attr('name') or '无name'
                    logger.debug(f'Select {i+1}: ID={sel_id}, Name={sel_name}')
            except:
                pass
            
            raise Exception('Cannot find category select')

        tab.wait(2)

        logger.debug(f'Input the brand: {brand}')
        brand_input = tab.ele(f'xpath://input[@id="depositForm__form__brands-input"]', timeout=10)
        
        # 清空并输入品牌
        brand_input.clear()
        tab.wait(0.5)
        
        # 逐字输入（模拟真实输入）
        for char in brand:
            brand_input.input(char)
            tab.wait(0.15)
        
        # 等待品牌下拉选项出现
        logger.debug('等待品牌下拉选项出现...')
        brand_selected = False
        for i in range(10):
            tab.wait(0.5)
            # 尝试多个选择器
            brand_selectors = [
                f'xpath://button[text()="{brand.title()}"]',  # Prada
                f'xpath://*[text()="{brand.title()}"]',
                f'xpath://*[contains(text(), "{brand.upper()}")]',
                f'xpath://*[contains(@class, "brand-search") and contains(., "{brand.title()}")]',
            ]
            
            for selector in brand_selectors:
                try:
                    brand_option = tab.ele(selector, timeout=1)
                    if brand_option:
                        brand_option.click()
                        logger.debug(f'✅ 已选择品牌: {brand_option.text}')
                        brand_selected = True
                        break
                except:
                    continue
            
            if brand_selected:
                break
        
        if not brand_selected:
            logger.warning(f'⚠️  未找到品牌选项，继续尝试...')
            # 使用 smart_click 作为后备
            options_css_xpath = "xpath://*[contains(@class, 'brand-search_depositForm__form__optionsList__item__value')]/../../.."
            click_rule = "xpath://*[contains(@class, 'brand-search_depositForm__form__optionsList__item__value__') and normalize-space() = '{replace_name}']/.."
            smart.smart_click(tab, mode='click', options_css_xpath=options_css_xpath, click_rule=click_rule, org_name=brand)
        
        tab.wait(2)

        # 等待 Continue 按钮可点击（尝试多种选择器）
        continue_selectors = [
            'css:button#vc-preduct-add-submit',  # 直接用 ID
            'xpath://button[@id="vc-preduct-add-submit"]',
            'xpath://button[@id="vc-preduct-add-submit" and not(@disabled)]',
        ]
        
        continue_btn = None
        for selector in continue_selectors:
            try:
                continue_btn = tab.wait.ele_displayed(selector, timeout=5)
                if continue_btn:
                    logger.debug(f'找到 Continue 按钮: {selector}')
                    break
            except:
                continue
        
        if not continue_btn:
            screenshot = f'logs/error_no_continue_{int(time.time())}.png'
            tab.get_screenshot(screenshot)
            logger.error(f'未找到 Continue 按钮，截屏: {screenshot}')
            raise Exception('Cannot find Continue button')
        
        tab.wait(2)
        logger.debug('Click continue button')
        continue_btn.click()
        
        logger.debug('等待页面跳转...')
        tab.wait(3)

        # Check whether on the product adding page
        screenshot_before = f'logs/before_wait_{int(time.time())}.png'
        tab.get_screenshot(screenshot_before)
        logger.debug(f'等待文件上传按钮出现，当前截屏: {screenshot_before}')
        
        upload_btn = tab.wait.ele_displayed("xpath://button[contains(@class, 'FileUploader_field-file-fake__')]", timeout=20)
        if not upload_btn:
            screenshot_timeout = f'logs/timeout_upload_btn_{int(time.time())}.png'
            tab.get_screenshot(screenshot_timeout)
            logger.error(f'未找到文件上传按钮，截屏: {screenshot_timeout}')
            raise Exception('Cannot find upload button, page may not have transitioned')

        logger.success('The page is in the right from')

        return True

    except Exception as e:
        raise Exception(f"Filter step failed, {e}")


def submit_step1_details(tab, product_data):
    """fill the form for the 1st step"""
    logger.success('Enter 1st step')

    if tab.ele("xpath://label[text()='External reference']", timeout=1):
        logger.debug(f'Input External reference: {product_data["External reference"]}')
        tab.ele(f"xpath:input[id='external_reference']").input(product_data["External reference"])

    if tab.ele("xpath://div/label[text()='Category']", timeout=1):

        logger.debug(f'Choose the Category: {product_data["Category"]}')

        # Details 里面的分类有两种情况
        # 1.匹配上一轮的分类名称
        # 2.匹配表中 Details-category 的名称
        # 3.如果两个都不匹配，则抛出异常
        details_cat = product_data['Details - Category'] if product_data['Details - Category'] else product_data['Category']

        input_xpath_css = 'css:input[id="subcategory"]'
        option_css_xpath = "xpath://ul/li[@data-component-id='subcategory']/.."
        click_xpath_css = "xpath://ul/li[@data-component-id='subcategory' and normalize-space()='{replace_name}']"
        input_search_click(tab, input_xpath_css, option_css_xpath, click_xpath_css, details_cat)

        tab.wait(1)

    logger.debug(f'Choose the condition: {product_data["Conditions"]}')
    tab.ele(f"xpath://label[text()='Condition']").click(by_js=True)
    tab.wait(1)

    tab.ele(f"xpath://label[text()='Condition']/following-sibling::*//ul/li/span[text()='{product_data['Conditions']}']").click(by_js=True)

    tab.wait(2)

    if tab.ele(f"xpath://label[text()='Model']/following-sibling::*", timeout=0):

        if not product_data["Model"]:
            product_data["Model"] = 'Other'

        logger.debug(f'Choose the Model: {product_data["Model"]}')
        tab.ele(f"xpath://label[text()='Model']/following-sibling::*").click()
        tab.wait(5)

        tab.ele(f"xpath://input[@placeholder='Find your item model']").input(product_data['Model'])
        tab.wait(1)

        is_model_none = tab.ele(f"xpath://button[text()='None of these']")
        if is_model_none:
            is_model_none.click()
        else:
            model_btn = tab.ele(f"xpath://span[contains(@class, 'ModelSelect_modelsModal__list') and text()='Centennial']")
            if model_btn:
                model_btn.click()

    tab.wait(1)

    # input materials
    input_xpath_css = 'css:div[data-component-id="material"] > button'
    option_css_xpath = "xpath://ul/li[@data-component-id='material']/.."
    click_xpath_css = "xpath://ul/li[@data-component-id='material' and normalize-space()='{replace_name}']"
    input_search_click(tab, input_xpath_css, option_css_xpath, click_xpath_css, product_data["Material"])

    # input color
    input_xpath_css = 'css:input[id="color"]'
    option_css_xpath = "xpath://ul/li[@data-component-id='color']/.."
    click_xpath_css = "xpath://ul/li[@data-component-id='color' and normalize-space()='{replace_name}']"
    input_search_click(tab, input_xpath_css, option_css_xpath, click_xpath_css, product_data["Color"])

    # input Pattern
    input_xpath_css = 'css:input[id="pattern"]'
    option_css_xpath = "xpath://ul/li[@data-component-id='pattern']/.."
    click_xpath_css = "xpath://ul/li[@data-component-id='pattern' and normalize-space()='{replace_name}']"
    input_search_click(tab, input_xpath_css, option_css_xpath, click_xpath_css, product_data["Pattern"])

    # 只有在商品类别为手表时才处理手表相关字段
    if product_data["Category"].lower() in ["watches", "watch"]:
        # input Bracelet
        input_xpath_css = 'css:input[id="material_watch_strap"]'
        option_css_xpath = "xpath://ul/li[@data-component-id='material_watch_strap']/.."
        click_xpath_css = "xpath://ul/li[@data-component-id='material_watch_strap' and normalize-space()='{replace_name}']"
        input_search_click(tab, input_xpath_css, option_css_xpath, click_xpath_css, product_data["Bracelet"])

        # input Mechanism
        input_xpath_css = 'css:input[id="watch_mechanism"]'
        option_css_xpath = "xpath://ul/li[@data-component-id='watch_mechanism']/.."
        click_xpath_css = "xpath://ul/li[@data-component-id='watch_mechanism' and normalize-space()='{replace_name}']"
        input_search_click(tab, input_xpath_css, option_css_xpath, click_xpath_css, product_data["Mechanism"])

    tab.wait(1)

    # input Size
    if product_data["Size - standard"] and tab.ele("xpath://label[text()='Standard']/following-sibling::*", timeout=1):
        if tab.ele("xpath://label[text()='Standard']/following-sibling::*", timeout=1).select.by_text(product_data["Size - standard"]):
            logger.debug(f'Choose the Measurements: {product_data["Size - standard"]}')
            tab.ele("xpath://label[text()='Standard']/following-sibling::*/../following-sibling::*/select", timeout=1).select.by_text(_format_num(product_data["Size - value"]))
            # prompt1 = ''
            # prompt2 = ''
            # smart.smart_click(tab, mode='select', options_css_xpath='css:select[data-component-id="size_unit"]', click_rule='', org_name=product_data["Size - standard"], prompt1=prompt1, prompt2=prompt2)

    # Click Continue
    logger.debug('Click continue button')
    tab.ele('xpath://button[text()="Continue" and not(@disabled)]').click()

    tab.wait(1)
    tab.wait.ele_displayed('xpath://input[@id="newPic0"]', timeout=5)
    tab.wait(1)
    return


def submit_step2_photos(tab, product_data):
    """上传商品照片"""
    logger.info('进入第2步：照片上传')
    
    try:
        # 等待照片上传区域加载
        upload_area_selectors = [
            'css:div.PhotoBulkUpload_photoArea__ro4bq',
            'css:div[class*="PhotoBulkUpload_photoArea"]',
            'xpath://div[contains(@class, "PhotoBulkUpload_photoArea")]'
        ]
        
        upload_area = None
        for selector in upload_area_selectors:
            try:
                if area := tab.wait.ele_displayed(selector, timeout=10):
                    upload_area = area
                    logger.debug(f'找到照片上传区域：{selector}')
                    break
            except Exception as e:
                logger.debug(f'尝试选择器 {selector} 失败: {e}')
                continue
                
        if not upload_area:
            raise Exception("未找到照片上传区域")
            
        # 获取照片文件列表
        file_list = pics.save_all_pics(product_data)
        if not file_list:
            raise Exception("未能获取到有效的照片文件")
            
        logger.debug(f'准备上传 {len(file_list)} 张照片')
        
        # 查找上传按钮
        upload_button_selectors = [
            'xpath://button[contains(@class, "FileUploader_field-file-fake")]',
            'css:label[for="file_upload"]',
            'xpath://button[contains(text(), "Add photos")]'
        ]
        
        upload_button = None
        for selector in upload_button_selectors:
            try:
                if button := tab.wait.ele_displayed(selector, timeout=5):
                    upload_button = button
                    logger.debug(f'找到上传按钮：{selector}')
                    break
            except Exception as e:
                logger.debug(f'尝试选择器 {selector} 失败: {e}')
                continue
                
        if not upload_button:
            raise Exception("未找到照片上传按钮")
            
        # 执行上传
        try:
            upload_button.click.to_upload(file_list)
            logger.info(f'开始上传 {len(file_list)} 张照片')
            
            # 等待上传完成
            loading_indicators = [
                'css:img[alt="upload in progress"]',
                'css:[class*="loading"]',
                'css:[class*="spinner"]'
            ]
            
            # 等待所有加载指示器消失
            for indicator in loading_indicators:
                try:
                    tab.wait.ele_deleted(indicator, timeout=180)
                except Exception as e:
                    logger.debug(f'等待加载指示器 {indicator} 消失超时: {e}')
            
            # 验证上传是否成功
            tab.wait(2)  # 等待页面状态更新
            
            # 检查是否有错误提示
            error_selectors = [
                'css:[class*="error"]',
                'css:[class*="alert"]',
                'xpath://div[contains(text(), "error")]'
            ]
            
            for selector in error_selectors:
                if error_ele := tab.ele(selector, timeout=1):
                    error_text = error_ele.text
                    raise Exception(f"上传出现错误：{error_text}")
                    
            # 检查是否达到最小照片数量要求
            photo_count_text = tab.ele('css:.Photo_photoSection__text__juAIc', timeout=5).text
            if "at least 3 photos" in photo_count_text:
                if len(file_list) < 3:
                    raise Exception("需要上传至少3张照片")
                    
            logger.success('照片上传成功')
            
            # 上传成功后截屏
            screenshot_after_upload = f'logs/after_photos_upload_{int(time.time())}.png'
            tab.get_screenshot(screenshot_after_upload)
            logger.debug(f'照片上传完成，截屏: {screenshot_after_upload}')
            
            # 等待一下让页面状态更新
            tab.wait(3)
            
            # 查找并点击继续按钮（多个可能的定位方式）
            continue_button = None
            continue_selectors = [
                'xpath://button[text()="Continue" and not(@disabled)]',
                'xpath://button[contains(text(), "Continue")]',
                'css:button[type="submit"]',
                'xpath://button[@id="vc-preduct-add-submit" and not(@disabled)]',
                'css:button#vc-preduct-add-submit:not([disabled])'
            ]
            
            for selector in continue_selectors:
                try:
                    if btn := tab.ele(selector, timeout=5):
                        # 检查按钮是否可用
                        disabled = btn.attr('disabled')
                        if not disabled:
                            continue_button = btn
                            logger.debug(f'找到继续按钮：{selector}')
                            break
                        else:
                            logger.debug(f'找到继续按钮但已禁用：{selector}')
                except Exception as e:
                    logger.debug(f'尝试选择器 {selector} 失败: {e}')
                    continue
            
            if not continue_button:
                # 截屏并记录当前页面状态
                screenshot_no_continue = f'logs/no_continue_button_{int(time.time())}.png'
                tab.get_screenshot(screenshot_no_continue)
                logger.error(f'未找到可点击的继续按钮，截屏: {screenshot_no_continue}')
                
                # 尝试查找所有按钮元素用于调试
                all_buttons = tab.eles('css:button')
                logger.debug(f'页面上找到 {len(all_buttons)} 个按钮元素')
                for i, btn in enumerate(all_buttons[:10]):  # 只显示前10个
                    try:
                        btn_text = btn.text[:50] if btn.text else '无文本'
                        btn_id = btn.attr('id') or '无ID'
                        btn_disabled = btn.attr('disabled')
                        logger.debug(f'按钮 {i+1}: 文本="{btn_text}", ID="{btn_id}", 禁用={btn_disabled}')
                    except:
                        pass
                
                raise Exception("未找到可点击的继续按钮")
            
            # 点击继续按钮
            logger.info('点击继续按钮进入下一步')
            screenshot_before_click = f'logs/before_click_continue_{int(time.time())}.png'
            tab.get_screenshot(screenshot_before_click)
            
            try:
                continue_button.click()
            except Exception as e:
                logger.warning(f'直接点击失败，尝试JavaScript点击: {e}')
                tab.run_js('arguments[0].click()', continue_button)
            
            # 等待下一步页面加载 - 使用多个可能的标识符
            logger.info('等待下一步页面加载...')
            tab.wait(2)
            
            next_page_indicators = [
                'css:textarea.TextArea_textarea__WRrcw',  # 描述文本框（第3步）
                'css:input[name="serial_number"]',  # 序列号输入框
                'css:label[text()="Description"]',  # 描述标签
                'xpath://label[contains(text(), "Description")]',
                'css:textarea[placeholder*="Add item details"]',
                'css:textarea[placeholder*="details"]'
            ]
            
            page_loaded = False
            for indicator in next_page_indicators:
                try:
                    if tab.wait.ele_displayed(indicator, timeout=15):
                        logger.success(f'下一步页面已加载，标识符: {indicator}')
                        page_loaded = True
                        break
                except Exception as e:
                    logger.debug(f'等待标识符 {indicator} 超时: {e}')
                    continue
            
            # 截屏确认页面状态
            screenshot_after_continue = f'logs/after_click_continue_{int(time.time())}.png'
            tab.get_screenshot(screenshot_after_continue)
            logger.debug(f'点击继续后截屏: {screenshot_after_continue}')
            
            if not page_loaded:
                logger.warning('未检测到下一步页面加载，但继续执行')
            
            return True
            
        except Exception as e:
            logger.error(f'照片上传过程中出错：{e}')
            # 尝试重新上传
            raise Exception(f"照片上传失败：{e}")
            
    except Exception as e:
        logger.error(f'照片上传步骤失败：{e}')
        return False


def _format_num(value):
    """格式化数字，处理各种输入格式"""
    if not value:  # 处理空值
        return ''
        
    # 如果是字符串，移除单位部分
    if isinstance(value, str):
        # 提取数字部分
        import re
        matches = re.findall(r'([\d.]+)', value)
        if not matches:
            return value
        value = matches[0]
    
    try:
        num = float(value)
        # 如果是整数，返回整数格式
        if num.is_integer():
            return str(int(num))
        # 否则返回浮点数格式，去掉末尾的0
        return str(num).rstrip('0').rstrip('.')
    except (ValueError, TypeError):
        return str(value)


def submit_step3_description(tab, product_data):
    """填写描述信息"""
    logger.info('进入第3步：描述信息')
    
    try:
        # 等待页面加载完成
        tab.wait.ele_displayed('css:textarea.TextArea_textarea__WRrcw', timeout=10)
        
        # 定位描述文本框 - 使用更精确的选择器
        description_selectors = [
            'css:textarea.TextArea_textarea__WRrcw',  # 主选择器，与当前页面匹配
            'css:textarea[placeholder="Add item details..."]',  # 使用placeholder定位
            'css:textarea[data-testid="description-textarea"]',  # 可能的测试ID
            'xpath://textarea[@class="TextArea_textarea__WRrcw"]',  # 完全匹配类名
            'xpath://label[text()="Description"]/following-sibling::div//textarea'  # 通过标签文本定位
        ]
        
        description_ele = None
        for selector in description_selectors:
            try:
                if ele := tab.ele(selector, timeout=3):
                    description_ele = ele
                    logger.debug(f'找到描述文本框：{selector}')
                    break
            except Exception as e:
                logger.debug(f'尝试选择器 {selector} 失败: {e}')
                continue
                
        if not description_ele:
            raise Exception("未找到描述文本框")
            
        # 确保元素可见和可交互
        tab.run_js('arguments[0].scrollIntoView({behavior: "smooth", block: "center"})', description_ele)
        tab.wait(1)
        
        # 清除现有内容
        description_ele.clear()
        tab.wait(0.5)
        
        # 输入描述文本
        description = product_data.get("Description", "").strip()
        if not description:
            description = "Beautiful item in excellent condition."
            
        # 使用 JavaScript 设置值，确保触发必要的事件
        tab.run_js('''
            const element = arguments[0];
            const value = arguments[1];
            
            // 设置值
            element.value = value;
            
            // 触发必要的事件
            element.dispatchEvent(new Event('input', { bubbles: true }));
            element.dispatchEvent(new Event('change', { bubbles: true }));
            element.dispatchEvent(new Event('blur', { bubbles: true }));
        ''', description_ele, description)
        
        # 验证输入
        actual_value = description_ele.attr('value')
        if actual_value != description:
            logger.warning(f'描述文本验证失败，期望值：{description}，实际值：{actual_value}')
            # 尝试直接输入作为备选方案
            description_ele.input(description)
            
        # 点击继续按钮
        continue_button = tab.ele('xpath://button[text()="Continue" and not(@disabled)]')
        if not continue_button:
            raise Exception("未找到可点击的继续按钮")
            
        continue_button.click()
        
        # 等待下一步页面加载
        tab.wait.ele_displayed('css:input[name="selectedAddress"]', timeout=10)
        
        return True
        
    except Exception as e:
        logger.error(f'提交描述信息失败: {e}')
        return False


def submit_step4_address(tab, product_data):
    """选择地址信息"""
    logger.info('进入第4步：选择地址')
    
    try:
        # 等待地址选择页面加载
        tab.wait(2)
        
        # 截屏记录当前状态
        screenshot_before_address = f'logs/before_address_{int(time.time())}.png'
        tab.get_screenshot(screenshot_before_address)
        logger.debug(f'地址选择前截屏: {screenshot_before_address}')
        
        # 尝试多种选择器定位地址选择框
        address_selectors = [
            'css:input[name="selectedAddress"]',
            'css:input[placeholder*="address"]',
            'css:input[aria-label*="address"]',
            'xpath://input[contains(@placeholder, "address") or contains(@aria-label, "address")]',
            'css:select[name="selectedAddress"]',
            'xpath://select[@name="selectedAddress"]'
        ]
        
        address_field = None
        for selector in address_selectors:
            try:
                if field := tab.wait.ele_displayed(selector, timeout=5):
                    address_field = field
                    logger.debug(f'找到地址选择框：{selector}')
                    break
            except Exception as e:
                logger.debug(f'尝试选择器 {selector} 失败: {e}')
                continue
        
        if not address_field:
            # 如果找不到地址输入框，可能地址已经选择好了，直接继续
            logger.warning('未找到地址选择框，可能地址已选择，尝试继续')
            screenshot_no_address = f'logs/no_address_field_{int(time.time())}.png'
            tab.get_screenshot(screenshot_no_address)
            
            # 尝试直接查找继续按钮
            continue_button = tab.ele('xpath://button[text()="Continue" and not(@disabled)]', timeout=5)
            if continue_button:
                logger.info('找到继续按钮，直接继续')
                continue_button.click()
                tab.wait(2)
                return True
        else:
            # 如果有地址选择框，尝试选择第一个地址或使用默认地址
            logger.info('找到地址选择框，尝试选择默认地址')
            
            # 如果是下拉框，选择第一个选项
            if address_field.tag == 'select':
                options = address_field.eles('css:option')
                if options and len(options) > 1:  # 第一个通常是默认的
                    address_field.select.by_index(1)
                    logger.success('已选择地址')
            else:
                # 如果是输入框，可能需要点击选择
                address_field.click()
                tab.wait(1)
                
                # 尝试选择第一个选项
                first_option = tab.ele('css:[role="option"]', timeout=3)
                if first_option:
                    first_option.click()
                    logger.success('已选择地址')
        
        # 查找并点击继续按钮
        continue_button = None
        continue_selectors = [
            'xpath://button[text()="Continue" and not(@disabled)]',
            'xpath://button[contains(text(), "Continue")]',
            'css:button[type="submit"]',
            'xpath://button[@id="vc-preduct-add-submit" and not(@disabled)]'
        ]
        
        for selector in continue_selectors:
            try:
                if btn := tab.ele(selector, timeout=5):
                    disabled = btn.attr('disabled')
                    if not disabled:
                        continue_button = btn
                        logger.debug(f'找到继续按钮：{selector}')
                        break
            except:
                continue
        
        if not continue_button:
            screenshot_no_continue = f'logs/no_continue_address_{int(time.time())}.png'
            tab.get_screenshot(screenshot_no_continue)
            logger.warning(f'未找到继续按钮，截屏: {screenshot_no_continue}')
            # 不抛出异常，可能地址步骤可以跳过
            return True
        
        logger.info('点击继续按钮')
        continue_button.click()
        
        # 等待下一步页面加载
        tab.wait(2)
        
        screenshot_after_address = f'logs/after_address_{int(time.time())}.png'
        tab.get_screenshot(screenshot_after_address)
        logger.debug(f'地址选择后截屏: {screenshot_after_address}')
        
        return True
        
    except Exception as e:
        logger.error(f'地址选择步骤失败: {e}')
        screenshot_error = f'logs/address_error_{int(time.time())}.png'
        tab.get_screenshot(screenshot_error)
        logger.debug(f'错误截屏: {screenshot_error}')
        return False


def submit_step5_price(tab, product_data):
    """
    价格输入步骤
    """
    try:
        logger.info('进入第5步：价格输入')
        
        # 等待价格输入框出现并可交互
        price_selectors = [
            'css:input#priceField.PriceInputs_priceInputs__input__XvBHr',
            'css:input[data-cy="pvpInput"]',
            'css:input#priceField',
            'xpath://input[@id="priceField"]'
        ]
        
        price_field = None
        for selector in price_selectors:
            try:
                if price_field := tab.wait.ele_displayed(selector, timeout=5):
                    logger.debug(f'找到价格输入框：{selector}')
                    break
            except:
                continue
                            
        if not price_field:
            logger.error('未找到价格输入框')
            return False
            
        # 确保价格输入框可见和可交互
        tab.run_js('arguments[0].scrollIntoView({behavior: "smooth", block: "center"})', price_field)
        tab.wait(1)
        
        # 清除现有内容并输入新价格
        price_str = str(int(float(product_data['Price'])))  # 确保价格是整数
        
        for attempt in range(3):
            try:
                # 方法1：直接点击和输入
                try:
                    price_field.click()
                    tab.wait(0.5)
                    price_field.clear()
                    tab.wait(0.5)
                    price_field.input(price_str)
                except Exception as e:
                    logger.debug(f'直接输入失败：{e}')
                    
                    # 方法2：使用JavaScript设置值
                    try:
                        tab.run_js('''
                            arguments[0].value = arguments[1];
                            arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
                            arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
                        ''', price_field, price_str)
                    except Exception as e:
                        logger.debug(f'JavaScript设置失败：{e}')
                        
                        # 方法3：模拟键盘输入
                        price_field.click()
                        tab.keyboard.input(price_str)
                
                # 验证输入
                tab.wait(1)
                current_value = price_field.attr('value')
                if current_value == price_str:
                    logger.success(f'价格输入成功：{price_str}')
                    break
                else:
                    logger.warning(f'价格输入验证失败，当前值：{current_value}，期望值：{price_str}')
                    if attempt < 2:  # 最后一次尝试不等待
                        tab.wait(2)
                
            except Exception as e:
                logger.warning(f'价格输入第{attempt + 1}次尝试失败：{e}')
                if attempt < 2:
                    tab.wait(2)
        
        # 等待价格确认信息出现
        fee_message_selectors = [
            'xpath://span[contains(text(), "The buyer will also pay")]',
            'xpath://span[contains(text(), "service fee")]',
            'css:p.PriceInputs_price__buyerFee__'
        ]
        
        fee_message_found = False
        for selector in fee_message_selectors:
            try:
                if tab.wait.ele_displayed(selector, timeout=5):
                    fee_message_found = True
                    break
            except:
                continue
                
        if not fee_message_found:
            logger.warning('未检测到价格确认信息')
            # 不要因为确认信息没出现就返回失败，因为有时确认信息可能不会立即显示
        
        # 点击Complete steps按钮
        try:
            complete_button = tab.ele('xpath://button[text()="Complete steps" and not(@disabled)]')
            if complete_button:
                complete_button.click()
                logger.success('点击Complete steps按钮成功')
        except Exception as e:
            logger.warning(f'点击Complete steps按钮失败：{e}')
        
        return True
        
    except Exception as e:
        logger.error(f'价格输入步骤发生错误：{e}')
        return False


def submit_step6_final_submit(tab, product_data):
    """
    最终提交步骤 - 确认并发布产品
    """
    try:
        logger.info('进入第7步：最终提交')
        
        # 等待页面加载
        tab.wait(3)
        
        # 截屏记录当前状态
        screenshot_before_submit = f'logs/before_final_submit_{int(time.time())}.png'
        tab.get_screenshot(screenshot_before_submit)
        logger.debug(f'最终提交前截屏: {screenshot_before_submit}')
        
        # 查找最终提交按钮 - 多种可能的定位方式
        submit_selectors = [
            'xpath://button[contains(text(), "Publish")]',
            'xpath://button[contains(text(), "List item")]',
            'xpath://button[contains(text(), "Submit")]',
            'xpath://button[contains(text(), "Confirm")]',
            'xpath://button[contains(text(), "Complete")]',
            'css:button[type="submit"]',
            'css:button[class*="publish"]',
            'css:button[class*="submit"]',
            'css:button[id*="publish"]',
            'css:button[id*="submit"]',
            'css:button[data-testid*="publish"]',
            'css:button[data-testid*="submit"]',
            'xpath://button[@id="vc-preduct-add-submit" and not(@disabled)]',
            'css:button#vc-preduct-add-submit:not([disabled])'
        ]
        
        submit_button = None
        for selector in submit_selectors:
            try:
                if btn := tab.wait.ele_displayed(selector, timeout=5):
                    # 检查按钮是否可用
                    disabled = btn.attr('disabled')
                    if not disabled:
                        submit_button = btn
                        logger.debug(f'找到最终提交按钮：{selector}')
                        break
                    else:
                        logger.debug(f'找到按钮但已禁用：{selector}')
            except Exception as e:
                logger.debug(f'尝试选择器 {selector} 失败: {e}')
                continue
        
        if not submit_button:
            # 截屏并尝试查找所有可能的按钮
            screenshot_no_button = f'logs/no_final_submit_button_{int(time.time())}.png'
            tab.get_screenshot(screenshot_no_button)
            logger.warning(f'未找到最终提交按钮，截屏: {screenshot_no_button}')
            
            # 尝试查找所有按钮用于调试
            all_buttons = tab.eles('css:button')
            logger.debug(f'页面上找到 {len(all_buttons)} 个按钮元素')
            for i, btn in enumerate(all_buttons[:15]):  # 显示前15个
                try:
                    btn_text = btn.text[:50] if btn.text else '无文本'
                    btn_id = btn.attr('id') or '无ID'
                    btn_class = btn.attr('class') or '无class'
                    btn_disabled = btn.attr('disabled')
                    logger.debug(f'按钮 {i+1}: 文本="{btn_text}", ID="{btn_id}", Class="{btn_class}", 禁用={btn_disabled}')
                except:
                    pass
            
            # 检查是否已经在产品页面（可能已经自动提交）
            if '/items/' in tab.url or '/sell/' not in tab.url:
                logger.success('可能已自动跳转到产品页面，发布可能已成功')
                return True
            
            raise Exception("未找到最终提交按钮")
        
        # 点击最终提交按钮
        logger.info('点击最终提交按钮')
        screenshot_before_click = f'logs/before_click_final_submit_{int(time.time())}.png'
        tab.get_screenshot(screenshot_before_click)
        
        try:
            submit_button.click()
        except Exception as e:
            logger.warning(f'直接点击失败，尝试JavaScript点击: {e}')
            tab.run_js('arguments[0].click()', submit_button)
        
        # 等待提交完成
        logger.info('等待提交完成...')
        tab.wait(5)
        
        # 检查是否成功跳转到产品页面
        final_url = tab.url
        if '/items/' in final_url:
            logger.success('已跳转到产品页面，发布成功！')
            screenshot_success = f'logs/final_submit_success_{int(time.time())}.png'
            tab.get_screenshot(screenshot_success)
            return True
        
        # 检查是否有错误提示
        error_selectors = [
            'css:[class*="error"]',
            'css:[class*="alert"]',
            'xpath://div[contains(@class, "error")]',
            'xpath://div[contains(text(), "error")]'
        ]
        
        for selector in error_selectors:
            if error_ele := tab.ele(selector, timeout=2):
                error_text = error_ele.text[:200] if error_ele.text else '未知错误'
                logger.error(f'检测到错误提示：{error_text}')
                screenshot_error = f'logs/final_submit_error_{int(time.time())}.png'
                tab.get_screenshot(screenshot_error)
                raise Exception(f"提交时出现错误：{error_text}")
        
        # 截屏确认当前状态
        screenshot_after_submit = f'logs/after_final_submit_{int(time.time())}.png'
        tab.get_screenshot(screenshot_after_submit)
        logger.debug(f'最终提交后截屏: {screenshot_after_submit}')
        
        logger.success('最终提交步骤完成')
        return True
        
    except Exception as e:
        logger.error(f'最终提交步骤失败: {e}')
        screenshot_error = f'logs/final_submit_step_error_{int(time.time())}.png'
        tab.get_screenshot(screenshot_error)
        logger.debug(f'错误截屏: {screenshot_error}')
        return False
            

def input_search_click(tab, input_xpath_css, option_css_xpath, click_xpath_css, the_name):
    if not the_name:
        the_name = 'Other'

    if not tab.ele(input_xpath_css, timeout=0):
        logger.warning(f'Can not locate the param {option_css_xpath}')
        tab.wait(1)
        return

    tab.actions.click(input_xpath_css).type(the_name)

    tab.wait(2)

    smart.smart_click(tab, mode='click', options_css_xpath=option_css_xpath, click_rule=click_xpath_css, org_name=the_name)

    tab.wait(1)


def get_chrome_profiles():
    """获取Chrome配置文件列表"""
    profiles = []
    if sys.platform == 'darwin':  # macOS
        profile_path = '/Users/yinxianzhi/Library/Application Support/Google/Chrome'
    elif sys.platform == 'win32':  # Windows
        profile_path = os.path.expandvars(r'%LOCALAPPDATA%\Google\Chrome\User Data')
    else:  # Linux
        profile_path = os.path.expanduser('~/.config/google-chrome')
        
    try:
        # 读取Local State文件获取配置文件信息
        local_state_path = os.path.join(profile_path, 'Local State')
        if os.path.exists(local_state_path):
            import json
            with open(local_state_path, 'r', encoding='utf-8') as f:
                local_state = json.load(f)
                if 'profile' in local_state and 'info_cache' in local_state['profile']:
                    profiles = [(name, info.get('name', name)) 
                              for name, info in local_state['profile']['info_cache'].items()]
    except Exception as e:
        logger.warning(f"读取Chrome配置文件列表失败: {e}")
        
    if not profiles:
        profiles = [('Default', '默认')]
        
    return profiles

def main():
    # 显示配置文件列表并让用户选择
    profiles = get_chrome_profiles()
    print("\nChrome配置文件列表:")
    for i, (profile_dir, profile_name) in enumerate(profiles, 1):
        print(f"{i}. {profile_name} ({profile_dir})")
        
    # 默认选择第5个配置文件（Profile 7 - trivesa.it）
    default_profile_index = 4  # 索引从0开始，所以4代表第5个配置文件
    
    try:
        # 如果存在第3个配置文件，直接使用它
        if default_profile_index < len(profiles):
            selected_profile = profiles[default_profile_index][0]
            print(f"\n自动选择配置文件: {profiles[default_profile_index][1]} ({selected_profile})")
        else:
            # 如果第3个配置文件不存在，则提示用户选择
            while True:
                try:
                    choice = input("\n未找到默认配置文件，请选择要使用的Chrome配置文件 (输入数字): ")
                    profile_index = int(choice) - 1
                    if 0 <= profile_index < len(profiles):
                        selected_profile = profiles[profile_index][0]
                        break
                    else:
                        print("无效的选择，请重试")
                except ValueError:
                    print("请输入有效的数字")
    except Exception as e:
        # 如果出现任何错误，使用第一个配置文件作为后备选项
        selected_profile = profiles[0][0]
        print(f"\n选择配置文件时出错，使用默认配置文件: {profiles[0][1]} ({selected_profile})")
        logger.warning(f"选择配置文件时出错: {e}")

    logger.info(f"选择的Chrome配置文件: {selected_profile}")

    # 检查并关闭已经运行的Chrome实例
    try:
        if sys.platform == 'darwin':  # macOS
            subprocess.run(['pkill', '-f', 'Google Chrome'])
        elif sys.platform == 'win32':  # Windows
            subprocess.run(['taskkill', '/F', '/IM', 'chrome.exe'], capture_output=True)
        elif sys.platform == 'linux':  # Linux
            subprocess.run(['pkill', '-f', 'chrome'])
        logger.info("已关闭现有的Chrome实例")
    except Exception as e:
        logger.warning(f"关闭Chrome实例时出错: {e}")

    # 创建Chrome配置
    co = ChromiumOptions()
    
    # 设置Chrome路径
    if sys.platform == 'darwin':  # macOS
        chrome_path = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
    elif sys.platform == 'win32':  # Windows
        chrome_path = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
    else:  # Linux
        chrome_path = '/usr/bin/google-chrome'
    
    co.set_browser_path(chrome_path)
    
    # 设置用户数据和缓存路径
    if sys.platform == 'darwin':  # macOS
        user_data_path = '/Users/yinxianzhi/Library/Application Support/Google/Chrome'
        cache_path = '/Users/yinxianzhi/Library/Caches/Google/Chrome'
    elif sys.platform == 'win32':  # Windows
        user_data_path = os.path.expandvars(r'%LOCALAPPDATA%\Google\Chrome\User Data')
        cache_path = os.path.expandvars(r'%LOCALAPPDATA%\Google\Chrome\User Data\Default\Cache')
    else:  # Linux
        user_data_path = os.path.expanduser('~/.config/google-chrome')
        cache_path = os.path.expanduser('~/.cache/google-chrome')

    co.set_paths(
        user_data_path=user_data_path,
        cache_path=cache_path
    )

    # 基本设置
    co.set_argument(f'--profile-directory={selected_profile}')  # 使用选择的配置文件
    co.set_argument('--remote-debugging-port=9222')  # 设置调试端口
    co.set_argument('--no-first-run')  # 跳过首次运行设置
    co.set_argument('--no-default-browser-check')  # 跳过默认浏览器检查
    
    # 性能优化
    co.set_argument('--disable-gpu')  # 禁用GPU加速
    co.set_argument('--disable-dev-shm-usage')  # 禁用/dev/shm使用
    co.set_argument('--no-sandbox')  # 禁用沙盒
    co.set_argument('--disable-setuid-sandbox')  # 禁用setuid沙盒
    
    # 稳定性设置
    co.set_argument('--disable-extensions')  # 禁用扩展
    co.set_argument('--disable-popup-blocking')  # 禁用弹窗拦截
    co.set_argument('--disable-notifications')  # 禁用通知
    co.set_argument('--disable-infobars')  # 禁用信息栏
    
    # 网络设置
    co.set_argument('--disable-background-networking')  # 禁用后台网络
    co.set_argument('--disable-background-timer-throttling')  # 禁用后台定时器限制
    co.set_argument('--disable-backgrounding-occluded-windows')  # 禁用后台窗口遮挡
    
    # 其他优化
    co.set_argument('--disable-translate')  # 禁用翻译
    co.set_argument('--disable-sync')  # 禁用同步
    co.set_argument('--disable-default-apps')  # 禁用默认应用
    co.set_argument('--mute-audio')  # 静音
    
    # 使用配置创建浏览器页面
    try:
        logger.info("正在启动Chrome...")
        page = ChromiumPage(co)
        tab = page.get_tab()
        logger.debug("使用Chrome个人资料创建浏览器页面成功")

        # 直接访问Vestiaire网站
        logger.info("访问Vestiaire网站")
        tab.get('https://www.vestiairecollective.com/')
        tab.wait(10)
        
        # 检查是否已登录
        login_indicators = [
            'css:div[class*="user-menu"]',
            'xpath://div[contains(@class, "user-menu")]',
            'css:a[href*="account"]',
            'xpath://a[contains(@href, "account")]',
            'css:button[data-testid="header-login-button"]'
        ]
        
        is_logged_in = False
        for indicator in login_indicators:
            try:
                if tab.ele(indicator, timeout=5):
                    is_logged_in = True
                    logger.success("检测到已登录状态")
                    break
            except:
                continue
        
        if not is_logged_in:
            logger.info("未检测到登录状态，请手动使用Google账号登录")
            input("登录完成后按回车键继续...")
        
        # 测试数据
        data = {
            'Gender': 'Womenswear',  # 更改为实际需要的性别类别
            'Category': 'Bags',       # 更改为实际需要的商品类别
            'Brand': 'Hermes',        # 更改为实际需要的品牌
            'External reference': '800798 HERMES BAG01',
            'Conditions': 'Very good condition',
            'Details - Category': 'Other',
            'Model': 'Other',
            'Material': 'Leather',
            'Color': 'Brown',
            'Pattern': '',
            'Size - standard': 'EU',
            'Size - value': '',
            'Measurements -cm/in': 'cm',
            'Length': '30',
            'Width': '20',
            'Height': '15',
            'Title': 'Hermes leather bag',
            'Description': 'Beautiful Hermes leather bag in very good condition. Perfect for everyday use or special occasions.',
            'Price': 2500,
            'Image 1': 'https://example.com/image1.jpg'  # 替换为实际图片URL
        }
        
        logger.info("开始执行测试功能")
        
        try:
            # 步骤1：前往商品发布页面并选择类别
            logger.info("执行步骤1：前往商品发布页面")
            if not goto_the_position(tab, data['Gender'], data['Category'], data['Brand']):
                raise Exception("无法完成类别选择")
            
            # 步骤2：填写商品详细信息
            logger.info("执行步骤2：填写商品详细信息")
            submit_step1_details(tab, data)
            
            # 步骤3：上传商品图片
            logger.info("执行步骤3：上传商品图片")
            submit_step2_photos(tab, data)
            
            # 步骤4：填写商品描述
            logger.info("执行步骤4：填写商品描述")
            if not submit_step3_description(tab, data):
                raise Exception("填写商品描述失败")
            
            # 步骤5：选择地址
            logger.info("执行步骤5：选择地址")
            if not submit_step4_address(tab, data):
                raise Exception("地址选择失败")
            
            # 步骤6：设置价格
            logger.info("执行步骤6：设置价格")
            if not submit_step5_price(tab, data):
                raise Exception("价格设置失败")
                
            logger.success("所有步骤执行完成")
            
        except Exception as e:
            logger.error(f"测试过程出错: {str(e)}")
            logger.exception("详细错误信息:")
        
    except Exception as e:
        logger.error(f"程序执行出错: {str(e)}")
        logger.exception("详细错误信息:")
    finally:
        # 清理资源
        try:
            input("测试完成，按回车键关闭浏览器...")
            tab.quit()
            logger.info("浏览器已关闭")
        except Exception as e:
            logger.error(f"关闭浏览器时出错: {str(e)}")


def publish_from_data(data):
    """从 JSON 数据发布产品到 VC
    
    Args:
        data (dict): 产品数据字典，包含所有发布所需信息
        
    Returns:
        dict: {'success': bool, 'vc_item_id': str, 'vc_listing_url': str, 'error': str}
    """
    import sys
    from DrissionPage import ChromiumPage
    
    # 导入监控控制模块
    try:
        import monitor_control
    except ImportError:
        # 如果导入失败，创建一个空的监控控制类
        class MonitorControl:
            @staticmethod
            def clear_stuck(): pass
            @staticmethod
            def update_publisher_status(*args, **kwargs): pass
            @staticmethod
            def mark_stuck(*args, **kwargs): pass
            @staticmethod
            def get_retry_request(): return None
            @staticmethod
            def clear_retry_request(): pass
        monitor_control = MonitorControl()
    
    try:
        logger.info("=" * 60)
        logger.info(f"🚀 开始发布产品: {data.get('product_name', 'Unknown')}")
        logger.info("=" * 60)
        
        # 连接到已运行的 Chrome 实例（端口 9222）
        logger.info("连接到已运行的 Chrome (端口 9222)...")
        logger.info("💡 请确保已运行 start_chrome.command 启动脚本")
        
        try:
            # 使用 ChromiumOptions 配置连接到已运行的 Chrome
            from DrissionPage import ChromiumOptions
            co = ChromiumOptions()
            co.set_address('127.0.0.1:9222')  # 设置远程调试地址
            
            # 使用 ChromiumPage 类连接到已运行的 Chrome
            page = ChromiumPage(addr_or_opts=co)
            tab = page.get_tab()
            logger.success("✅ 成功连接到 Chrome")
        except Exception as e:
            logger.error(f"❌ 无法连接到 Chrome: {e}")
            logger.error("请先运行 start_chrome.command 启动 Chrome")
            raise Exception(f"无法连接到 Chrome (端口 9222): {e}")
        
        # 执行发布流程（带卡住检测）
        steps = [
            ("步骤 1: 前往商品发布页面", lambda: goto_the_position(tab, data['Gender'], data['Category'], data['Brand']), "无法完成类别选择"),
            ("步骤 2: 填写商品详细信息", lambda: submit_step1_details(tab, data), None),
            ("步骤 3: 上传商品图片", lambda: submit_step2_photos(tab, data), None),
            ("步骤 4: 填写商品描述", lambda: submit_step3_description(tab, data), "填写商品描述失败"),
            ("步骤 5: 选择地址", lambda: submit_step4_address(tab, data), "地址选择失败"),
            ("步骤 6: 设置价格", lambda: submit_step5_price(tab, data), "价格设置失败"),
            ("步骤 7: 最终提交", lambda: submit_step6_final_submit(tab, data), "最终提交失败"),
        ]
        
        for step_name, step_func, error_msg in steps:
            logger.info(step_name)
            monitor_control.update_publisher_status(step_name, 'running')
            
            # 检查是否有重试请求
            retry_request = monitor_control.get_retry_request()
            if retry_request and retry_request.get('action') == 'retry':
                logger.info(f"收到重试请求，重新执行 {step_name}")
                monitor_control.clear_retry_request()
            
            try:
                result = step_func()
                if result is False or (result is None and error_msg):
                    raise Exception(error_msg or f"{step_name}失败")
                monitor_control.update_publisher_status(step_name, 'completed')
            except Exception as e:
                # 截屏记录错误
                error_screenshot = f'logs/error_{step_name.replace(" ", "_")}_{int(time.time())}.png'
                tab.get_screenshot(error_screenshot)
                monitor_control.mark_stuck(step_name, str(e), error_screenshot)
                monitor_control.update_publisher_status(step_name, 'error', {'error': str(e)})
                raise
        
        # 等待页面跳转或加载完成
        tab.wait(5)
        
        # 获取发布后的 URL（应该跳转到产品页面）
        final_url = tab.url
        
        # 尝试从 URL 中提取 VC item ID
        vc_item_id = ''
        if '/items/' in final_url:
            vc_item_id = final_url.split('/items/')[-1].split('/')[0]
        
        logger.success(f"✅ 产品发布成功!")
        logger.info(f"   VC Item ID: {vc_item_id}")
        logger.info(f"   VC URL: {final_url}")
        
        # 更新状态为完成
        monitor_control.update_publisher_status('completed', 'completed', {
            'vc_item_id': vc_item_id,
            'vc_listing_url': final_url
        })
        monitor_control.clear_stuck()
        
        # 注意：不关闭浏览器，因为是连接到已运行的 Chrome
        # 可以继续处理下一个产品
        logger.debug("保持 Chrome 连接，准备处理下一个产品")
        
        return {
            'success': True,
            'vc_item_id': vc_item_id,
            'vc_listing_url': final_url,
            'error': '',
        }
        
    except Exception as e:
        logger.error(f"❌ 发布失败: {str(e)}")
        logger.exception("详细错误信息:")
        
        # 更新状态为错误
        monitor_control.update_publisher_status('error', 'error', {'error': str(e)})
        
        # 不关闭浏览器，仅记录错误
        # Chrome 保持运行，可以继续处理下一个产品
        
        return {
            'success': False,
            'vc_item_id': '',
            'vc_listing_url': '',
            'error': str(e),
        }


if __name__ == '__main__':
    main()
