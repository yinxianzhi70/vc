#!/usr/bin/env python3
"""
监控控制模块 - 监控脚本和发布流程之间的通信桥梁
"""

import os
import json
import time
from pathlib import Path

CONTROL_DIR = Path('/Users/yinxianzhi/workspace/vc/logs/control')
CONTROL_DIR.mkdir(parents=True, exist_ok=True)

STUCK_FILE = CONTROL_DIR / 'stuck_detected.json'
RETRY_FILE = CONTROL_DIR / 'retry_request.json'
STATUS_FILE = CONTROL_DIR / 'publisher_status.json'

def mark_stuck(step, reason, screenshot_path=None):
    """标记发布流程卡住"""
    stuck_data = {
        'stuck': True,
        'step': step,
        'reason': reason,
        'timestamp': time.time(),
        'screenshot': screenshot_path
    }
    with open(STUCK_FILE, 'w') as f:
        json.dump(stuck_data, f, indent=2)

def clear_stuck():
    """清除卡住标记"""
    if STUCK_FILE.exists():
        STUCK_FILE.unlink()

def is_stuck():
    """检查是否卡住"""
    if not STUCK_FILE.exists():
        return False, None
    
    try:
        with open(STUCK_FILE, 'r') as f:
            data = json.load(f)
            return data.get('stuck', False), data
    except:
        return False, None

def request_retry(step, action='retry'):
    """请求重试或恢复"""
    retry_data = {
        'action': action,  # 'retry', 'skip', 'restart'
        'step': step,
        'timestamp': time.time()
    }
    with open(RETRY_FILE, 'w') as f:
        json.dump(retry_data, f, indent=2)

def get_retry_request():
    """获取重试请求"""
    if not RETRY_FILE.exists():
        return None
    
    try:
        with open(RETRY_FILE, 'r') as f:
            data = json.load(f)
            # 检查请求是否过期（超过10分钟）
            if time.time() - data.get('timestamp', 0) > 600:
                RETRY_FILE.unlink()
                return None
            return data
    except:
        return None

def clear_retry_request():
    """清除重试请求"""
    if RETRY_FILE.exists():
        RETRY_FILE.unlink()

def update_publisher_status(step, status, details=None):
    """更新发布流程状态"""
    status_data = {
        'step': step,
        'status': status,  # 'running', 'stuck', 'error', 'completed'
        'details': details or {},
        'timestamp': time.time()
    }
    with open(STATUS_FILE, 'w') as f:
        json.dump(status_data, f, indent=2)

def get_publisher_status():
    """获取发布流程状态"""
    if not STATUS_FILE.exists():
        return None
    
    try:
        with open(STATUS_FILE, 'r') as f:
            return json.load(f)
    except:
        return None













