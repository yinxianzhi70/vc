import os
import hashlib
import asyncio
import aiohttp
import json
import time
from PIL import Image
from loguru import logger
from functools import lru_cache
from typing import List, Dict, Optional
from datetime import datetime, timedelta

class ImageConfig:
    """图片处理配置"""
    MAX_SIZE = 5_000_000  # 5MB
    MIN_WIDTH = 800
    MIN_HEIGHT = 800
    ALLOWED_FORMATS = ['jpg', 'jpeg', 'png']
    COMPRESSION_QUALITY = 85
    MAX_RETRIES = 3
    TIMEOUT = 30  # seconds
    CHUNK_SIZE = 8192
    CACHE_DIR = "image_cache"
    DOWNLOAD_DIR = "download"
    CACHE_METADATA_FILE = "cache_metadata.json"
    CACHE_EXPIRY_DAYS = 7  # 缓存过期时间（天）
    CACHE_CLEANUP_INTERVAL = 24  # 清理间隔（小时）

class ImageCache:
    """图片缓存管理"""
    def __init__(self, cache_dir: str = ImageConfig.CACHE_DIR):
        self.cache_dir = cache_dir
        self.metadata_file = os.path.join(cache_dir, ImageConfig.CACHE_METADATA_FILE)
        self.metadata = self._load_metadata()
        os.makedirs(cache_dir, exist_ok=True)
        
    def _load_metadata(self) -> Dict:
        """加载缓存元数据"""
        if os.path.exists(self.metadata_file):
            try:
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load cache metadata: {e}")
        return {}
    
    def _save_metadata(self):
        """保存缓存元数据"""
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(self.metadata, f)
        except Exception as e:
            logger.error(f"Failed to save cache metadata: {e}")
    
    def get_cache_key(self, url: str) -> str:
        return hashlib.md5(url.encode()).hexdigest()
    
    @lru_cache(maxsize=100)
    def get_cached_image(self, url: str) -> Optional[str]:
        cache_key = self.get_cache_key(url)
        cache_path = os.path.join(self.cache_dir, f"{cache_key}.jpg")
        
        # 检查文件是否存在且未过期
        if os.path.exists(cache_path):
            metadata = self.metadata.get(cache_key, {})
            created_time = metadata.get('created_time', 0)
            expiry_time = created_time + (ImageConfig.CACHE_EXPIRY_DAYS * 24 * 3600)
            
            if time.time() < expiry_time:
                return cache_path
            else:
                # 文件已过期，删除它
                self.remove_cached_file(cache_key)
                
        return None

    def save_to_cache(self, url: str, file_path: str) -> str:
        cache_key = self.get_cache_key(url)
        cache_path = os.path.join(self.cache_dir, f"{cache_key}.jpg")
        os.replace(file_path, cache_path)
        
        # 更新元数据
        self.metadata[cache_key] = {
            'url': url,
            'created_time': int(time.time()),
            'file_path': cache_path
        }
        self._save_metadata()
        
        return cache_path

    def remove_cached_file(self, cache_key: str):
        """删除缓存文件"""
        try:
            cache_path = os.path.join(self.cache_dir, f"{cache_key}.jpg")
            if os.path.exists(cache_path):
                os.remove(cache_path)
            if cache_key in self.metadata:
                del self.metadata[cache_key]
                self._save_metadata()
        except Exception as e:
            logger.error(f"Failed to remove cached file: {e}")

    def cleanup_expired_cache(self, force: bool = False):
        """清理过期的缓存文件"""
        current_time = time.time()
        cleaned_count = 0
        total_size_freed = 0

        for cache_key, metadata in list(self.metadata.items()):
            created_time = metadata.get('created_time', 0)
            expiry_time = created_time + (ImageConfig.CACHE_EXPIRY_DAYS * 24 * 3600)
            
            if force or current_time > expiry_time:
                file_path = metadata.get('file_path')
                if file_path and os.path.exists(file_path):
                    size = os.path.getsize(file_path)
                    os.remove(file_path)
                    total_size_freed += size
                    cleaned_count += 1
                
                del self.metadata[cache_key]

        if cleaned_count > 0:
            self._save_metadata()
            logger.info(f"Cleaned {cleaned_count} expired cache files, freed {total_size_freed/1024/1024:.2f}MB")

    async def start_cleanup_task(self):
        """启动定期清理任务"""
        while True:
            try:
                self.cleanup_expired_cache()
                await asyncio.sleep(ImageConfig.CACHE_CLEANUP_INTERVAL * 3600)
            except Exception as e:
                logger.error(f"Cache cleanup task error: {e}")
                await asyncio.sleep(3600)  # 出错后等待1小时再试

class UploadProgressTracker:
    """上传进度跟踪"""
    def __init__(self):
        self.total_files = 0
        self.uploaded_files = 0
        self.failed_files = 0
        
    def update_progress(self, success: bool = True):
        if success:
            self.uploaded_files += 1
        else:
            self.failed_files += 1
            
        progress = (self.uploaded_files / self.total_files) * 100 if self.total_files > 0 else 0
        logger.info(f"Upload progress: {progress:.2f}% ({self.uploaded_files}/{self.total_files})")

