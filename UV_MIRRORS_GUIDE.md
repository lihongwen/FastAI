# uv 镜像源配置指南

本项目已预配置中国大陆最优镜像源，显著提升依赖安装速度。

## 🚀 性能测试结果

基于82个依赖包的完整安装测试：

| 镜像源 | 下载时间 | 推荐度 | URL |
|--------|---------|-------|-----|
| 🥇 清华大学 | ~6秒 | ⭐⭐⭐ | https://pypi.tuna.tsinghua.edu.cn/simple |
| 🥈 阿里云 | ~6秒 | ⭐⭐ | https://mirrors.aliyun.com/pypi/simple/ |
| 🥉 华为云 | ~7秒 | ⭐⭐ | https://mirrors.huaweicloud.com/repository/pypi/simple |
| 腾讯云 | ~31秒 | ⭐ | https://mirrors.cloud.tencent.com/pypi/simple |
| 官方源 | >60秒 | 海外用户 | https://pypi.org/simple |

## 📁 配置文件

项目根目录的 `uv.toml` 已预配置清华镜像源：

```toml
# 默认使用清华大学镜像源（测试结果最快）
index-url = "https://pypi.tuna.tsinghua.edu.cn/simple"

# 启用缓存以提高重复安装速度
no-cache = false
```

## 🛠️ 使用方法

### 自动使用（推荐）
```bash
# 项目已预配置，直接使用即可
uv run mcp-server
```

### 手动指定镜像源
```bash
# 阿里云镜像
uv run --index-url https://mirrors.aliyun.com/pypi/simple/ mcp-server

# 华为云镜像  
uv run --index-url https://mirrors.huaweicloud.com/repository/pypi/simple mcp-server

# 腾讯云镜像
uv run --index-url https://mirrors.cloud.tencent.com/pypi/simple mcp-server

# 官方源（海外用户或特殊需求）
uv run --index-url https://pypi.org/simple mcp-server
```

### 环境变量配置
```bash
# 设置环境变量（全局生效）
export UV_INDEX_URL="https://pypi.tuna.tsinghua.edu.cn/simple"
uv run mcp-server

# Windows
set UV_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
uv run mcp-server
```

## 🌍 地域推荐

### 中国大陆用户
1. **清华大学镜像** - 教育网和公网都很快
2. **阿里云镜像** - 商用环境友好
3. **华为云镜像** - 企业用户优选

### 海外用户
- 直接使用官方PyPI源：删除或注释 `uv.toml` 中的 `index-url` 配置

### 特殊网络环境
- 公司内网：可能需要配置代理或使用内部镜像
- 教育网：清华镜像通常是最佳选择

## 🔧 故障排除

### 镜像源连接失败
```bash
# 切换到备用镜像源
uv run --index-url https://mirrors.aliyun.com/pypi/simple/ mcp-server
```

### 包版本不同步
```bash
# 使用官方源获取最新版本
uv run --index-url https://pypi.org/simple mcp-server
```

### 清除缓存重新安装
```bash
# 清除uv缓存
uv cache clean

# 删除虚拟环境重新创建
rm -rf .venv
uv run mcp-server
```

## 📊 速度对比示例

```bash
# 测试脚本：比较不同镜像源的安装速度
echo "Testing Tsinghua mirror..."
time uv run --index-url https://pypi.tuna.tsinghua.edu.cn/simple python -c "import sys; print('Ready!')"

echo "Testing Aliyun mirror..."  
time uv run --index-url https://mirrors.aliyun.com/pypi/simple/ python -c "import sys; print('Ready!')"

echo "Testing official PyPI..."
time uv run --index-url https://pypi.org/simple python -c "import sys; print('Ready!')"
```

## 🚨 注意事项

1. **首次安装**: 即使使用镜像源，首次安装仍需要下载所有依赖
2. **缓存效果**: 第二次运行会利用本地缓存，速度显著提升
3. **网络环境**: 镜像源速度可能因时段和网络环境而异
4. **包完整性**: 所有镜像源都会验证包的完整性和签名

## 📝 贡献

如发现更快的镜像源或有优化建议，欢迎提交PR更新此指南。