# VC 队列发布系统 - 测试指南

## ✅ 当前状态

### 1. **队列目录结构** ✅
```
~/vc_queue/
├── pending/       ✅ 已创建（有测试文件）
├── processing/    ✅ 已创建
├── completed/     ✅ 已创建
├── failed/        ✅ 已创建
└── processed/     ✅ 已创建
```

### 2. **测试文件** ✅
- `~/vc_queue/pending/test_product_14007.json` - 产品 14007 的测试数据

### 3. **需要处理的问题**

#### ❌ 依赖问题（watch_queue.py）
- `pydantic_core` 架构不匹配（x86_64 vs arm64）
- 需要重新安装依赖或使用正确的 Python 环境

## 🧪 测试步骤

### **方法 1: 完整流程测试（推荐）**

#### Step 1: 修复依赖（如果需要）
```bash
cd /Users/yinxianzhi/workspace/vc
pip3 install --upgrade pydantic pydantic-core
# 或者使用虚拟环境
```

#### Step 2: 启动队列监控
```bash
cd /Users/yinxianzhi/workspace/vc
python3 watch_queue.py
```

#### Step 3: 在 Odoo 中导出产品
1. 登录 https://erp.trivesa.it
2. 进入 **Inventory → Products**
3. 勾选产品 14007（或其他产品）
4. Action → **Export to VC Queue**
5. 检查 `~/vc_queue/pending/` 是否出现新的 JSON 文件

#### Step 4: 观察自动发布
- `watch_queue.py` 会自动检测并处理新文件
- 发布成功后，文件会移动到 `completed/` 或 `failed/`
- Odoo 定时任务每 5 分钟自动读取结果

---

### **方法 2: 仅测试 Odoo 导出功能**

直接在 Odoo 中测试 JSON 导出，不运行 Mac 端：

1. 登录 Odoo
2. Inventory → Products → 勾选产品 → Action → Export to VC Queue
3. 检查服务器上的队列目录（需要配置路径）
4. 或检查 Mac 的 `~/vc_queue/pending/` 目录

---

### **方法 3: 手动测试发布流程**

如果有依赖问题，可以手动调用 vestiaire.py：

```bash
cd /Users/yinxianzhi/workspace/vc
python3 << EOF
import json
from vestiaire import publish_from_data

# 读取测试 JSON
with open('~/vc_queue/pending/test_product_14007.json', 'r') as f:
    data = json.load(f)

# 发布
result = publish_from_data(data)
print(result)
EOF
```

---

## 🔧 故障排查

### 问题 1: 依赖错误
**解决方案**: 
```bash
# 使用系统 Python 或创建虚拟环境
python3 -m venv ~/vc_env
source ~/vc_env/bin/activate
pip install DrissionPage loguru openai python-dotenv
```

### 问题 2: Odoo 无法写入队列目录
**解决方案**: 
- 检查队列目录权限
- 配置系统参数 `vc.queue_directory`
- 或使用共享目录（NFS/SMB/Dropbox）

### 问题 3: Chrome 无法启动
**解决方案**: 
- 确保 Chrome 已安装
- 检查 Chrome 配置文件路径
- 手动登录 VC 到 Profile 2

---

## 📊 验证清单

- [ ] 队列目录创建成功
- [ ] 测试 JSON 文件创建成功
- [ ] watch_queue.py 可以导入
- [ ] Odoo 可以导出产品到队列
- [ ] watch_queue.py 可以读取并处理 JSON
- [ ] vestiaire.py 可以成功发布产品
- [ ] 结果文件正确保存
- [ ] Odoo 定时任务可以读取结果

---

## 🚀 下一步

1. **修复依赖问题**（如果需要）
2. **测试 Odoo 导出功能**
3. **测试完整发布流程**
4. **配置 Odoo 队列目录路径**（如果服务器和 Mac 不在同一机器）

