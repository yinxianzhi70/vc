import time
import smart
import pics
import platform
import os
import sys
import subprocess
import re

from loguru import logger
from DrissionPage.common import Keys
from DrissionPage import ChromiumPage, ChromiumOptions, SessionPage, SessionOptions
from dotenv import load_dotenv


def login(tab, username, password, max_retries=3):
    """登录到 Vestiaire Collective"""
    for attempt in range(max_retries):
        try:
            logger.info(f'开始登录流程 (第{attempt + 1}次尝试)')
            tab.get('https://www.vestiairecollective.com/')
            tab.wait(20)  # 增加初始等待时间到20秒
            
            # 记录当前页面URL和状态
            logger.debug(f'当前页面URL: {tab.url}')
            logger.debug(f'页面标题: {tab.title}')
            logger.debug(f'页面就绪状态: {tab.run_js("return document.readyState")}')
            
            # 处理Cookie接受按钮
            cookie_selectors = [
                'css:button[id="onetrust-accept-btn-handler"]',
                'xpath://button[contains(text(), "Accept")]',
                'xpath://button[contains(text(), "Accept all")]',
                'css:button[class*="cookie"]',
                'css:button[class*="accept"]',
                'xpath://button[contains(@class, "cookie")]',
                'xpath://button[contains(@class, "accept")]'
            ]
            
            cookie_clicked = False
            for selector in cookie_selectors:
                try:
                    if cookie_btn := tab.ele(selector, timeout=5):
                        logger.debug(f"找到cookie按钮: {selector}")
                        # 确保按钮可见
                        tab.run_js('arguments[0].scrollIntoView({behavior: "smooth", block: "center"})', cookie_btn)
                        tab.wait(1)
                        
                        # 尝试多种点击方式
                        try:
                            cookie_btn.click()
                            cookie_clicked = True
                            break
                        except Exception as e:
                            logger.debug(f"直接点击失败，尝试JavaScript点击: {e}")
                            try:
                                tab.run_js('arguments[0].click()', cookie_btn)
                                cookie_clicked = True
                                break
                            except Exception as e:
                                logger.debug(f"JavaScript点击失败: {e}")
                                continue
                except Exception as e:
                    logger.debug(f"尝试cookie按钮 {selector} 失败: {e}")
                    continue
                
            if not cookie_clicked:
                logger.warning("未找到或无法点击cookie按钮，继续执行")
            
            # 点击登录按钮
            login_button_selectors = [
                'css:button[id="user-login"]',
                'css:button[data-testid="header-login-button"]',
                'xpath://button[contains(@class, "login")]',
                'xpath://button[contains(text(), "Log in")]',
                'css:button[class*="login"]',
                'xpath://a[contains(@class, "login")]',
                'xpath://a[contains(text(), "Log in")]',
                'css:button[class*="HeaderLoginButton"]'
            ]
            
            login_button = None
            for selector in login_button_selectors:
                try:
                    if login_button := tab.wait.ele_displayed(selector, timeout=20):
                        logger.debug(f"找到登录按钮: {selector}")
                        # 确保按钮可见和可点击
                        tab.run_js('arguments[0].scrollIntoView({behavior: "smooth", block: "center"})', login_button)
                        tab.wait(5)
                        break
                except Exception as e:
                    logger.debug(f"尝试登录按钮 {selector} 失败: {e}")
                    continue
                    
            if not login_button:
                logger.error("未找到登录按钮")
                logger.debug(f"页面内容: {tab.html}")
                if attempt < max_retries - 1:
                    logger.info("等待30秒后重试...")
                    tab.wait(30)
                    continue
                raise Exception("未找到登录按钮")
                
            login_button.click()
            tab.wait(15)  # 增加等待时间到15秒
            
            # 查找并点击Google登录按钮
            google_login_selectors = [
                'css:button[data-testid="google-login"]',
                'xpath://button[contains(@class, "google")]',
                'xpath://button[contains(text(), "Continue with Google")]',
                'xpath://button[contains(., "Google")]',
                'css:button[class*="google"]',
                'xpath://div[contains(@class, "google")]',
                'xpath://div[contains(text(), "Continue with Google")]'
            ]
            
            google_button = None
            for selector in google_login_selectors:
                try:
                    if google_button := tab.wait.ele_displayed(selector, timeout=20):
                        logger.debug(f"找到Google登录按钮: {selector}")
                        # 确保按钮可见和可点击
                        tab.run_js('arguments[0].scrollIntoView({behavior: "smooth", block: "center"})', google_button)
                        tab.wait(5)
                        break
                except Exception as e:
                    logger.debug(f"尝试Google登录按钮 {selector} 失败: {e}")
                    continue
                    
            if google_button:
                google_button.click()
                logger.info("点击Google登录按钮")
                tab.wait(20)  # 等待Google登录流程完成
                
                # 检查是否已登录成功
                success_indicators = [
                    'css:div[class*="user-menu"]',
                    'xpath://div[contains(@class, "user-menu")]',
                    'css:a[href*="account"]',
                    'xpath://a[contains(@href, "account")]',
                    'css:button[data-testid="header-login-button"]'
                ]
                
                login_success = False
                for indicator in success_indicators:
                    try:
                        if tab.wait.ele_displayed(indicator, timeout=30):
                            logger.success("使用Google账号登录成功")
                            login_success = True
                            break
                    except Exception as e:
                        logger.debug(f"检查登录成功指示器 {indicator} 失败: {e}")
                        continue
                        
                if login_success:
                    return True
                    
            # 如果Google登录失败或未找到Google登录按钮，尝试常规登录方式
            logger.warning("Google登录未成功，尝试使用常规登录方式")
            
            # 记录登录表单页面URL
            logger.debug(f'登录表单页面URL: {tab.url}')
            logger.debug(f'登录表单页面HTML: {tab.html}')
            
            # 输入邮箱
            email_selectors = [
                'css:input[id="welcomeEmail"]',
                'css:input[type="email"]',
                'xpath://input[@placeholder="Email"]',
                'css:input[name="email"]',
                'xpath://input[contains(@class, "email")]'
            ]
            
            email_input = None
            for selector in email_selectors:
                try:
                    if email_input := tab.wait.ele_displayed(selector, timeout=20):
                        logger.debug(f"找到邮箱输入框: {selector}")
                        break
                except Exception as e:
                    logger.debug(f"尝试邮箱输入框 {selector} 失败: {e}")
                    continue
                    
            if not email_input:
                logger.error("未找到邮箱输入框")
                logger.debug(f"页面内容: {tab.html}")
                if attempt < max_retries - 1:
                    logger.info("等待30秒后重试...")
                    tab.wait(30)
                    continue
                raise Exception("未找到邮箱输入框")
                
            # 确保邮箱输入框可见和可交互
            tab.run_js('arguments[0].scrollIntoView({behavior: "smooth", block: "center"})', email_input)
            tab.wait(5)
            
            # 清除并输入邮箱
            email_input.clear()
            email_input.input(username)
            logger.debug(f"输入邮箱: {username}")
            
            # 点击继续按钮
            continue_selectors = [
                'css:button[data-testid="welcome_continue_btn"]',
                'xpath://button[contains(text(), "Continue")]',
                'xpath://button[contains(@class, "continue")]',
                'css:button[class*="continue"]',
                'xpath://button[contains(@class, "submit")]'
            ]
            
            continue_button = None
            for selector in continue_selectors:
                try:
                    if continue_button := tab.wait.ele_displayed(selector, timeout=20):
                        logger.debug(f"找到继续按钮: {selector}")
                        break
                except Exception as e:
                    logger.debug(f"尝试继续按钮 {selector} 失败: {e}")
                    continue
                    
            if not continue_button:
                logger.error("未找到继续按钮")
                logger.debug(f"页面内容: {tab.html}")
                if attempt < max_retries - 1:
                    logger.info("等待30秒后重试...")
                    tab.wait(30)
                    continue
                raise Exception("未找到继续按钮")
                
            continue_button.click()
            tab.wait(15)  # 增加等待时间到15秒
            
            # 等待页面加载完成
            try:
                tab.wait.ele_displayed('css:div[role="dialog"]', timeout=25)
                logger.debug("登录对话框已加载")
            except Exception as e:
                logger.warning(f"等待登录对话框超时: {e}")
                logger.debug(f"当前页面内容: {tab.html}")
            
            # 记录密码输入页面URL和状态
            logger.debug(f'密码输入页面URL: {tab.url}')
            logger.debug(f'页面标题: {tab.title}')
            logger.debug(f'页面就绪状态: {tab.run_js("return document.readyState")}')
            
            # 输入密码
            password_selectors = [
                'css:input[id="loginPassword"]',
                'css:input[type="password"]',
                'css:input[name="password"]',
                'xpath://input[@placeholder="Password"]',
                'xpath://input[@type="password"]',
                'css:input[class*="password"]'
            ]
            
            # 记录当前页面内容以便调试
            logger.debug(f"当前页面HTML: {tab.html}")
            
            password_input = None
            for selector in password_selectors:
                try:
                    if password_input := tab.wait.ele_displayed(selector, timeout=20):
                        logger.debug(f"找到密码输入框: {selector}")
                        break
                    else:
                        logger.debug(f"未找到密码输入框: {selector}")
                except Exception as e:
                    logger.debug(f"尝试选择器 {selector} 失败: {e}")
                    continue
                    
            if not password_input:
                # 尝试使用JavaScript定位密码输入框
                try:
                    js_result = tab.run_js('''
                        let input = document.querySelector('input[type="password"]');
                        if (!input) input = document.querySelector('input#loginPassword');
                        if (!input) {
                            input = Array.from(document.querySelectorAll('input')).find(el => 
                                el.placeholder && el.placeholder.toLowerCase().includes('password')
                            );
                        }
                        if (input) {
                            input.style.display = 'block';
                            input.style.visibility = 'visible';
                            input.style.opacity = '1';
                            return true;
                        }
                        return false;
                    ''')
                    if js_result:
                        logger.debug("通过JavaScript找到并显示密码输入框")
                        # 重新尝试获取密码输入框
                        for selector in password_selectors:
                            try:
                                if password_input := tab.wait.ele_displayed(selector, timeout=10):
                                    logger.debug(f"通过JavaScript后找到密码输入框: {selector}")
                                    break
                            except Exception as e:
                                logger.debug(f"JavaScript后尝试选择器 {selector} 失败: {e}")
                                continue
                except Exception as e:
                    logger.debug(f"JavaScript定位密码输入框失败: {e}")
                                
            if not password_input:
                logger.error("未找到密码输入框")
                logger.debug(f"页面内容: {tab.html}")
                if attempt < max_retries - 1:
                    logger.info("等待30秒后重试...")
                    tab.wait(30)
                    continue
                raise Exception("未找到密码输入框")
                
            # 确保密码输入框可见和可交互
            tab.run_js('arguments[0].scrollIntoView({behavior: "smooth", block: "center"})', password_input)
            tab.wait(5)
            
            # 清除并输入密码
            password_input.clear()
            password_input.input(password)
            logger.debug("输入密码完成")
            tab.wait(10)  # 增加等待时间到10秒
            
            # 点击登录按钮
            submit_selectors = [
                'css:button[type="submit"]',
                'xpath://button[contains(text(), "Log in")]',
                'xpath://button[contains(@class, "submit")]',
                'css:button[class*="submit"]',
                'css:button[data-testid="login-submit"]',
                'xpath://button[contains(@class, "login")]',
                'xpath://button[contains(@class, "btn-login")]'
            ]
            
            submit_button = None
            for selector in submit_selectors:
                try:
                    if submit_button := tab.wait.ele_displayed(selector, timeout=30):
                        logger.debug(f"找到提交按钮: {selector}")
                        # 确保按钮可见
                        tab.run_js('arguments[0].scrollIntoView({behavior: "smooth", block: "center"})', submit_button)
                        tab.wait(5)
                        break
                except Exception as e:
                    logger.debug(f"尝试提交按钮 {selector} 失败: {e}")
                    continue
                    
            if not submit_button:
                logger.error("未找到提交按钮")
                logger.debug(f"页面内容: {tab.html}")
                if attempt < max_retries - 1:
                    logger.info("等待30秒后重试...")
                    tab.wait(30)
                    continue
                raise Exception("未找到提交按钮")
                
            # 尝试多种点击方式
            try:
                submit_button.click()
            except Exception as e:
                logger.debug(f"直接点击失败，尝试JavaScript点击: {e}")
                try:
                    tab.run_js('arguments[0].click()', submit_button)
                except Exception as e:
                    logger.debug(f"JavaScript点击失败: {e}")
                    # 尝试模拟回车键
                    tab.keyboard.press(Keys.ENTER)
            
            # 等待登录完成，检查多个可能的成功标志
            success_indicators = [
                'css:div[class*="user-menu"]',
                'xpath://div[contains(@class, "user-menu")]',
                'css:a[href*="account"]',
                'xpath://a[contains(@href, "account")]',
                'css:button[data-testid="header-login-button"]',
                'xpath://button[contains(@class, "login")]'
            ]
            
            login_success = False
            for indicator in success_indicators:
                try:
                    if tab.wait.ele_displayed(indicator, timeout=30):
                        logger.info("登录成功")
                        login_success = True
                        break
                except Exception as e:
                    logger.debug(f"检查登录成功指示器 {indicator} 失败: {e}")
                    continue
            
            if not login_success:
                # 检查是否有错误消息
                error_indicators = [
                    'css:div[class*="error"]',
                    'xpath://div[contains(@class, "error")]',
                    'css:div[class*="alert"]',
                    'xpath://div[contains(@class, "alert")]'
                ]
                
                for indicator in error_indicators:
                    try:
                        if error_ele := tab.ele(indicator, timeout=5):
                            error_text = error_ele.text
                            logger.error(f"登录失败，错误信息: {error_text}")
                            raise Exception(f"登录失败: {error_text}")
                    except Exception as e:
                        continue
                
                # 如果没有找到错误消息，检查页面状态
                logger.debug(f"当前页面URL: {tab.url}")
                logger.debug(f"页面标题: {tab.title}")
                logger.debug(f"页面HTML: {tab.html}")
                
                if attempt < max_retries - 1:
                    logger.info("等待30秒后重试...")
                    tab.wait(30)
                    continue
                raise Exception("登录失败，未检测到成功标志")
            
            return True

        except Exception as e:
            logger.error(f"登录过程中出错: {e}")
            if attempt < max_retries - 1:
                logger.info("等待30秒后重试...")
            tab.wait(30)
            continue
            raise Exception(f"登录失败: {e}")
            
    return False


