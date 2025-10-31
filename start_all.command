#!/bin/bash

# VC 自动发布系统启动脚本
# 自动启动 Chrome、监控脚本和发布流程

cd /Users/yinxianzhi/workspace/vc

# 激活虚拟环境
source venv/bin/activate

# 1. 检查并启动 Chrome
echo "检查 Chrome 状态..."
if ! pgrep -f "Google Chrome.*--remote-debugging-port=9222" > /dev/null; then
    echo "启动 Chrome..."
    bash start_chrome.command > /dev/null 2>&1 &
    sleep 10
fi

# 2. 启动监控脚本（如果未运行）
if ! pgrep -f "python.*monitor.*--watch" > /dev/null; then
    echo "启动监控脚本..."
    python3 monitor.py --watch > logs/monitor.log 2>&1 &
    sleep 2
fi

# 3. 启动发布流程（如果未运行）
if ! pgrep -f "python.*process_queue" > /dev/null; then
    echo "启动发布流程..."
    python3 process_queue.py >> logs/queue_output.log 2>&1 &
    sleep 2
fi

echo ""
echo "========================================"
echo "✅ 系统启动完成！"
echo "========================================"
echo ""
echo "📊 运行状态:"
ps aux | grep -E "(python.*monitor|python.*process_queue|Google Chrome.*9222)" | grep -v grep | wc -l | xargs -I {} echo "   运行中的服务: {} 个"
echo ""
echo "📝 查看日志:"
echo "   监控日志: tail -f logs/monitor.log"
echo "   发布日志: tail -f logs/queue_output.log"
echo ""
echo "⏹️  停止所有服务:"
echo "   pkill -f 'python.*monitor'; pkill -f 'python.*process_queue'"
echo ""

