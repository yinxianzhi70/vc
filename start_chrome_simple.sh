#!/bin/bash
# VC Chrome 自动启动脚本（简化版）

echo "🚀 启动 Chrome (Profile 7 - trivesa.it)..."
echo ""

# 关闭现有 Chrome 实例
echo "1. 关闭现有 Chrome 实例..."
pkill -f "Google Chrome" 2>/dev/null
sleep 2

# 启动 Chrome
echo "2. 启动 Chrome (端口 9222)..."
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --user-data-dir="$HOME/Library/Application Support/Google/Chrome" \
  --profile-directory="Profile 7" \
  --remote-debugging-port=9222 \
  --no-first-run \
  --no-default-browser-check \
  > /tmp/chrome_vc.log 2>&1 &

CHROME_PID=$!
echo "   Chrome 进程 ID: $CHROME_PID"

# 等待 Chrome 启动
echo "3. 等待 Chrome 启动..."
sleep 5

# 检查端口
if lsof -nP -iTCP:9222 | grep -q LISTEN; then
    echo ""
    echo "✅ Chrome 启动成功！"
    echo ""
    echo "📋 下一步："
    echo "   1. Chrome 应该已经打开"
    echo "   2. 访问 https://www.vestiairecollective.com/"
    echo "   3. 确认已登录 (info@trivesa.it)"
    echo "   4. 运行测试: python3 test_system.py"
    echo ""
else
    echo ""
    echo "❌ Chrome 启动失败"
    echo ""
    echo "请手动启动 Chrome:"
    echo "/Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome \\"
    echo "  --user-data-dir=\"\$HOME/Library/Application Support/Google/Chrome\" \\"
    echo "  --profile-directory=\"Profile 7\" \\"
    echo "  --remote-debugging-port=9222 \\"
    echo "  --no-first-run \\"
    echo "  --no-default-browser-check &"
    echo ""
fi

