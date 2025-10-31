# VC 队列系统测试指南

## 📋 当前状态

✅ **已完成的调整：**
1. 图片处理模块已适配 Odoo 数据（`pics_odoo.py`）
2. `vestiaire.py` 已更新使用新的图片模块
3. 图片查找功能测试通过（15张图片）
4. 队列文件存在（12个产品）

## 🚀 测试步骤（你需要手动操作）

### 步骤 1：启动 Chrome（Profile 7）

**方法 A：使用 Chrome 图标**
1. 关闭所有 Chrome 窗口
2. 打开终端，复制粘贴以下命令：

```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --user-data-dir="$HOME/Library/Application Support/Google/Chrome" \
  --profile-directory="Profile 7" \
  --remote-debugging-port=9222 \
  --no-first-run \
  --no-default-browser-check &
```

3. Chrome 应该会打开（使用 Profile 7 - trivesa.it）

**方法 B：双击脚本**
- 双击 `/Users/yinxianzhi/workspace/vc/start_chrome.command`

---

### 步骤 2：登录 VC

1. 在打开的 Chrome 中访问：`https://www.vestiairecollective.com/`
2. 检查右上角是否已经登录（Profile 7 应该有 Google 登录状态）
3. 如果未登录，点击"Log in"并使用 Google 账号登录（info@trivesa.it）
4. 确认登录成功（右上角显示头像）

---

### 步骤 3：测试队列处理脚本

打开终端，运行以下命令：

```bash
cd /Users/yinxianzhi/workspace/vc
python3 -c "
from DrissionPage import Chromium

# 测试连接到 Chrome
try:
    print('正在连接到 Chrome (端口 9222)...')
    page = Chromium(addr='127.0.0.1:9222')
    tab = page.get_tab()
    
    print(f'✅ 成功连接到 Chrome')
    print(f'   当前页面: {tab.url}')
    print(f'   页面标题: {tab.title}')
    
except Exception as e:
    print(f'❌ 连接失败: {e}')
    print()
    print('请确认：')
    print('1. Chrome 已经启动')
    print('2. 使用了 --remote-debugging-port=9222 参数')
    print('3. 端口 9222 没有被其他程序占用')
"
```

如果看到 "✅ 成功连接到 Chrome"，说明系统正常！

---

### 步骤 4：测试单个产品发布（安全测试）

运行测试脚本（只测试前几步，不会真正发布）：

```bash
cd /Users/yinxianzhi/workspace/vc
python3 test_vestiaire.py
```

或者手动测试：

```python
cd /Users/yinxianzhi/workspace/vc
python3 -c "
import json
from DrissionPage import Chromium
import vestiaire

# 连接到 Chrome
page = Chromium(addr='127.0.0.1:9222')
tab = page.get_tab()

# 读取一个产品数据
with open('queue/001.json', 'r') as f:
    data = json.load(f)

print('测试产品:', data['Title'])
print()

# 测试登录状态检测
try:
    tab.get('https://www.vestiairecollective.com/')
    tab.wait(5)
    
    # 检查登录状态
    if tab.ele('xpath://a[contains(@href, \"/sell\")]', timeout=3):
        print('✅ 已登录到 VC')
    else:
        print('❌ 未登录，请先登录')
except Exception as e:
    print(f'错误: {e}')
"
```

---

## ⚠️ 注意事项

1. **不要关闭 Chrome**：测试期间保持 Chrome 开启
2. **保持登录**：确保 VC 登录状态有效
3. **测试数据**：当前使用的是旧产品数据，不会重复发布
4. **端口冲突**：如果 9222 被占用，关闭其他 Chrome 实例

---

## 🐛 常见问题

### Q1: Chrome 无法启动
**A:** 确保先关闭所有 Chrome 窗口，然后再运行启动命令

### Q2: 连接失败 "Address: 127.0.0.1:9222"
**A:** 
- 检查 Chrome 是否使用 `--remote-debugging-port=9222` 启动
- 运行 `lsof -nP -iTCP:9222` 查看端口是否监听

### Q3: 图片找不到
**A:** 已经解决！新的 `pics_odoo.py` 会自动搜索 `/Users/yinxianzhi/workspace/listing/data/products/` 中的图片

---

## ✅ 成功后的下一步

如果测试成功，可以：
1. 从 Odoo 导出新产品的 JSON 文件
2. 使用 `process_queue.py` 批量发布
3. 查看 `completed/` 和 `failed/` 目录中的结果

---

需要我的帮助随时告诉我！ 🚀

