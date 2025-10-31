#!/usr/bin/env python3
"""
VC 队列监控脚本
自动监控 ~/vc_queue/pending/ 目录，处理待发布产品
"""

import os
import json
import time
import shutil
from pathlib import Path
from datetime import datetime
from loguru import logger
import vestiaire

# 配置目录路径
HOME = Path.home()
QUEUE_DIR = HOME / 'vc_queue'
PENDING_DIR = QUEUE_DIR / 'pending'
PROCESSING_DIR = QUEUE_DIR / 'processing'
COMPLETED_DIR = QUEUE_DIR / 'completed'
FAILED_DIR = QUEUE_DIR / 'failed'

# 确保所有目录存在
for directory in [PENDING_DIR, PROCESSING_DIR, COMPLETED_DIR, FAILED_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

logger.info(f"📁 队列目录: {QUEUE_DIR}")
logger.info(f"   - pending:    {PENDING_DIR}")
logger.info(f"   - processing: {PROCESSING_DIR}")
logger.info(f"   - completed:  {COMPLETED_DIR}")
logger.info(f"   - failed:     {FAILED_DIR}")


def process_json_file(json_path):
    """处理单个 JSON 文件"""
    logger.info(f"📋 开始处理: {json_path.name}")
    
    try:
        # 1. 移动到 processing 目录
        processing_path = PROCESSING_DIR / json_path.name
        shutil.move(str(json_path), str(processing_path))
        logger.debug(f"   移动到 processing: {processing_path}")
        
        # 2. 读取 JSON 数据
        with open(processing_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        product_id = data.get('product_id', 'unknown')
        product_name = data.get('product_name', 'Unknown Product')
        logger.info(f"   产品 ID: {product_id}")
        logger.info(f"   产品名称: {product_name}")
        
        # 3. 调用 vestiaire.py 的发布函数
        logger.info(f"   开始发布到 VC...")
        result = vestiaire.publish_from_data(data)
        
        # 4. 生成结果 JSON
        result_data = {
            'product_id': product_id,
            'product_name': product_name,
            'success': result.get('success', False),
            'vc_item_id': result.get('vc_item_id', ''),
            'vc_listing_url': result.get('vc_listing_url', ''),
            'error': result.get('error', ''),
            'processed_time': datetime.now().isoformat(),
        }
        
        # 5. 移动到对应的完成目录
        if result['success']:
            final_dir = COMPLETED_DIR
            logger.success(f"   ✅ 发布成功! VC Item ID: {result['vc_item_id']}")
        else:
            final_dir = FAILED_DIR
            logger.error(f"   ❌ 发布失败: {result['error']}")
        
        # 保存原始 JSON
        final_path = final_dir / processing_path.name
        shutil.move(str(processing_path), str(final_path))
        
        # 保存结果 JSON
        result_filename = f"result_{processing_path.stem}.json"
        result_path = final_dir / result_filename
        with open(result_path, 'w', encoding='utf-8') as f:
            json.dump(result_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"   结果保存到: {result_path}")
        return result_data
        
    except Exception as e:
        logger.exception(f"❌ 处理文件时出错: {e}")
        
        # 出错时移动到 failed 目录
        error_path = FAILED_DIR / json_path.name
        if processing_path.exists():
            shutil.move(str(processing_path), str(error_path))
        
        # 保存错误信息
        error_data = {
            'product_id': 'unknown',
            'success': False,
            'error': str(e),
            'processed_time': datetime.now().isoformat(),
        }
        error_result_path = FAILED_DIR / f"result_{json_path.stem}.json"
        with open(error_result_path, 'w', encoding='utf-8') as f:
            json.dump(error_data, f, indent=2, ensure_ascii=False)
        
        return error_data


def watch_queue(interval=10):
    """监控队列目录"""
    logger.info("🚀 开始监控 VC 队列...")
    logger.info(f"   扫描间隔: {interval} 秒")
    logger.info("   按 Ctrl+C 停止\n")
    
    processed_count = 0
    success_count = 0
    failed_count = 0
    
    try:
        while True:
            # 查找所有待处理的 JSON 文件
            json_files = sorted(PENDING_DIR.glob('*.json'))
            
            if json_files:
                logger.info(f"📥 发现 {len(json_files)} 个待处理文件")
                
                for json_file in json_files:
                    result = process_json_file(json_file)
                    processed_count += 1
                    
                    if result['success']:
                        success_count += 1
                    else:
                        failed_count += 1
                    
                    logger.info(f"📊 统计: 已处理={processed_count}, 成功={success_count}, 失败={failed_count}\n")
                    
                    # 处理完一个文件后等待一小段时间，避免过快
                    time.sleep(2)
            else:
                # 没有文件时，显示等待状态
                logger.debug(f"⏳ 队列为空，等待新文件... (已处理={processed_count})")
            
            # 等待下一次扫描
            time.sleep(interval)
            
    except KeyboardInterrupt:
        logger.warning("\n\n⚠️  收到中断信号，正在停止...")
        logger.info(f"📊 最终统计:")
        logger.info(f"   总处理: {processed_count}")
        logger.info(f"   成功: {success_count}")
        logger.info(f"   失败: {failed_count}")
        logger.info("👋 队列监控已停止")


if __name__ == '__main__':
    # 配置日志
    logger.add(
        QUEUE_DIR / "watch_queue.log",
        rotation="1 day",
        retention="30 days",
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
    )
    
    watch_queue(interval=10)