def goto_the_position(tab, type, cat, brand):
    """Go to the position where the bot can start to collect data"""
    logger.debug(f'Go to the Sell an Item page, and choose the category')

    try:

        tab.listen.start('https://collector.vestiairecollective.com/com.snowplowanalytics.snowplow/tp2')
        tab.get('https://www.vestiairecollective.com/sell-clothes-online/')

        tab.listen.wait()

        logger.debug(f'Category page is loaded')

        try:
            tab.ele('button#popin_tc_privacy_button_2', timeout=10).click()
            logger.debug('Click privacy button')
        except:
            pass

        # Choose the category
        tab.wait.ele_displayed("css:input[data-role='search']", timeout=15)
        tab.wait(1)

        logger.debug(f'Click the Type: {type}')
        tab.ele(f"xpath://span[contains(@class, 'universe-selector_depositForm__form__universeLabel') and text()='{type}']", timeout=30).click()

        tab.wait(1)

        logger.debug(f'Choose the Category: {cat}')
        smart.smart_click(tab, mode='select', options_css_xpath='css:#preductAddCategory', click_rule='', org_name=cat)
        # tab.ele('css:#preductAddCategory').select.by_text(cat)

        tab.wait(1)

        logger.debug(f'Input the brand: {brand}')
        # tab.ele(f"xpath://div[contains(@class, 'brand-search_depositForm_') and text()='{brand}']/..").click(by_js=True)
        # tab.ele(f"xpath://div[contains(@class, 'brand-search_depositForm_') and text()='{brand}']/..").click(by_js=True)
        tab.ele(f'xpath://input[@id="depositForm__form__brands-input"]').input(brand)

        tab.wait(1)
        # options_css_xpath = "xpath://span[contains(@class, 'brand-search_depositForm_')]/../../../.."  # 定位到选项列表
        options_css_xpath = "xpath://*[contains(@class, 'brand-search_depositForm__form__optionsList__item__value')]/../../.."  # 定位到选项列表
        click_rule = "xpath://*[contains(@class, 'brand-search_depositForm__form__optionsList__item__value__') and normalize-space() = '{replace_name}']/.."  # 选项点击规则，{replace_name} 会被替换成最匹配名称
        smart.smart_click(tab, mode='click', options_css_xpath=options_css_xpath, click_rule=click_rule, org_name=brand)

        tab.wait.ele_displayed('xpath://button[@id="vc-preduct-add-submit" and not(@disabled)]', timeout=15)
        tab.wait(1)

        logger.debug('Click continue button')
        tab.ele('xpath://button[@id="vc-preduct-add-submit" and not(@disabled)]').click()

        # Check whether on the product adding page
        tab.wait.ele_displayed("xpath://button[contains(@class, 'FileUploader_field-file-fake__')]", timeout=15)

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
            
            # 点击继续按钮
            continue_button = tab.ele('xpath://button[text()="Continue" and not(@disabled)]')
            if not continue_button:
                raise Exception("未找到可点击的继续按钮")
                
            continue_button.click()
            
            # 等待下一步页面加载
            tab.wait.ele_displayed('css:input[name="serial_number"]', timeout=10)
            
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


