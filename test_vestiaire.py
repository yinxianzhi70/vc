from DrissionPage import ChromiumPage, ChromiumOptions
from loguru import logger
import sys
import time
import os
from config import TEST_CONFIG

# 配置日志
logger.remove()
logger.add(sys.stderr, level="DEBUG")

def test_address_selection():
    page = None
    tab = None
    
    try:
        # 检查配置
        if not TEST_CONFIG['username'] or not TEST_CONFIG['password']:
            logger.error("请在config.py中填写用户名和密码")
            return
            
        # 配置浏览器选项
        co = ChromiumOptions()
        co.set_argument('--no-sandbox')
        co.set_argument('--disable-gpu')
        co.set_argument('--disable-dev-shm-usage')
        co.set_argument('--remote-debugging-port=0')  # 使用动态端口
        
        # 创建浏览器实例
        logger.info("正在启动浏览器...")
        page = ChromiumPage(co)
        tab = page.get_tab()
        
        # 登录
        logger.info("正在登录...")
        from vestiaire import login
        if not login(tab, TEST_CONFIG['username'], TEST_CONFIG['password']):
            logger.error("登录失败")
            return
            
        logger.success("登录成功")
        
        # 等待页面加载
        logger.info("等待页面加载...")
        time.sleep(5)
        
        # 进入卖家页面
        logger.info("正在进入卖家页面...")
        from vestiaire import goto_the_position
        if not goto_the_position(tab, "Women", "Bags", "Gucci"):
            logger.error("进入卖家页面失败")
            return
            
        logger.success("成功进入卖家页面")
        
        # 填写商品信息
        logger.info("正在填写商品信息...")
        test_product_data = TEST_CONFIG['test_product']
        
        # 执行前三个步骤
        from vestiaire import submit_step1_details, submit_step2_photos, submit_step3_description
        
        logger.info("执行第一步：填写基本信息...")
        submit_step1_details(tab, test_product_data)
        
        logger.info("执行第二步：上传图片...")
        submit_step2_photos(tab, test_product_data)
        
        logger.info("执行第三步：填写描述...")
        submit_step3_description(tab, test_product_data)
        
        # 测试地址选择功能
        logger.info("执行第四步：选择地址...")
        from vestiaire import submit_step4_address
        result = submit_step4_address(tab)
        
        if result:
            logger.success("地址选择测试成功")
        else:
            logger.error("地址选择测试失败")
            
    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}")
        if isinstance(e, str) and 'remote-debugging-port' in e:
            logger.info("尝试终止所有Chrome进程...")
            os.system('pkill -f "Google Chrome"')
    finally:
        try:
            if tab:
                tab.close()
            if page:
                page.close()
        except Exception as e:
            logger.warning(f"关闭浏览器时发生错误: {e}")

if __name__ == '__main__':
    test_address_selection() 