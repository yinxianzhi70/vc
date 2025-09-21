import asyncio
import os
import time
from loguru import logger
from image_handler import ImprovedImageHandler
from pics_compat import convert_gdrive_link

async def test_image_processing():
    # 测试数据
    test_data = {
        'Image 1': 'https://drive.google.com/uc?export=view&id=1Op0PBEyN0qVUJQjju8c69V0uL99sQXM7',
        'Image 2': 'https://drive.google.com/uc?export=view&id=1p_0dLIEWYVboJRyOZ125PhgAemU8kNo0',
        'Image 3': 'https://drive.google.com/uc?export=view&id=1GNmB1ujKb2U5P79PkhDsu7lhCbp71ffJ'
    }

    handler = ImprovedImageHandler()

    # 1. 测试链接转换
    logger.info("Testing link conversion...")
    for key, url in test_data.items():
        converted_url = convert_gdrive_link(url)
        logger.info(f"{key}: {url} -> {converted_url}")

    # 2. 测试图片下载和处理
    logger.info("\nTesting image download and processing...")
    processed_files = await handler.process_product_images(test_data)
    
    # 3. 验证结果
    logger.info(f"\nProcessed {len(processed_files)} files:")
    for file_path in processed_files:
        file_size = os.path.getsize(file_path)
        logger.info(f"File: {file_path}, Size: {file_size/1024:.2f}KB")

    # 4. 测试缓存
    logger.info("\nTesting cache mechanism...")
    cached_files = await handler.process_product_images(test_data)
    logger.info(f"Files from cache: {len(cached_files)}")

    # 5. 测试缓存清理
    logger.info("\nTesting cache cleanup...")
    # 强制清理所有缓存
    handler.cache.cleanup_expired_cache(force=True)
    
    # 验证缓存已被清理
    cache_dir = handler.cache.cache_dir
    remaining_files = [f for f in os.listdir(cache_dir) if f.endswith('.jpg')]
    logger.info(f"Remaining files in cache: {len(remaining_files)}")

    # 6. 重新下载验证
    logger.info("\nTesting re-download after cache cleanup...")
    new_files = await handler.process_product_images(test_data)
    logger.info(f"Re-downloaded files: {len(new_files)}")

    return processed_files

if __name__ == "__main__":
    # 设置日志级别
    logger.remove()
    logger.add(lambda msg: print(msg), level="INFO")
    
    # 运行测试
    logger.info("Starting image handler test...")
    result = asyncio.run(test_image_processing())
    logger.info("Test completed.") 