import table
import vestiaire
import traceback
import os
import json
from dotenv import load_dotenv
import socket

from plugin import init_chrome
from datetime import datetime
from loguru import logger

from DrissionPage import ChromiumPage, ChromiumOptions
import sys
import subprocess
import random
import time

# 加载环境变量
load_dotenv()

# 添加日志文件配置
log_file = f'logs/vestiaire_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
os.makedirs('logs', exist_ok=True)
logger.add(log_file, rotation="500 MB", level="DEBUG")

# 从环境变量获取凭据
user = os.getenv('VESTIAIRE_USER')
password = os.getenv('VESTIAIRE_PASSWORD')

if not user or not password:
    logger.error('请在.env文件中设置VESTIAIRE_USER和VESTIAIRE_PASSWORD')
    exit(1)

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

def is_port_in_use(port):
    """检查端口是否被占用"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('127.0.0.1', port))
            return False
        except socket.error:
            return True

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    excel_file = 'Vestiaire Collective Product Information.xlsx'
    launch_date = datetime.now().strftime('%Y-%m-%d %H_%M_%S')  # use current time as the launch date for Excel name

    # 显示Chrome配置文件列表
    profiles = get_chrome_profiles()
    print("\nChrome配置文件列表:")
    for i, (profile_dir, profile_name) in enumerate(profiles, 1):
        print(f"{i}. {profile_name} ({profile_dir})")
        
    # 优先选择trivesa.it配置文件
    selected_profile = None
    
    try:
        # 首先查找trivesa.it配置文件
        for i, (profile_dir, profile_name) in enumerate(profiles):
            if 'trivesa.it' in profile_name.lower() or 'profile 7' in profile_dir.lower():
                selected_profile = profile_dir
                print(f"\n自动选择配置文件: {profile_name} ({profile_dir}) - 用于Vestiaire Collective登录")
                break
        
        # 如果没有找到trivesa.it配置文件，则使用默认的第3个配置文件
        if selected_profile is None:
            default_profile_index = 2  # 索引从0开始，所以2代表第3个配置文件
            if default_profile_index < len(profiles):
                selected_profile = profiles[default_profile_index][0]
                print(f"\n未找到trivesa.it配置文件，使用默认配置文件: {profiles[default_profile_index][1]} ({selected_profile})")
            else:
                # 如果第3个配置文件也不存在，则提示用户选择
                while True:
                    try:
                        choice = input("\n请选择要使用的Chrome配置文件 (输入数字): ")
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

    # If there are files in the queue folder, the bot will continue from the first file in the queue folder
    # Else the bot will split the excel file into Json files and save them in the queue folder
    try:
        if table.get_queue():
            queue_files = table.get_queue()
            logger.info(f'Init: Queue has not finished yet, bot will go on from queue/{queue_files[0]}')
        else:
            logger.info(f'Init: Queue folder is empty, split the {excel_file} to queue folder')

            excel_data = table.excel_to_list_of_dicts(excel_file)
            os.rename(excel_file, f'{excel_file.split(".")[0]} - {launch_date} - Pushed_To_Queue.xlsx')  # Mark the original Excel file as Pushed_to_queue
            queue_files = table.dicts_to_queue(excel_data)
    except Exception as e:
        logger.critical(f'Failed to load the Excel file: {e}')
        exit(1)

    # 关闭现有的Chrome实例
    try:
        if sys.platform == 'darwin':  # macOS
            subprocess.run(['pkill', '-f', 'Google Chrome'])
        elif sys.platform == 'win32':  # Windows
            subprocess.run(['taskkill', '/F', '/IM', 'chrome.exe'], capture_output=True)
        elif sys.platform == 'linux':  # Linux
            subprocess.run(['pkill', '-f', 'chrome'])
        logger.info("已关闭现有的Chrome实例")
        time.sleep(2)  # 等待进程完全关闭
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
    co.set_argument('--disable-web-security')  # 禁用网页安全限制
    co.set_argument('--allow-running-insecure-content')  # 允许运行不安全内容
    co.set_argument('--ignore-certificate-errors')  # 忽略证书错误
    co.set_argument('--no-sandbox')  # 禁用沙盒
    co.set_argument('--disable-dev-shm-usage')  # 禁用/dev/shm使用
    co.set_argument('--disable-gpu')  # 禁用GPU加速
    co.set_argument('--disable-extensions')  # 禁用扩展
    co.set_argument('--disable-popup-blocking')  # 禁用弹窗拦截
    co.set_argument('--disable-notifications')  # 禁用通知
    co.set_argument('--disable-infobars')  # 禁用信息栏
    co.set_argument('--disable-features=VizDisplayCompositor')  # 禁用某些功能
    co.set_argument('--window-size=1920,1080')  # 设置窗口大小

    logger.info(f"使用Chrome配置文件: {selected_profile}")

    try:
        # 创建浏览器页面
        page = ChromiumPage(co)
        tab = page.get_tab()
        logger.info("Chrome浏览器启动成功")
    except Exception as e:
        logger.error(f"Chrome启动失败: {e}")
        logger.info("尝试使用默认配置启动Chrome...")
        
        # 使用更简单的配置重试
        co_simple = ChromiumOptions()
        co_simple.set_browser_path(chrome_path)
        co_simple.set_argument(f'--profile-directory={selected_profile}')
        co_simple.set_argument('--no-sandbox')
        co_simple.set_argument('--disable-dev-shm-usage')
        
        page = ChromiumPage(co_simple)
        tab = page.get_tab()
        logger.info("使用简化配置启动Chrome成功")

    # 添加随机延迟
    delay = random.uniform(3, 7)
    logger.info(f"等待 {delay:.2f} 秒后访问网站...")
    time.sleep(delay)

    # 设置页面加载超时
    tab.set.timeouts(page_load=30)  # 设置页面加载超时为30秒

    tab.set.blocked_urls('https://apiv2.vestiairecollective.com/deposit/price/recommended/*')  # 禁止该连接，就可以不自动设置建议价格

    try:
        # 直接访问Vestiaire网站
        logger.info("访问Vestiaire网站")
        tab.get('https://www.vestiairecollective.com/')
        tab.wait(10)  # 等待页面加载
        
        # 检查页面是否成功加载
        if not tab.title:
            logger.error("页面加载失败，标题为空")
            raise Exception("页面加载失败")
            
        logger.info(f"页面标题: {tab.title}")
        
        # 执行登录
        logger.info("开始登录流程")
        login_success = vestiaire.login(tab, user, password)
        if not login_success:
            logger.error("登录失败，程序退出")
            raise Exception("登录失败")
        logger.info("登录成功")
        
        # 点击"Sell an item"按钮
        sell_button_selectors = [
            'css:a[href*="sell-an-item"]',
            'css:a[data-testid="header-sell-button"]',
            'xpath://a[contains(text(), "Sell an item")]',
            'xpath://a[contains(@class, "sell")]',
            'css:button[class*="sell"]',
            'css:.HeaderSellButton'
        ]
        
        sell_button = None
        for selector in sell_button_selectors:
            try:
                if sell_button := tab.wait.ele_displayed(selector, timeout=10):
                    logger.debug(f"找到销售按钮: {selector}")
                    # 确保按钮可见和可点击
                    tab.run_js('arguments[0].scrollIntoView({behavior: "smooth", block: "center"})', sell_button)
                    tab.wait(2)
                    break
            except Exception as e:
                logger.debug(f"尝试销售按钮 {selector} 失败: {e}")
                continue
                
        if not sell_button:
            logger.error("未找到'Sell an item'按钮")
            raise Exception("未找到'Sell an item'按钮")
            
        try:
            sell_button.click()
            logger.info("点击'Sell an item'按钮")
            tab.wait(10)  # 等待页面加载
        except Exception as e:
            logger.debug(f"直接点击失败，尝试JavaScript点击: {e}")
            try:
                tab.run_js('arguments[0].click()', sell_button)
                tab.wait(10)
            except Exception as e:
                logger.error(f"点击'Sell an item'按钮失败: {e}")
                raise Exception("无法点击'Sell an item'按钮")
        
        # 处理队列中的商品数据
        for queue_file in queue_files:
            index, row = table.load_json_data(queue_file)
            logger.info(f"处理第 {index} 条数据")
            logger.debug(f"数据内容: {row}")

            reason = ''

            try:
                vestiaire.goto_the_position(tab, type=row['Gender'], cat=row['Category'], brand=row['Brand'])
                tab.wait(3)

                vestiaire.submit_step1_details(tab, row)
                tab.wait(3)

                vestiaire.submit_step2_photos(tab, row)
                tab.wait(3)

                vestiaire.submit_step3_description(tab, row)
                tab.wait(3)

                vestiaire.submit_step4_address(tab)
                tab.wait(3)

                vestiaire.submit_step5_price(tab, row)
                
            except Exception as e:
                traceback.print_exc()
                reason = traceback.format_exc()
                logger.error(f'处理失败: {e}')
            finally:
                table.save_result_to_excel(tab, launch_date, row, index, reason)
                os.remove(f'queue/{queue_file}')
                tab.wait(5)
                logger.info('----------------------------------------')

        logger.success('所有产品处理完成')
            
    except Exception as e:
        logger.error(f"程序执行出错: {str(e)}")
        logger.exception("详细错误信息:")
    finally:
        # 清理资源
        try:
            input("测试完成，按回车键关闭浏览器...")
            page.quit()
            logger.info("浏览器已关闭")
        except Exception as e:
            logger.error(f"关闭浏览器时出错: {str(e)}")
