#!/usr/bin/env python3
"""监控脚本 - 实时监控VC上传程序的运行状态"""

import subprocess
import time
import os
import glob
from datetime import datetime
import sys

# 添加当前目录到路径以导入监控控制模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    import monitor_control
except ImportError:
    monitor_control = None

def get_latest_log():
    """获取最新的日志文件"""
    # 检查多种日志文件格式
    log_patterns = [
        '/Users/yinxianzhi/workspace/vc/logs/vestiaire_*.log',
        '/Users/yinxianzhi/workspace/vc/logs/*.log',
        '/Users/yinxianzhi/workspace/vc/logs/queue_output.log'
    ]
    
    all_logs = []
    for pattern in log_patterns:
        logs = glob.glob(pattern)
        all_logs.extend(logs)
    
    if not all_logs:
        return None
    
    # 返回最新的日志文件
    return max(all_logs, key=os.path.getmtime)

def check_process_running():
    """检查相关Python进程是否还在运行"""
    try:
        result = subprocess.run(
            ['ps', 'aux'],
            capture_output=True,
            text=True
        )
        processes = []
        keywords = ['process_queue.py', 'vestiaire.py', 'publish_from_data']
        
        for line in result.stdout.split('\n'):
            if 'python' in line.lower() and 'grep' not in line:
                for keyword in keywords:
                    if keyword in line:
                        processes.append(line.strip())
                        break
        
        return len(processes) > 0, processes
    except Exception as e:
        return False, f"Error: {e}"

def get_latest_screenshot():
    """获取最新的截屏文件"""
    screenshots = glob.glob('/Users/yinxianzhi/workspace/vc/logs/*.png')
    if not screenshots:
        return None
    return max(screenshots, key=os.path.getmtime)

def get_last_log_lines(n=10):
    """获取日志文件的最后N行"""
    log_file = get_latest_log()
    if not log_file:
        return "No log file found"
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            return ''.join(lines[-n:])
    except Exception as e:
        return f"Error reading log: {e}"

def get_log_file_size(log_file):
    """获取日志文件大小"""
    try:
        return os.path.getsize(log_file)
    except:
        return 0