async def submit_step4_address(self):
    """提交地址信息"""
    self.logger.info("开始提交地址信息...")
    
    try:
        # 尝试多种选择器定位地址输入框
        selectors = [
            'css:input[id="6868921"]',
            'css:input[placeholder*="地址"]',
            'css:input[aria-label*="address"]',
            'xpath://input[contains(@placeholder, "地址") or contains(@aria-label, "address")]'
        ]
        
        input_element = None
        for selector in selectors:
            try:
                input_element = await self.page.wait_for_selector(selector, timeout=5000)
                if input_element:
                    self.logger.info(f"找到地址输入框，使用选择器: {selector}")
                    break
            except Exception as e:
                self.logger.debug(f"使用选择器 {selector} 未找到元素: {str(e)}")
                continue
                    
        if not input_element:
            raise Exception("无法找到地址输入框")
            
        # 输入地址信息
        await input_element.fill("123 Test Street")
        await self.page.keyboard.press("Enter")
        
        # 等待地址确认
        await self.page.wait_for_selector('css:button[type="submit"]', timeout=10000)
        self.logger.info("地址信息提交成功")
        
    except Exception as e:
        self.logger.error(f"提交地址时出错: {str(e)}")
        await self.save_screenshot("address_error")
        raise


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
        
    # 默认选择第3个配置文件（Profile 2）
    default_profile_index = 2  # 索引从0开始，所以2代表第3个配置文件
    
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


if __name__ == '__main__':
    main()
