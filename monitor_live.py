#!/usr/bin/env python3
"""
VC 发布实时监控脚本
实时显示发布进度、截屏、错误信息
"""

import os
import time
import glob
from pathlib import Path
from datetime import datetime

def get_latest_screenshot():
    """获取最新的截屏文件"""
    screenshots = glob.glob('/Users/yinxianzhi/workspace/vc/logs/*.png')
    if not screenshots:
        return None
    return max(screenshots, key=os.path.getmtime)

def get_latest_log():
    """获取最新的日志文件"""
    log_files = glob.glob('/Users/yinxianzhi/workspace/vc/logs/vestiaire_*.log')
    if not log_files:
        return None
    return max(log_files, key=os.path.getmtime)

def get_log_tail(log_file, lines=20):
    """获取日志最后N行"""
    if not log_file or not os.path.exists(log_file):
        return []
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
            return all_lines[-lines:]
    except:
        return []

def monitor_publishing():
    """实时监控发布过程"""
    print("\n" + "=" * 80)
    print("🔍 VC 发布实时监控")
    print("=" * 80)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("按 Ctrl+C 停止监控\n")
    
    last_screenshot = None
    last_log_time = 0
    
    try:
        while True:
            # 清屏（可选）
            # os.system('clear' if os.name != 'nt' else 'cls')
            
            print("\n" + "-" * 80)
            print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("-" * 80)
            
            # 检查最新的截屏
            latest_screenshot = get_latest_screenshot()
            if latest_screenshot:
                screenshot_time = os.path.getmtime(latest_screenshot)
                if screenshot_time != last_screenshot:
                    screenshot_age = int(time.time() - screenshot_time)
                    print(f"\n📸 最新截屏: {os.path.basename(latest_screenshot)}")
                    print(f"   时间: {screenshot_age}秒前")
                    last_screenshot = screenshot_time
            
            # 检查日志文件
            latest_log = get_latest_log()
            if latest_log:
                log_time = os.path.getmtime(latest_log)
                if log_time != last_log_time:
                    log_lines = get_log_tail(latest_log, 15)
                    
                    print(f"\n📝 最新日志 ({os.path.basename(latest_log)}):")
                    print("   " + "-" * 76)
                    
                    # 只显示关键信息
                    for line in log_lines:
                        line = line.strip()
                        if not line:
                            continue
                        
                        # 高亮重要信息
                        if 'SUCCESS' in line or '✅' in line:
                            print(f"   ✅ {line}")
                        elif 'ERROR' in line or '❌' in line:
                            print(f"   ❌ {line}")
                        elif '步骤' in line or '步骤' in line or 'Step' in line:
                            print(f"   📋 {line}")
                        elif '截屏' in line or 'screenshot' in line.lower():
                            print(f"   📸 {line}")
                        elif 'INFO' in line:
                            print(f"   ℹ️  {line}")
                        else:
                            print(f"   {line}")
                    
                    last_log_time = log_time
            
            # 检查队列状态
            queue_dir = Path('/Users/yinxianzhi/workspace/vc/queue')
            if queue_dir.exists():
                json_files = list(queue_dir.glob('*.json'))
                print(f"\n📦 队列状态: {len(json_files)} 个产品待处理")
                
                if json_files:
                    print("   待处理文件:")
                    for i, f in enumerate(json_files[:5], 1):
                        print(f"      {i}. {f.name}")
                    if len(json_files) > 5:
                        print(f"      ... 还有 {len(json_files) - 5} 个")
            
            # 检查 completed 和 failed
            completed_dir = Path('/Users/yinxianzhi/workspace/vc/completed')
            failed_dir = Path('/Users/yinxianzhi/workspace/vc/failed')
            
            completed_count = len(list(completed_dir.glob('*.json'))) if completed_dir.exists() else 0
            failed_count = len(list(failed_dir.glob('*.json'))) if failed_dir.exists() else 0
            
            print(f"\n📊 统计:")
            print(f"   ✅ 成功: {completed_count}")
            print(f"   ❌ 失败: {failed_count}")
            
            # 检查 Chrome 进程
            try:
                import subprocess
                result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
                chrome_count = len([l for l in result.stdout.split('\n') if 'Google Chrome' in l and 'grep' not in l])
                port_9222 = '9222' in result.stdout
                
                print(f"\n🌐 Chrome 状态:")
                print(f"   进程数: {chrome_count}")
                print(f"   调试端口 9222: {'✅ 监听中' if port_9222 else '❌ 未监听'}")
            except:
                pass
            
            print("\n" + "-" * 80)
            print("⏳ 5秒后刷新... (Ctrl+C 停止)")
            
            time.sleep(5)
            
    except KeyboardInterrupt:
        print("\n\n👋 监控已停止")
        print("=" * 80)

if __name__ == '__main__':
    monitor_publishing()

