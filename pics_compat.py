import asyncio
from image_handler import ImprovedImageHandler
from loguru import logger

def convert_gdrive_link(url):
    """保持旧接口的 Google Drive 链接转换函数"""
    if 'drive.google.com' in url and 'export=view' in url:
        return url.replace('export=view', 'export=download')
    return url

def save_all_pics(product_data):
    """
    兼容性函数，保持与旧的 pics.py 相同的接口
    但内部使用新的 ImprovedImageHandler
    """
    async def _async_save():
        handler = ImprovedImageHandler()
        return await handler.process_product_images(product_data)

    # 在同步函数中运行异步代码
    return asyncio.run(_async_save())

def clear_jpg_files(folder_path):
    """保持旧接口的文件清理函数"""
    try:
        handler = ImprovedImageHandler()
        handler.cache.cleanup_expired_cache(force=True)
        logger.info(f"Cleaned cache files in {folder_path}")
    except Exception as e:
        logger.error(f"Failed to clear files: {e}")

# 导出所有需要的函数
__all__ = ['convert_gdrive_link', 'save_all_pics', 'clear_jpg_files'] 