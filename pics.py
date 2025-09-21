import requests
import os
import time
import shutil

from io import BytesIO
from loguru import logger


def convert_gdrive_link(url):
    """Convert Google Drive link from view to download"""
    if 'drive.google.com' in url and 'export=view' in url:
        return url.replace('export=view', 'export=download')
    return url


def save_all_pics(product_data):
    """
    从本地products文件夹获取图片并复制到download文件夹
    :param product_data: 产品字典
    :return: 本地图片保存的绝对地址
    """

    # empty the download folder
    clear_jpg_files('download')

    abs_path = os.path.abspath('download')
    products_path = os.path.abspath('products')

    saved_pic_paths = []
    
    # 获取产品的External reference作为图片文件名前缀
    external_ref = product_data.get('External reference', '')
    if not external_ref:
        logger.error("No External reference found in product data")
        return saved_pic_paths

    # 查找匹配的图片文件
    if os.path.exists(products_path):
        # 获取所有匹配的图片文件
        matching_files = []
        for filename in os.listdir(products_path):
            if filename.startswith(external_ref) and filename.lower().endswith('.jpg'):
                matching_files.append(filename)
        
        # 按文件名排序，确保顺序一致
        matching_files.sort()
        
        # 复制图片到download文件夹
        for i, filename in enumerate(matching_files, 1):
            if i > 15:  # 最多15张图片
                break
                
            src_path = os.path.join(products_path, filename)
            dst_filename = f'{i}.jpg'
            dst_path = os.path.join('download', dst_filename)
            
            try:
                # 确保输出目录存在
                os.makedirs('download', exist_ok=True)
                
                # 复制文件
                shutil.copy2(src_path, dst_path)
                
                pic_abs_path = os.path.join(abs_path, dst_filename)
                saved_pic_paths.append(pic_abs_path)
                
                logger.debug(f'Copied image from {src_path} to {dst_path}')
                
            except Exception as e:
                logger.error(f'Failed to copy image {filename}: {str(e)}')
                continue
    
    else:
        logger.error(f"Products folder not found: {products_path}")
    
    if not saved_pic_paths:
        logger.error(f"No images found for product: {external_ref}")
    else:
        logger.info(f"Found {len(saved_pic_paths)} images for product: {external_ref}")
    
    return saved_pic_paths


def save_pic(url, num):
    # 从链接获取图片
    save_path = os.path.join('download', f'{num}.jpg')

    for i in range(5):
        try:
            logger.debug(f'Fetching image from {url}')
            response = requests.get(url, stream=True)
            response.raise_for_status()  # 检查请求是否成功

            # 确保输出目录存在
            os.makedirs('download', exist_ok=True)

            # 以二进制写入模式保存图片到本地
            with open(save_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):  # 分块下载
                    file.write(chunk)

                # 保存图片为 JPG 格式
                logger.debug(f'Saving image to {save_path}')
                return f'{num}.jpg'

        except Exception as e:
            logger.error(f'url save failed, retry after 5s: {str(e)}')
            time.sleep(5)
            continue

    logger.error(f'Failed to download image after 5 retries: {url}')
    return None


def clear_jpg_files(folder_path):
    try:
        # 检查文件夹是否存在
        if os.path.exists(folder_path) and os.path.isdir(folder_path):
            # 遍历文件夹中的所有文件（不遍历子目录）
            for filename in os.listdir(folder_path):
                file_path = os.path.join(folder_path, filename)
                # 检查是否是文件且扩展名为 .jpg
                if os.path.isfile(file_path) and file_path.lower().endswith('.jpg'):
                    os.unlink(file_path)  # 删除文件
            print(f"All .jpg files in '{folder_path}' folder have been deleted.")
        else:
            logger.error(f"Folder '{folder_path}' does not exist or is not a directory.")
    except Exception as e:
        logger.error(f"Failed to clear .jpg files: {e}")


if __name__ == '__main__':
    save_pic('https://drive.google.com/uc?export=download&id=1HMZ8q6UcDe0dFHx7fAcKtSUmRmxT4gp_', 2)
