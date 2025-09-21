import requests
import os
import time

from io import BytesIO
from loguru import logger


def convert_gdrive_link(url):
    """Convert Google Drive link from view to download"""
    if 'drive.google.com' in url and 'export=view' in url:
        return url.replace('export=view', 'export=download')
    return url


def save_all_pics(product_data):
    """
    下载所有的图片存入本地
    :param product_data: 产品字典
    :return: 本地图片保存的绝对地址
    """

    # empty the download folder
    clear_jpg_files('download')

    abs_path = os.path.abspath('download')

    saved_pic_paths = []
    i = 1
    for key, value in product_data.items():
        if key.startswith('Image ') and value.startswith('http'):
            # 转换 Google Drive 链接
            download_url = convert_gdrive_link(value)
            path = save_pic(download_url, i)
            pic_abs_path = os.path.join(abs_path, path)
            saved_pic_paths.append(pic_abs_path)
            i += 1
            if i > 15:
                break

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