def main():
    import sys
    
    # 如果传入参数 --watch，持续监控
    watch_mode = '--watch' in sys.argv or '-w' in sys.argv
    
    if watch_mode:
        print("=" * 80)
        print("🔍 VC 发布实时监控 (持续模式)")
        print("=" * 80)
        print("每3秒刷新一次，检测进程卡住情况，按 Ctrl+C 停止\n")
        
        last_screenshot_time = 0
        last_log_time = 0
        last_log_size = 0
        last_activity_time = time.time()
        stuck_warning_shown = False
        check_interval = 3  # 3秒检查一次
        stuck_threshold = 60  # 60秒没有活动就报警
        
        try:
            while True:
                current_time = time.time()
                activity_detected = False
                
                # 清屏
                os.system('clear' if os.name != 'nt' else 'cls')
                
                print("=" * 80)
                print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print("=" * 80)
                
                # 检查最新截屏
                latest_screenshot = get_latest_screenshot()
                screenshot_age = 999999
                if latest_screenshot:
                    screenshot_time = os.path.getmtime(latest_screenshot)
                    screenshot_age = int(current_time - screenshot_time)
                    
                    if screenshot_time != last_screenshot_time:
                        age = int(current_time - screenshot_time)
                        print(f"\n📸 最新截屏: {os.path.basename(latest_screenshot)} ({age}秒前)")
                        last_screenshot_time = screenshot_time
                        last_activity_time = current_time
                        activity_detected = True
                        stuck_warning_shown = False
                    else:
                        print(f"\n📸 最新截屏: {os.path.basename(latest_screenshot)} ({screenshot_age}秒前)")
                
                # 检查最新日志
                latest_log = get_latest_log()
                log_age = 999999
                if latest_log:
                    log_time = os.path.getmtime(latest_log)
                    log_age = int(current_time - log_time)
                    log_size = get_log_file_size(latest_log)
                    
                    # 检查日志文件是否有更新（时间或大小变化）
                    log_updated = (log_time != last_log_time) or (log_size != last_log_size)
                    
                    if log_updated:
                        print(f"\n📝 最新日志: {os.path.basename(latest_log)} ({log_age}秒前, {log_size}字节)")
                        print("-" * 80)
                        lines = get_last_log_lines(20)
                        for line in lines:
                            line = line.strip()
                            if 'SUCCESS' in line or '✅' in line:
                                print(f"✅ {line}")
                            elif 'ERROR' in line or '❌' in line:
                                print(f"❌ {line}")
                            elif '步骤' in line or 'Step' in line:
                                print(f"📋 {line}")
                            elif '截屏' in line or 'screenshot' in line.lower():
                                print(f"📸 {line}")
                            elif line:
                                print(f"   {line}")
                        last_log_time = log_time
                        last_log_size = log_size
                        last_activity_time = current_time
                        activity_detected = True
                        stuck_warning_shown = False
                    else:
                        print(f"\n📝 最新日志: {os.path.basename(latest_log)} ({log_age}秒前, {log_size}字节)")
                
                # 检查进程
                is_running, process_info = check_process_running()
                if isinstance(process_info, list) and len(process_info) > 0:
                    print(f"\n🔴 进程状态: {'🟢 运行中 (' + str(len(process_info)) + '个进程)' if is_running else '🔴 已停止'}")
                    for proc in process_info[:3]:  # 只显示前3个
                        parts = proc.split()
                        if len(parts) > 10:
                            pid = parts[1]
                            cpu = parts[2]
                            mem = parts[3]
                            cmd = ' '.join(parts[10:])[:60]
                            print(f"   PID: {pid}, CPU: {cpu}%, MEM: {mem}%, CMD: {cmd}")
                else:
                    print(f"\n🔴 进程状态: {'🟢 运行中' if is_running else '🔴 已停止'}")
                
                # 检测是否卡住
                time_since_last_activity = int(current_time - last_activity_time)
                if is_running and time_since_last_activity > stuck_threshold:
                    if not stuck_warning_shown:
                        print(f"\n⚠️  ⚠️  ⚠️  警告：进程可能已卡住！")
                        print(f"   进程存在但已经 {time_since_last_activity} 秒没有活动")
                        print(f"   日志最后更新: {log_age}秒前")
                        print(f"   截屏最后更新: {screenshot_age}秒前")
                        print(f"   建议检查进程或手动干预")
                        
                        # 如果有监控控制模块，标记为卡住
                        if monitor_control:
                            publisher_status = monitor_control.get_publisher_status()
                            step = publisher_status.get('step', '未知步骤') if publisher_status else '未知步骤'
                            monitor_control.mark_stuck(step, f'无活动超过{time_since_last_activity}秒')
                            print(f"   📝 已标记卡住状态（步骤: {step}）")
                        
                        stuck_warning_shown = True
                elif activity_detected:
                    stuck_warning_shown = False
                
                # 如果进程停止，显示警告
                if not is_running:
                    print(f"\n⚠️  警告：没有检测到运行中的发布进程！")
                    print(f"   日志最后更新: {log_age}秒前")
                    print(f"   截屏最后更新: {screenshot_age}秒前")
                
                # 检查Chrome
                try:
                    result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
                    chrome_count = len([l for l in result.stdout.split('\n') if 'Google Chrome' in l and 'grep' not in l])
                    port_9222 = '9222' in result.stdout
                    chrome_status = '✅' if port_9222 else '❌'
                    print(f"\n🌐 Chrome: {chrome_count} 进程, 端口9222: {chrome_status}")
                    if not port_9222:
                        print(f"   ⚠️  Chrome调试端口未监听，发布进程可能无法连接")
                except:
                    pass
                
                print("\n" + "-" * 80)
                print(f"⏳ {check_interval}秒后刷新... (Ctrl+C 停止)")
                print(f"   活动检测: {'🟢 正常' if activity_detected or time_since_last_activity < stuck_threshold else '🔴 异常'}")
                
                time.sleep(check_interval)
                
        except KeyboardInterrupt:
            print("\n\n👋 监控已停止")
            return
    
    # 单次查看模式
    print("=" * 80)
    print(f"VC上传程序监控 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # 检查进程状态
    is_running, process_info = check_process_running()
    print(f"\n进程状态: {'🟢 运行中' if is_running else '🔴 已停止'}")
    if process_info:
        print(f"进程信息: {process_info}")
    
    # 获取最新日志文件
    latest_log = get_latest_log()
    if latest_log:
        file_time = datetime.fromtimestamp(os.path.getmtime(latest_log))
        time_diff = (datetime.now() - file_time).total_seconds()
        print(f"\n最新日志文件: {os.path.basename(latest_log)}")
        print(f"最后修改时间: {file_time.strftime('%Y-%m-%d %H:%M:%S')} ({int(time_diff)}秒前)")
    
    # 检查最新截屏
    latest_screenshot = get_latest_screenshot()
    if latest_screenshot:
        screenshot_time = datetime.fromtimestamp(os.path.getmtime(latest_screenshot))
        time_diff = (datetime.now() - screenshot_time).total_seconds()
        print(f"\n📸 最新截屏: {os.path.basename(latest_screenshot)}")
        print(f"   时间: {screenshot_time.strftime('%Y-%m-%d %H:%M:%S')} ({int(time_diff)}秒前)")
    
    # 显示最后10行日志
    print("\n" + "=" * 80)
    print("最后10行日志:")
    print("=" * 80)
    print(get_last_log_lines(10))
    
    # 检查Chrome进程
    try:
        result = subprocess.run(
            ['ps', 'aux'],
            capture_output=True,
            text=True
        )
        chrome_count = 0
        for line in result.stdout.split('\n'):
            if 'Google Chrome' in line and 'grep' not in line:
                chrome_count += 1
        print(f"\nChrome进程数量: {chrome_count}")
    except:
        pass

if __name__ == '__main__':
    main()

