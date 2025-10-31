#!/bin/bash
# VC 自动发布系统 - 一键启动
# 双击此文件即可运行

clear
echo "================================================================"
echo "🚀 VC 自动发布系统"
echo "================================================================"
echo ""

cd "$(dirname "$0")"

# 步骤 1: 启动 Chrome
echo "📱 步骤 1/3: 启动 Chrome..."
if lsof -nP -iTCP:9222 | grep -q LISTEN; then
    echo "   ✅ Chrome 已在运行"
else
    echo "   正在启动 Chrome..."
    pkill -f "Google Chrome" 2>/dev/null
    sleep 1
    
    /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
      --user-data-dir="$HOME/Library/Application Support/Google/Chrome" \
      --profile-directory="Profile 7" \
      --remote-debugging-port=9222 \
      --no-first-run \
      --no-default-browser-check \
      > /tmp/chrome_vc.log 2>&1 &
    
    echo "   等待 Chrome 启动..."
    sleep 5
    
    if lsof -nP -iTCP:9222 | grep -q LISTEN; then
        echo "   ✅ Chrome 启动成功"
    else
        echo "   ❌ Chrome 启动失败"
        echo "   请手动打开 Chrome 并重新运行此脚本"
        exit 1
    fi
fi

echo ""

# 步骤 2: 检查登录状态
echo "🔐 步骤 2/3: 检查 VC 登录状态..."
source venv/bin/activate
python3 -c "
from DrissionPage import ChromiumPage
try:
    page = ChromiumPage(addr_or_opts='127.0.0.1:9222')
    tab = page.get_tab()
    tab.get('https://www.vestiairecollective.com/')
    tab.wait(2)
    
    if tab.ele('xpath://a[contains(@href, \"/sell\")]', timeout=2):
        print('   ✅ 已登录到 VC')
    else:
        print('   ⚠️  未登录')
        print('   请在 Chrome 中登录 VC (info@trivesa.it)')
        print('   登录后按回车继续...')
        input()
except Exception as e:
    print(f'   ❌ 检查失败: {e}')
    exit(1)
" || exit 1

echo ""

# 步骤 3: 开始批量发布
echo "🚀 步骤 3/3: 开始批量发布产品..."
echo ""

QUEUE_COUNT=$(ls -1 queue/*.json 2>/dev/null | wc -l | tr -d ' ')

if [ "$QUEUE_COUNT" -eq "0" ]; then
    echo "   ⚠️  队列为空，没有产品需要发布"
    echo ""
    echo "   💡 下一步："
    echo "   1. 在 Odoo 中选择产品"
    echo "   2. 点击 Action → Export to VC Queue"
    echo "   3. 将 JSON 文件放到 queue/ 文件夹"
    echo "   4. 重新运行此脚本"
    echo ""
    exit 0
fi

echo "   📦 发现 $QUEUE_COUNT 个产品待发布"
echo ""
read -p "   是否开始发布？(y/N) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "   已取消"
    exit 0
fi

echo ""
echo "================================================================"
echo "⚡ 开始自动发布..."
echo "================================================================"
echo ""

# 运行发布脚本
python3 process_queue.py

echo ""
echo "================================================================"
echo "✅ 发布完成！"
echo "================================================================"
echo ""
echo "📊 查看结果："
echo "   成功: completed/ 文件夹"
echo "   失败: failed/ 文件夹"
echo ""

