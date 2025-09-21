import asyncio
from loguru import logger
from DrissionPage import ChromiumPage
import vestiaire

async def test_upload():
    # 测试数据
    test_data = {
        'Gender': 'Womenswear',
        'Category': 'Handbags',
        'Brand': 'Hermès',
        'External reference': '802480 HERMÈ WB04SH',
        'Conditions': 'Never worn, with tag',
        'Details - Category': 'Handbags',
        'Model': 'Other',
        'Material': 'Canvas and Leather',
        'Color': 'Multicolour',
        'Pattern': 'Solid',
        'Size - standard': 'International',
        'Size - value': 'Medium',
        'Measurements -cm/in': 'cm',
        'Length': '',
        'Width': '',
        'Height': '',
        'Title': 'Test Handbag',
        'Description': 'Test upload with new image handler',
        'Price': 1000,
        'Image 1': 'https://drive.google.com/uc?export=view&id=1Op0PBEyN0qVUJQjju8c69V0uL99sQXM7',
        'Image 2': 'https://drive.google.com/uc?export=view&id=1p_0dLIEWYVboJRyOZ125PhgAemU8kNo0',
        'Image 3': 'https://drive.google.com/uc?export=view&id=1GNmB1ujKb2U5P79PkhDsu7lhCbp71ffJ'
    }

    # 初始化浏览器
    logger.info("Initializing browser...")
    page = ChromiumPage()
    tab = page.get_tab()

    try:
        # 1. 登录（使用测试账号）
        logger.info("Testing login...")
        vestiaire.login(tab, "test_user", "test_password")

        # 2. 导航到上传页面
        logger.info("Navigating to upload page...")
        vestiaire.goto_the_position(tab, test_data['Gender'], test_data['Category'], test_data['Brand'])

        # 3. 填写基本信息
        logger.info("Filling basic information...")
        vestiaire.submit_step1_details(tab, test_data)

        # 4. 上传图片（使用新的图片处理器）
        logger.info("Uploading images...")
        await vestiaire.submit_step2_photos(tab, test_data)

        # 5. 填写描述
        logger.info("Adding description...")
        vestiaire.submit_step3_description(tab, test_data)

        # 6. 设置地址
        logger.info("Setting address...")
        vestiaire.submit_step4_address(tab, test_data)

        # 7. 设置价格
        logger.info("Setting price...")
        vestiaire.submit_step5_price(tab, test_data)

        logger.success("Test completed successfully!")

    except Exception as e:
        logger.error(f"Test failed: {e}")
        raise
    finally:
        # 清理
        tab.wait(2)
        tab.close()

if __name__ == "__main__":
    # 设置日志级别
    logger.remove()
    logger.add(lambda msg: print(msg), level="INFO")
    
    # 运行测试
    logger.info("Starting upload test...")
    asyncio.run(test_upload()) 