import json
import time
import os
import glob
import shutil
import subprocess
import signal
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional
from loguru import logger
from DrissionPage import ChromiumOptions, ChromiumPage

DEBUG_PORT = 9223  # 使用不同的端口

@dataclass
class ElementInfo:
    """元素信息记录"""
    selector: str
    tag_name: str
    text: str
    attributes: Dict[str, str]
    is_visible: bool
    timestamp: float
    xpath: str
    css_selector: str

class ElementInspector:
    """网站元素探测器"""
    def __init__(self):
        # 清理可能存在的Chrome进程
        self._cleanup_existing_chrome()
        
        # 配置浏览器选项
        options = ChromiumOptions()
        options.set_paths(local_port=DEBUG_PORT)
        options.set_argument(f'--remote-debugging-port={DEBUG_PORT}')
        options.set_argument('--no-sandbox')
        options.set_argument('--disable-dev-shm-usage')
        options.set_argument('--disable-gpu')
        options.set_argument('--no-first-run')
        options.set_argument('--no-default-browser-check')
        options.set_argument('--disable-popup-blocking')
        options.set_argument('--ignore-certificate-errors')
        options.set_argument('--disable-blink-features=AutomationControlled')
        options.set_argument('--disable-infobars')  # 禁用信息栏
        
        # 准备2captcha扩展
        extension_path = self._prepare_2captcha_extension()
        if extension_path:
            options.set_argument(f'--load-extension={extension_path}')
        
        # 启动Chrome浏览器
        self._start_chrome()
        
        # 等待Chrome启动
        time.sleep(5)
        
        # 初始化浏览器
        self.page = ChromiumPage(addr_or_opts=options)
        
        # 执行额外的反自动化检测
        self._execute_stealth_js()
        
        self.inspection_results = {}
        
    def _find_latest_extension_version(self, extension_dir):
        """查找扩展的最新版本目录"""
        version_dirs = glob.glob(os.path.join(extension_dir, "*.*.*.*"))
        if not version_dirs:
            return None
        return max(version_dirs)
        
    def _prepare_2captcha_extension(self):
        """准备2captcha扩展"""
        try:
            # 查找原始扩展目录
            base_dir = os.path.expanduser("~/Library/Application Support/Google/Chrome/Default/Extensions")
            extension_dir = os.path.join(base_dir, "momgilhldjefkkjcmlaeelbomnnahepi")
            
            if not os.path.exists(extension_dir):
                logger.error("未找到2captcha扩展")
                return None
                
            # 找到最新版本
            version_dir = self._find_latest_extension_version(extension_dir)
            if not version_dir:
                logger.error("未找到有效的扩展版本")
                return None
                
            # 创建临时目录
            temp_dir = f"/tmp/chrome_extensions_{DEBUG_PORT}"
            temp_ext_dir = os.path.join(temp_dir, "2captcha")
            
            # 清理并重新创建临时目录
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            os.makedirs(temp_ext_dir)
            
            # 复制扩展文件
            shutil.copytree(version_dir, temp_ext_dir, dirs_exist_ok=True)
            
            logger.info(f"2captcha扩展已准备就绪: {temp_ext_dir}")
            return temp_ext_dir
            
        except Exception as e:
            logger.error(f"准备2captcha扩展时出错: {e}")
            return None
        
    def _cleanup_existing_chrome(self):
        """清理已存在的Chrome进程"""
        try:
            # 使用pkill清理Chrome进程
            subprocess.run(['pkill', '-f', 'Google Chrome'], check=False)
            time.sleep(2)  # 等待进程完全终止
            
            # 清理临时目录
            for temp_dir in [f"/tmp/chrome_debug_profile_{DEBUG_PORT}", f"/tmp/chrome_extensions_{DEBUG_PORT}"]:
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
                
            logger.info("已清理现有Chrome进程和临时文件")
        except Exception as e:
            logger.warning(f"清理Chrome进程时出错: {e}")
        
    def _start_chrome(self):
        """启动Chrome浏览器"""
        logger.info("启动Chrome浏览器...")
        chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        
        # 确保临时目录存在
        profile_dir = f"/tmp/chrome_debug_profile_{DEBUG_PORT}"
        os.makedirs(profile_dir, exist_ok=True)
        
        cmd = [
            chrome_path,
            f"--remote-debugging-port={DEBUG_PORT}",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-gpu",
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-popup-blocking",
            "--ignore-certificate-errors",
            "--disable-blink-features=AutomationControlled",
            "--disable-infobars",
            "--disable-notifications",  # 禁用通知
            "--disable-password-manager",  # 禁用密码管理器
            f"--user-data-dir={profile_dir}"
        ]
        
        try:
            self.chrome_process = subprocess.Popen(cmd)
            logger.info("Chrome浏览器启动成功")
            time.sleep(3)  # 等待浏览器完全启动
        except Exception as e:
            logger.error(f"Chrome浏览器启动失败: {e}")
            raise
        
    def goto_upload_page(self):
        """导航到上传页面"""
        logger.debug('导航到商品上传页面')
        
        try:
            # 监听页面加载
            self.page.listen.start('https://collector.vestiairecollective.com/com.snowplowanalytics.snowplow/tp2')
            self.page.get('https://www.vestiairecollective.com/sell-clothes-online/')
            
            # 等待页面加载完成
            self.page.listen.wait()
            logger.debug('分类页面已加载')
            
            # 处理隐私按钮
            try:
                if self.page.ele('button#popin_tc_privacy_button_2', timeout=10):
                    logger.debug('点击隐私按钮')
                    self.page.ele('button#popin_tc_privacy_button_2').click()
            except:
                pass
                
            # 等待搜索输入框显示
            self.page.wait.ele_displayed("css:input[data-role='search']", timeout=15)
            time.sleep(1)
            
            return True
            
        except Exception as e:
            logger.error(f"导航到上传页面失败: {e}")
            return False
            
    def configure_2captcha(self):
        """配置2captcha扩展"""
        logger.info("正在配置2captcha扩展...")
        try:
            # 访问Vestiaire Collective
            self.page.get('https://www.vestiairecollective.com/')
            time.sleep(6)
            
            # 处理Cookie接受按钮
            if self.page.ele('css:button[title="Accept"]', timeout=0):
                logger.debug("接受Cookies")
                self.page.ele('css:button[title="Accept"]', timeout=0).click()
                time.sleep(2)
            
            # 点击登录按钮
            self.page.ele('css:button[id="user-login"]', timeout=30).click()
            
            # 等待登录表单加载
            self.page.wait.eles_loaded('css:input[id="welcomeEmail"]', timeout=30)
            logger.debug("输入用户名和密码")
            
            time.sleep(2)
            
            # 输入用户名
            self.page.ele('css:input[id="welcomeEmail"]').input('info@trivesa.it')
            time.sleep(1)
            
            # 点击继续按钮
            self.page.ele('css:button[data-testid="welcome_continue_btn"]').click()
            time.sleep(2)
            
            # 处理可能出现的通知请求弹窗
            self._handle_notification_prompt()
            
            # 输入密码
            self.page.ele('css:input[id="loginPassword"]').input('Florijnlaan@17')
            time.sleep(1)
            
            # 点击登录按钮
            logger.debug("点击登录按钮")
            self.page.ele('css:button[data-testid="login_submit_connect_btn"]').click()
            time.sleep(1)
            
            # 处理密码保存提示
            self._handle_password_save_prompt()
            
            # 等待登录完成
            logger.debug("等待登录完成")
            self.page.wait.eles_loaded('css:button[aria-labelledby="user-access-item-icon-title-profile"]', timeout=30)
            time.sleep(1)
            
            # 验证登录状态
            if 'info@trivesa.it' in self.page.html:
                logger.success("登录成功")
                
                # 导航到上传页面
                if self.goto_upload_page():
                    logger.success("成功导航到上传页面")
                    return True
                    
                logger.error("导航到上传页面失败")
                return False
                
            logger.error("登录失败")
            return False
            
        except Exception as e:
            logger.error(f"2captcha配置失败: {e}")
            return False
            
    def _handle_notification_prompt(self):
        """处理通知请求弹窗"""
        try:
            # 使用JavaScript处理通知请求
            notification_js = """
            // 阻止通知请求
            window.Notification = undefined;
            
            // 点击Block按钮
            const blockButton = document.querySelector('button.Block, button[data-testid="notification-block-button"]');
            if (blockButton) {
                blockButton.click();
            }
            
            // 处理通知权限
            if (window.Notification && window.Notification.permission !== 'denied') {
                window.Notification.requestPermission = function() {
                    return Promise.resolve('denied');
                };
            }
            """
            self.page.run_js(notification_js)
            logger.debug("已处理通知请求弹窗")
            
            # 等待弹窗消失
            time.sleep(1)
        except Exception as e:
            logger.warning(f"处理通知请求弹窗时出错: {e}")
            
    def _handle_password_save_prompt(self):
        """处理密码保存提示"""
        try:
            # 使用JavaScript处理密码保存提示
            password_js = """
            // 点击Never按钮
            function clickNeverButton() {
                // 查找所有可能的Never按钮
                const neverButtons = [
                    document.querySelector('button.Never'),
                    document.evaluate(
                        "//button[contains(text(), 'Never')]",
                        document,
                        null,
                        XPathResult.FIRST_ORDERED_NODE_TYPE,
                        null
                    ).singleNodeValue,
                    document.querySelector('button[data-testid="password-save-never-button"]')
                ];
                
                // 点击找到的第一个按钮
                for (const button of neverButtons) {
                    if (button) {
                        button.click();
                        return true;
                    }
                }
                return false;
            }
            
            // 尝试点击Never按钮
            if (!clickNeverButton()) {
                // 如果没有找到Never按钮，尝试移除整个密码保存对话框
                const dialog = document.querySelector('div[role="dialog"]');
                if (dialog && dialog.textContent.includes('Save password')) {
                    dialog.remove();
                }
            }
            """
            self.page.run_js(password_js)
            logger.debug("已处理密码保存提示")
            
            # 等待弹窗消失
            time.sleep(1)
        except Exception as e:
            logger.warning(f"处理密码保存提示时出错: {e}")
            
    def _get_element_info(self, element) -> Optional[ElementInfo]:
        """获取元素详细信息"""
        try:
            attrs = {}
            for attr in element.attrs:
                try:
                    attrs[attr] = element.attr(attr)
                except:
                    continue
                    
            return ElementInfo(
                selector=element.css_path,
                tag_name=element.tag,
                text=element.text,
                attributes=attrs,
                is_visible=element.is_displayed(),
                timestamp=time.time(),
                xpath=element.xpath_path,
                css_selector=element.css_path
            )
        except Exception as e:
            logger.error(f"获取元素信息失败: {e}")
            return None

    def inspect_current_page(self, step_name: str):
        """检查当前页面的所有可交互元素"""
        logger.info(f"开始检查步骤: {step_name}")
        
        # 等待页面加载
        time.sleep(2)
        
        # 获取所有可交互元素
        selectors = [
            "button", "input", "select", "a", "textarea",
            "[role='button']", "[role='link']", "[role='textbox']",
            "[tabindex]", "[clickable]", "[class*='btn']",
            "[class*='button']", "[class*='link']"
        ]
        
        elements = []
        for selector in selectors:
            try:
                elements.extend(self.page.eles(selector))
            except:
                continue
                
        # 记录元素信息
        step_results = []
        for element in elements:
            info = self._get_element_info(element)
            if info:
                step_results.append(asdict(info))
                
        self.inspection_results[step_name] = step_results
        logger.info(f"步骤 {step_name} 检查完成")

    def save_inspection_results(self, filename: str = "element_inspection.json"):
        """保存检查结果到文件"""
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(self.inspection_results, f, ensure_ascii=False, indent=2)
        logger.info(f"检查结果已保存到 {filename}")

    def analyze_changes(self) -> Dict[str, List[Dict]]:
        """分析元素变化"""
        changes = {}
        for step, elements in self.inspection_results.items():
            step_changes = []
            for element in elements:
                # 分析元素状态变化
                step_changes.append({
                    "selector": element["selector"],
                    "visible": element["is_visible"],
                    "text": element["text"],
                    "timestamp": element["timestamp"]
                })
            changes[step] = step_changes
        return changes

    def find_stable_selectors(self) -> List[str]:
        """找出最稳定的选择器"""
        selector_frequency = {}
        for step in self.inspection_results.values():
            for element in step:
                selector = element["selector"]
                selector_frequency[selector] = selector_frequency.get(selector, 0) + 1
                
        # 返回出现频率最高的选择器
        return sorted(selector_frequency.items(), key=lambda x: x[1], reverse=True)
        
    def cleanup(self):
        """清理资源"""
        try:
            # 关闭浏览器
            if hasattr(self, 'page'):
                self.page.quit()
            
            # 终止Chrome进程
            if hasattr(self, 'chrome_process'):
                # 发送SIGTERM信号
                self.chrome_process.terminate()
                try:
                    self.chrome_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    # 如果进程没有及时终止，发送SIGKILL信号
                    self.chrome_process.kill()
                    self.chrome_process.wait()
            
            # 清理临时文件
            for temp_dir in [f"/tmp/chrome_debug_profile_{DEBUG_PORT}", f"/tmp/chrome_extensions_{DEBUG_PORT}"]:
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
                
            logger.info("清理完成")
        except Exception as e:
            logger.error(f"清理资源时出错: {e}")

    def _execute_stealth_js(self):
        """执行反自动化检测的JavaScript代码"""
        stealth_js = """
        // 覆盖webdriver标志
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
        
        // 移除自动化相关特征
        if (window.navigator.chrome) {
            window.navigator.chrome = undefined;
        }
        
        // 移除自动化提示
        const banner = document.querySelector('div[role="banner"]');
        if (banner) {
            banner.remove();
        }
        """
        try:
            self.page.run_js(stealth_js)
            logger.info("已执行反自动化检测代码")
        except Exception as e:
            logger.warning(f"执行反自动化检测代码时出错: {e}")

def run_inspection():
    """运行网站元素分析"""
    inspector = None
    try:
        inspector = ElementInspector()
        
        # 配置2captcha
        if not inspector.configure_2captcha():
            logger.error("2captcha配置失败，终止分析")
            return
            
        # 访问登录页面
        logger.info("访问Vestiaire Collective登录页面...")
        inspector.page.get("https://www.vestiairecollective.com/login/")
        
        # 检查登录表单
        for i in range(5):
            inspector.inspect_current_page(f"login_form_{time.time()}")
            time.sleep(0.5)
            
        # 检查上传页面
        inspector.page.get("https://www.vestiairecollective.com/sell/")
        inspector.inspect_current_page("upload_page")
        
        # 检查上传表单
        for i in range(5):
            inspector.inspect_current_page(f"upload_form_{time.time()}")
            time.sleep(0.5)
            
        # 保存结果
        inspector.save_inspection_results()
        
        # 分析变化
        changes = inspector.analyze_changes()
        stable_selectors = inspector.find_stable_selectors()
        
        logger.success("网站元素分析完成")
        
    except Exception as e:
        logger.error(f"分析过程出错: {e}")
        raise
    finally:
        if inspector:
            inspector.cleanup()

if __name__ == "__main__":
    run_inspection() 