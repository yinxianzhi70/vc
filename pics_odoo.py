"""
Odoo 图片处理模块 - 从 listing/data/products 文件夹获取图片
适配新的 Odoo 数据流程
"""

import os
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from loguru import logger


def find_product_images_folder(default_code, base_path="/Users/yinxianzhi/workspace/listing/data/products", max_days=120):
    """
    查找产品图片所在的文件夹
    
    Args:
        default_code: Odoo 的 default_code (例如: "803099 PRADA WS04SE")
        base_path: 图片根目录
        max_days: 搜索最近多少天的文件夹（默认 120 天）
        
    Returns:
        图片文件夹路径，如果找不到返回 None
    """
    base_path = Path(base_path)
    
    if not base_path.exists():
        logger.error(f"❌ 图片根目录不存在: {base_path}")
        return None
    
    # 将 default_code 转换为文件名前缀 (空格保留)
    # "803099 PRADA WS04SE" → 查找 "803099 PRADA WS*_*.jpg"
    # 注意：由于数据不一致（WS04SE vs WSO4SE），使用前缀匹配
    filename_prefix = default_code.strip()
    
    # 提取前缀部分用于模糊匹配: "803099 PRADA WS04SE" → "803099 PRADA"
    parts = filename_prefix.split()
    if len(parts) >= 2:
        # 使用前两部分（数字 + 品牌）进行匹配
        filename_prefix = ' '.join(parts[:2])  # "803099 PRADA"
        logger.debug(f"使用前缀进行模糊匹配: {filename_prefix}")
    
    # 搜索最近 max_days 天的文件夹
    today = datetime.now()
    
    for days_ago in range(max_days):
        # 尝试多种日期格式
        date = today - timedelta(days=days_ago)
        
        # 格式1: 2025_09_29
        folder1 = base_path / date.strftime("%Y_%m_%d")
        if folder1.exists():
            # 检查是否有匹配的图片（支持 .jpg 和 .jpeg）
            matching_files = []
            for ext in ['*.jpg', '*.jpeg', '*.JPG', '*.JPEG']:
                matching_files.extend(list(folder1.glob(f"{filename_prefix}{ext}")))
            
            if matching_files:
                logger.info(f"✅ 找到图片文件夹: {folder1} ({len(matching_files)} 张图片)")
                return folder1
        
        # 格式2: 20250929 (无下划线)
        folder2 = base_path / date.strftime("%Y%m%d")
        if folder2.exists():
            matching_files = []
            for ext in ['*.jpg', '*.jpeg', '*.JPG', '*.JPEG']:
                matching_files.extend(list(folder2.glob(f"{filename_prefix}{ext}")))
            
            if matching_files:
                logger.info(f"✅ 找到图片文件夹: {folder2} ({len(matching_files)} 张图片)")
                return folder2
    
    logger.error(f"❌ 未找到产品图片 (default_code: {default_code}, 搜索天数: {max_days})")
    return None


