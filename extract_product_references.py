#!/usr/bin/env python3
"""
产品引用编号提取工具
从VC应用的queue目录中提取所有产品的External Reference字段
生成Excel汇总表格

作者: AI助手
日期: 2025-10-03
"""

import json
import os
import sys
import pandas as pd
from pathlib import Path
from datetime import datetime

def extract_product_references(queue_dir='queue', output_file=None):
    """
    从queue目录提取产品引用编号

    Args:
        queue_dir: queue目录路径
        output_file: 输出Excel文件路径，默认为自动生成

    Returns:
        bool: 是否成功
    """
    print("🚀 开始提取产品引用编号...")

    # 收集所有external references
    references = []

    # 查找所有JSON文件
    queue_path = Path(queue_dir)
    if not queue_path.exists():
        print(f"❌ Queue目录不存在: {queue_dir}")
        return False

    json_files = list(queue_path.glob('*.json'))
    total_files = len(json_files)

    print(f"📂 找到 {total_files} 个JSON文件")

    for json_file in sorted(json_files):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 提取关键信息
            external_ref = data.get('External reference', '')
            brand = data.get('Brand', '')
            category = data.get('Category', '')
            gender = data.get('Gender', '')

            if external_ref:  # 只有当有引用编号时才记录
                references.append({
                    'Index': int(json_file.stem),  # 从文件名获取序号
                    'External Reference': external_ref,
                    'Brand': brand,
                    'Category': category,
                    'Gender': gender
                })

        except Exception as e:
            print(f"⚠️ 读取文件 {json_file.name} 时出错: {e}")
            continue

    if not references:
        print("❌ 未找到任何有效的引用编号")
        return False

    # 创建DataFrame
    df = pd.DataFrame(references)

    # 生成输出文件名
    if not output_file:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f'product_references_summary_{timestamp}.xlsx'

    # 保存到Excel文件
    try:
        df.to_excel(output_file, index=False)
        print(f"✅ 已创建汇总文件: {output_file}")
        print(f"📊 总共处理了 {len(references)} 个产品")
        print(f"📋 文件列标题: {list(df.columns)}")

        # 显示统计信息
        print("\n📈 数据统计:")
        print(f"   - 总产品数: {len(references)}")
        print(f"   - 唯一品牌数: {df['Brand'].nunique()}")
        print(f"   - 类别分布: {df['Category'].value_counts().to_dict()}")

        # 显示前几个和后几个引用编号
        print("\n🎯 前5个引用编号:")
        for _, row in df.head(5).iterrows():
            print(f"   - {row['External Reference']:20s} | {row['Brand']:15s} | {row['Category']}")

        print("\n🎯 后5个引用编号:")
        for _, row in df.tail(5).iterrows():
            print(f"   - {row['External Reference']:20s} | {row['Brand']:15s} | {row['Category']}")

        return True

    except Exception as e:
        print(f"❌ 保存Excel文件时出错: {e}")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("🎯 VC产品引用编号提取工具")
    print("=" * 60)

    # 默认参数
    queue_dir = 'queue'
    output_file = None

    # 如果有命令行参数
    if len(sys.argv) > 1:
        queue_dir = sys.argv[1]
    if len(sys.argv) > 2:
        output_file = sys.argv[2]

    # 执行提取
    success = extract_product_references(queue_dir, output_file)

    if success:
        print("\n✅ 提取完成！您可以使用Excel打开生成的文件查看所有引用编号。")
    else:
        print("\n❌ 提取失败！请检查queue目录和文件格式。")
        sys.exit(1)

if __name__ == '__main__':
    main()