class ImageProcessor:
    """图片处理器"""
    def __init__(self):
        self.failed_downloads: List[str] = []
        self.failed_uploads: List[str] = []
        
    def validate_and_process_image(self, file_path: str) -> bool:
        """验证和处理图片"""
        try:
            with Image.open(file_path) as img:
                # 检查尺寸
                if img.size[0] < ImageConfig.MIN_WIDTH or img.size[1] < ImageConfig.MIN_HEIGHT:
                    logger.warning(f"Image too small: {file_path}")
                    return False
                
                # 检查文件大小并压缩
                if os.path.getsize(file_path) > ImageConfig.MAX_SIZE:
                    logger.info(f"Compressing large image: {file_path}")
                    img.save(file_path, quality=ImageConfig.COMPRESSION_QUALITY, optimize=True)
                
                return True
        except Exception as e:
            logger.error(f"Image validation failed for {file_path}: {e}")
            return False

    async def retry_failed_operations(self):
        """重试失败的操作"""
        # 重试失败的下载
        failed_downloads = self.failed_downloads.copy()
        for url in failed_downloads:
            try:
                await self.download_image(url)
                self.failed_downloads.remove(url)
            except Exception as e:
                logger.error(f"Retry download failed for {url}: {e}")

        # 重试失败的上传
        failed_uploads = self.failed_uploads.copy()
        for file_path in failed_uploads:
            try:
                await self.upload_image(file_path)
                self.failed_uploads.remove(file_path)
            except Exception as e:
                logger.error(f"Retry upload failed for {file_path}: {e}")

class ImprovedImageHandler:
    """改进的图片处理器"""
    def __init__(self):
        self.cache = ImageCache()
        self.processor = ImageProcessor()
        self.progress = UploadProgressTracker()
        self.download_dir = ImageConfig.DOWNLOAD_DIR
        os.makedirs(self.download_dir, exist_ok=True)
        
    async def download_single_image(self, session: aiohttp.ClientSession, url: str, index: int) -> Optional[str]:
        """下载单个图片"""
        # 首先检查缓存
        if cached_path := self.cache.get_cached_image(url):
            logger.debug(f"Using cached image for {url}")
            return cached_path
            
        for retry in range(ImageConfig.MAX_RETRIES):
            try:
                file_path = os.path.join(self.download_dir, f"image_{index}.jpg")
                
                async with session.get(url, timeout=ImageConfig.TIMEOUT) as response:
                    if response.status != 200:
                        raise Exception(f"HTTP {response.status}")
                        
                    with open(file_path, 'wb') as f:
                        async for chunk in response.content.iter_chunked(ImageConfig.CHUNK_SIZE):
                            f.write(chunk)
                            
                # 验证和处理图片
                if not self.processor.validate_and_process_image(file_path):
                    raise Exception("Image validation failed")
                    
                # 保存到缓存
                cached_path = self.cache.save_to_cache(url, file_path)
                logger.success(f"Successfully downloaded and processed {url}")
                return cached_path
                
            except Exception as e:
                logger.warning(f"Download attempt {retry + 1} failed for {url}: {e}")
                if retry == ImageConfig.MAX_RETRIES - 1:
                    self.processor.failed_downloads.append(url)
                    logger.error(f"Failed to download {url} after {ImageConfig.MAX_RETRIES} attempts")
                await asyncio.sleep(1)  # 失败后等待1秒再重试
                
        return None

    async def download_images_async(self, product_data: Dict) -> List[str]:
        """异步下载所有图片"""
        image_urls = []
        for i in range(1, 18):  # 支持最多17张图片
            url = product_data.get(f'Image {i}')
            if url and isinstance(url, str) and url.strip():
                image_urls.append((url.strip(), i))

        if not image_urls:
            logger.warning("No valid image URLs found in product data")
            return []

        self.progress.total_files = len(image_urls)
        downloaded_images = []

        async with aiohttp.ClientSession() as session:
            tasks = []
            for url, index in image_urls:
                task = asyncio.create_task(self.download_single_image(session, url, index))
                tasks.append(task)

            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result, (url, _) in zip(results, image_urls):
                if isinstance(result, str):  # 成功下载的图片路径
                    downloaded_images.append(result)
                    self.progress.update_progress(True)
                else:  # 下载失败
                    logger.error(f"Failed to download {url}: {result}")
                    self.progress.update_progress(False)

        if not downloaded_images:
            logger.error("No images were successfully downloaded")
        else:
            logger.success(f"Successfully downloaded {len(downloaded_images)} images")

        return downloaded_images

    async def process_product_images(self, product_data: Dict) -> List[str]:
        """处理商品图片"""
        try:
            # 下载并处理所有图片
            downloaded_images = await self.download_images_async(product_data)
            
            if not downloaded_images:
                raise Exception("No images were successfully downloaded")

            # 验证所有下载的图片
            valid_images = []
            for img_path in downloaded_images:
                if os.path.exists(img_path) and self.processor.validate_and_process_image(img_path):
                    valid_images.append(img_path)
                else:
                    logger.warning(f"Skipping invalid image: {img_path}")

            if not valid_images:
                raise Exception("No valid images after processing")

            # 重试失败的操作
            await self.processor.retry_failed_operations()
            
            logger.success(f"Successfully processed {len(valid_images)} images")
            return valid_images

        except Exception as e:
            logger.error(f"Error processing product images: {e}")
            return []

    def cleanup(self):
        """清理临时文件"""
        try:
            # 清理下载目录
            if os.path.exists(self.download_dir):
                for file in os.listdir(self.download_dir):
                    file_path = os.path.join(self.download_dir, file)
                    try:
                        if os.path.isfile(file_path):
                            os.remove(file_path)
                    except Exception as e:
                        logger.error(f"Failed to remove file {file_path}: {e}")
            
            # 强制清理过期缓存
            self.cache.cleanup_expired_cache(force=True)
            
        except Exception as e:
            logger.error(f"Cleanup error: {e}") 