def save_all_pics(product_data):
    """
    从 listing/data/products 文件夹获取图片并复制到 download 文件夹
    
    Args:
        product_data: 产品字典，必须包含 'External reference' 或 'Style number' 字段
        
    Returns:
        本地图片保存的绝对地址列表
    """
    
    # 清空 download 文件夹
    clear_jpg_files('download')
    
    abs_path = os.path.abspath('download')
    saved_pic_paths = []
    
    # 获取产品的 External reference 或 Style number 作为图片文件名前缀
    # External reference 格式: "803099 PRADA WS04SE"
    external_ref = product_data.get('External reference', '')
    
    if not external_ref:
        logger.error("❌ 产品数据中没有 'External reference' 字段")
        return saved_pic_paths
    
    # 从 External reference 提取 default_code
    # "803099 PRADA WS04SE" → 直接使用
    default_code = external_ref.strip()
    
    # 查找图片文件夹
    image_folder = find_product_images_folder(default_code)
    
    if not image_folder:
        logger.error(f"❌ 未找到产品图片 (External reference: {external_ref})")
        return saved_pic_paths
    
    # 获取所有匹配的图片文件
    matching_files = []
    
    # 搜索以 default_code 开头的所有图片
    # 注意：由于数据不一致问题（WS04SE vs WSO4SE），我们需要模糊匹配
    # 提取前缀部分用于匹配: "803099 PRADA WS04SE" → "803099 PRADA"
    parts = default_code.split()
    if len(parts) >= 2:
        # 使用前两部分（数字 + 品牌）进行匹配
        search_prefix = ' '.join(parts[:2])  # "803099 PRADA"
        logger.debug(f"使用前缀搜索: {search_prefix}")
    else:
        search_prefix = default_code
    
    for filename in os.listdir(image_folder):
        if filename.startswith(search_prefix) and filename.lower().endswith(('.jpg', '.jpeg')):
            matching_files.append(filename)
    
    if not matching_files:
        logger.error(f"❌ 在文件夹中未找到匹配的图片: {image_folder}")
        return saved_pic_paths
    
    # 按文件名排序，确保顺序一致
    # 排序规则：
    # - _0 (标签图) 跳过
    # - _04 (主图) 优先
    # - 其他按数字排序
    def sort_key(filename):
        # 提取后缀数字
        import re
        match = re.search(r'_(\d+)\.', filename)
        if match:
            num = int(match.group(1))
            # _04 排最前
            if num == 4:
                return (0, num)
            # _0 排最后（但会被跳过）
            elif num == 0:
                return (999, num)
            # 其他按数字排序
            else:
                return (1, num)
        return (1, 999)
    
    matching_files.sort(key=sort_key)
    
    # 复制图片到 download 文件夹
    copied_count = 0
    for filename in matching_files:
        # 跳过 _0 (产品标签图)
        if '_0.' in filename:
            logger.debug(f"跳过标签图: {filename}")
            continue
        
        if copied_count >= 15:  # 最多15张图片
            break
        
        src_path = os.path.join(image_folder, filename)
        dst_filename = f'{copied_count + 1}.jpg'
        dst_path = os.path.join('download', dst_filename)
        
        try:
            # 确保输出目录存在
            os.makedirs('download', exist_ok=True)
            
            # 复制文件
            shutil.copy2(src_path, dst_path)
            
            pic_abs_path = os.path.join(abs_path, dst_filename)
            saved_pic_paths.append(pic_abs_path)
            copied_count += 1
            
            logger.debug(f'✅ 复制图片: {filename} → {dst_filename}')
            
        except Exception as e:
            logger.error(f'❌ 复制图片失败 {filename}: {str(e)}')
            continue
    
    if not saved_pic_paths:
        logger.error(f"❌ 未能复制任何图片 (External reference: {external_ref})")
    else:
        logger.info(f"✅ 成功准备 {len(saved_pic_paths)} 张图片 (External reference: {external_ref})")
    
    return saved_pic_paths


def clear_jpg_files(folder_path):
    """清空文件夹中的所有 jpg 文件"""
    if not os.path.exists(folder_path):
        os.makedirs(folder_path, exist_ok=True)
        return
    
    for filename in os.listdir(folder_path):
        if filename.lower().endswith(('.jpg', '.jpeg')):
            file_path = os.path.join(folder_path, filename)
            try:
                os.remove(file_path)
                logger.debug(f'清除旧图片: {filename}')
            except Exception as e:
                logger.warning(f'清除文件失败 {filename}: {str(e)}')


# 测试函数
if __name__ == '__main__':
    # 测试数据
    test_data = {
        'External reference': '803099 PRADA WS04SE',
        'Gender': 'Womenswear',
        'Category': 'Slippers',
    }
    
    print("=" * 60)
    print("测试图片查找功能")
    print("=" * 60)
    
    # 查找图片文件夹
    folder = find_product_images_folder(test_data['External reference'])
    if folder:
        print(f"\n✅ 找到图片文件夹: {folder}")
        
        # 列出所有匹配的图片
        matching_files = list(folder.glob(f"{test_data['External reference']}*.jpg"))
        print(f"   匹配的图片数量: {len(matching_files)}")
        
        # 复制图片到 download 文件夹
        saved_paths = save_all_pics(test_data)
        print(f"\n✅ 成功复制 {len(saved_paths)} 张图片到 download 文件夹")
        for i, path in enumerate(saved_paths, 1):
            print(f"   {i}. {path}")
    else:
        print("\n❌ 未找到图片文件夹")

