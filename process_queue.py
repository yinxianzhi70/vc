#!/usr/bin/env python3
"""
VC 队列处理脚本 - 简化版
直接使用 vestiaire.py 的 publish_from_data 函数
"""

import json
import os
import shutil
from pathlib import Path
from datetime import datetime
from loguru import logger
import vestiaire

# 队列目录 - 使用当前目录下的 queue 文件夹
QUEUE_DIR = Path(__file__).parent / 'queue'
PENDING_DIR = QUEUE_DIR / 'pending'
PROCESSING_DIR = QUEUE_DIR / 'processing'
COMPLETED_DIR = QUEUE_DIR / 'completed'
FAILED_DIR = QUEUE_DIR / 'failed'

# 如果 pending 目录不存在，使用 queue 目录本身
if not PENDING_DIR.exists():
    PENDING_DIR = QUEUE_DIR

# 确保目录存在
for d in [PENDING_DIR, PROCESSING_DIR, COMPLETED_DIR, FAILED_DIR]:
    d.mkdir(parents=True, exist_ok=True)

def process_one_file(json_file):
    """处理单个 JSON 文件"""
    logger.info(f"=" * 60)
    logger.info(f"📋 处理文件: {json_file.name}")
    logger.info(f"=" * 60)
    
    # 移动到 processing
    processing_file = PROCESSING_DIR / json_file.name
    shutil.move(str(json_file), str(processing_file))
    logger.info(f"   → 已移动到 processing/")
    
    try:
        # 读取 JSON
        with open(processing_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        product_id = data.get('product_id', 'unknown')
        product_name = data.get('product_name', 'Unknown')
        logger.info(f"   产品 ID: {product_id}")
        logger.info(f"   产品名称: {product_name}")
        logger.info(f"   Gender: {data.get('Gender')}")
        logger.info(f"   Category: {data.get('Category')}")
        logger.info(f"   Brand: {data.get('Brand')}")
        logger.info(f"   Price: €{data.get('Price')}")
        
        # 调用 vestiaire.py 的发布函数
        logger.info(f"\n🚀 开始发布...")
        result = vestiaire.publish_from_data(data)
        
        # 保存结果
        result_data = {
            'product_id': product_id,
            'product_name': product_name,
            'success': result.get('success', False),
            'vc_item_id': result.get('vc_item_id', ''),
            'vc_listing_url': result.get('vc_listing_url', ''),
            'error': result.get('error', ''),
            'processed_time': datetime.now().isoformat(),
        }
        
        # 移动到对应目录
        if result['success']:
            final_dir = COMPLETED_DIR
            logger.success(f"\n✅ 发布成功！")
            logger.info(f"   VC Item ID: {result['vc_item_id']}")
            logger.info(f"   URL: {result['vc_listing_url']}")
        else:
            final_dir = FAILED_DIR
            logger.error(f"\n❌ 发布失败: {result['error']}")
        
        # 移动文件
        final_file = final_dir / json_file.name
        shutil.move(str(processing_file), str(final_file))
        
        # 保存结果 JSON
        result_file = final_dir / f"result_{json_file.stem}.json"
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(result_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"   → 已移动到 {final_dir.name}/")
        return result_data
        
    except Exception as e:
        logger.exception(f"❌ 处理失败: {e}")
        
        # 移动到 failed
        failed_file = FAILED_DIR / json_file.name
        if processing_file.exists():
            shutil.move(str(processing_file), str(failed_file))
        
        # 保存错误信息
        error_data = {
            'product_id': data.get('product_id', 'unknown') if 'data' in locals() else 'unknown',
            'success': False,
            'error': str(e),
            'processed_time': datetime.now().isoformat(),
        }
        
        result_file = FAILED_DIR / f"result_{json_file.stem}.json"
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(error_data, f, indent=2, ensure_ascii=False)
        
        return error_data


def main():
    """主函数：处理所有待处理文件"""
    logger.info("🚀 VC 队列处理器启动")
    logger.info(f"队列目录: {QUEUE_DIR}\n")
    
    # 查找所有待处理文件
    json_files = sorted(PENDING_DIR.glob('*.json'))
    
    if not json_files:
        logger.warning("⚠️  pending/ 目录为空，没有文件需要处理")
        return
    
    logger.info(f"📥 发现 {len(json_files)} 个待处理文件\n")
    
    # 逐个处理
    success_count = 0
    failed_count = 0
    
    for i, json_file in enumerate(json_files, 1):
        logger.info(f"\n{'=' * 60}")
        logger.info(f"进度: {i}/{len(json_files)}")
        logger.info(f"{'=' * 60}")
        
        result = process_one_file(json_file)
        
        if result['success']:
            success_count += 1
        else:
            failed_count += 1
        
        logger.info(f"\n📊 当前统计: 成功={success_count}, 失败={failed_count}")
    
    # 最终统计
    logger.info(f"\n\n{'=' * 60}")
    logger.success(f"🎉 处理完成！")
    logger.info(f"   总计: {len(json_files)} 个文件")
    logger.info(f"   成功: {success_count}")
    logger.info(f"   失败: {failed_count}")
    logger.info(f"{'=' * 60}\n")


if __name__ == '__main__':
    main()

