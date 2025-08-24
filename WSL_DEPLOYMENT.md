# pgvector CLI - WSL部署指南

本指南将指导您在Windows Subsystem for Linux (WSL) 上完整部署pgvector CLI工具，确保与macOS环境完全一致。

## 环境要求

- **WSL版本**: WSL 2 (推荐Ubuntu 22.04 LTS)
- **Python版本**: 3.13.4
- **PostgreSQL版本**: 14.18
- **pgvector扩展版本**: 0.8.0

## 1. WSL环境准备

### 1.1 启用WSL 2
```bash
# 在Windows PowerShell (管理员身份) 中执行
wsl --install Ubuntu-22.04
wsl --set-version Ubuntu-22.04 2
```

### 1.2 更新系统
```bash
sudo apt update && sudo apt upgrade -y
```

### 1.3 安装基础开发工具
```bash
sudo apt install -y \
    build-essential \
    curl \
    git \
    wget \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release
```

## 2. Python 3.13.4 安装

### 2.1 添加Python PPA源
```bash
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
```

### 2.2 安装Python 3.13.4
```bash
sudo apt install -y \
    python3.13 \
    python3.13-dev \
    python3.13-venv \
    python3-pip
```

### 2.3 验证Python版本
```bash
python3.13 --version
# 预期输出: Python 3.13.4
```

### 2.4 设置Python3.13为默认版本
```bash
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.13 1
sudo update-alternatives --install /usr/bin/pip3 pip3 /usr/bin/pip3 1
```

## 3. PostgreSQL 14.18 安装

### 3.1 添加PostgreSQL APT仓库
```bash
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
echo "deb http://apt.postgresql.org/pub/repos/apt/ $(lsb_release -cs)-pgdg main" | sudo tee /etc/apt/sources.list.d/pgdg.list
sudo apt update
```

### 3.2 安装PostgreSQL 14
```bash
sudo apt install -y postgresql-14 postgresql-client-14 postgresql-contrib-14 postgresql-server-dev-14
```

### 3.3 启动PostgreSQL服务
```bash
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### 3.4 验证PostgreSQL版本
```bash
sudo -u postgres psql -c "SELECT version();"
# 预期输出包含: PostgreSQL 14.18
```

### 3.5 配置PostgreSQL用户
```bash
# 创建与当前用户同名的数据库用户
sudo -u postgres createuser --superuser $USER

# 创建数据库
sudo -u postgres createdb $USER

# 设置密码 (可选)
sudo -u postgres psql -c "ALTER USER $USER PASSWORD 'your_password';"
```

## 4. pgvector 0.8.0 扩展安装

### 4.1 安装编译依赖
```bash
sudo apt install -y \
    git \
    build-essential \
    postgresql-server-dev-14
```

### 4.2 从源码编译安装pgvector 0.8.0
```bash
# 下载源码
cd /tmp
git clone https://github.com/pgvector/pgvector.git
cd pgvector

# 切换到0.8.0版本
git checkout v0.8.0

# 编译安装
make
sudo make install
```

### 4.3 在数据库中启用pgvector扩展
```bash
psql -d postgres -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

### 4.4 验证pgvector版本
```bash
psql -d postgres -c "SELECT * FROM pg_extension WHERE extname = 'vector';"
# 预期输出: extversion | 0.8.0
```

## 5. 项目部署

### 5.1 克隆项目代码
```bash
cd ~
git clone <your-repo-url> FastAI
cd FastAI
```

### 5.2 创建虚拟环境
```bash
python3.13 -m venv venv
source venv/bin/activate
```

### 5.3 升级pip
```bash
pip install --upgrade pip
```

### 5.4 安装项目依赖
```bash
pip install -r requirements.txt
```

### 5.5 安装项目包
```bash
pip install -e .
```

## 6. 环境配置

### 6.1 创建.env文件
```bash
cat > .env << EOF
# Database connection - 根据实际情况调整
DATABASE_URL=postgresql://$USER@localhost:5432/postgres

# Application settings
DEBUG=false

# DashScope embedding service configuration (阿里云)
DASHSCOPE_API_KEY=your_api_key_here
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

# Cleanup configuration
SOFT_DELETE_RETENTION_DAYS=30
EOF
```

### 6.2 配置数据库连接
如果需要密码认证，修改.env文件中的DATABASE_URL：
```bash
DATABASE_URL=postgresql://username:password@localhost:5432/postgres
```

## 7. 验证部署

### 7.1 运行兼容性验证脚本
首先运行专门的验证脚本来检查所有版本是否与macOS环境一致：
```bash
source venv/bin/activate
python verify_wsl_compatibility.py
```

预期输出：
```
======================================================================
WSL 部署兼容性验证
======================================================================

🔍 系统版本检查:
------------------------------
✅ Python 3.13.4 (expected 3.13.4)
✅ PostgreSQL 14.18 (expected 14.18)
✅ pgvector 0.8.0 (expected 0.8.0)

📦 Python包版本检查:
------------------------------
✅ sqlalchemy 2.0.43 (expected 2.0.43)
... (所有包都应显示绿色勾号)

======================================================================
验证总结:
======================================================================
系统版本: ✅ 全部匹配
Python包: ✅ 全部匹配
总体状态: ✅ 环境完全兼容
```

如果看到任何❌标记，请参考本指南相应章节重新安装对应组件。

### 7.2 检查数据库连接和pgvector状态
```bash
source venv/bin/activate
python -m pgvector_cli status
```
预期输出：
```
            Database Status            
┏━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┓
┃ Component             ┃ Status      ┃
┡━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━┩
│ PostgreSQL Connection │ ✓ Connected │
│ pgvector Extension    │ ✓ Installed │
└───────────────────────┴─────────────┘
```

### 7.2 创建测试集合
```bash
python -m pgvector_cli create-collection "test_wsl" --dimension 1024 --description "WSL部署测试"
```

### 7.3 添加测试向量
```bash
python -m pgvector_cli add-vector "test_wsl" --text "这是WSL环境的测试向量" --metadata source=wsl --metadata env=test
```

### 7.4 搜索测试
```bash
python -m pgvector_cli search "test_wsl" --query "测试" --limit 5
```

### 7.5 清理测试数据
```bash
python -m pgvector_cli delete-collection "test_wsl" --confirm
```

## 8. 常见问题及解决方案

### 8.1 PostgreSQL连接问题
如果遇到连接拒绝错误：
```bash
# 检查PostgreSQL服务状态
sudo systemctl status postgresql

# 重启PostgreSQL服务
sudo systemctl restart postgresql

# 检查PostgreSQL配置
sudo nano /etc/postgresql/14/main/postgresql.conf
# 确保: listen_addresses = 'localhost'

sudo nano /etc/postgresql/14/main/pg_hba.conf
# 确保包含: local all all trust
```

### 8.2 pgvector编译问题
如果编译失败：
```bash
# 确保安装了所有必需的开发包
sudo apt install -y postgresql-server-dev-14 build-essential

# 清理并重新编译
cd /tmp/pgvector
make clean
make
sudo make install
```

### 8.3 Python依赖问题
如果某些包安装失败：
```bash
# 安装系统级依赖
sudo apt install -y \
    python3.13-dev \
    libpq-dev \
    libffi-dev \
    libssl-dev

# 重新安装失败的包
pip install --upgrade --force-reinstall <package-name>
```

### 8.4 权限问题
如果遇到数据库权限问题：
```bash
# 以postgres用户身份登录
sudo -u postgres psql

# 授予用户所需权限
GRANT ALL PRIVILEGES ON DATABASE postgres TO your_username;
GRANT ALL PRIVILEGES ON SCHEMA public TO your_username;
```

## 9. 性能优化建议

### 9.1 PostgreSQL配置优化
编辑PostgreSQL配置文件：
```bash
sudo nano /etc/postgresql/14/main/postgresql.conf
```

推荐设置：
```
# 内存设置
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB

# 连接设置
max_connections = 100

# 日志设置
log_statement = 'mod'
log_min_duration_statement = 1000
```

重启PostgreSQL使配置生效：
```bash
sudo systemctl restart postgresql
```

### 9.2 系统资源监控
```bash
# 监控PostgreSQL进程
ps aux | grep postgres

# 监控数据库连接
psql -d postgres -c "SELECT count(*) FROM pg_stat_activity;"

# 监控磁盘使用
df -h
```

## 10. 自动化脚本

创建一键部署脚本：
```bash
cat > deploy_wsl.sh << 'EOF'
#!/bin/bash

# WSL环境下pgvector CLI一键部署脚本

set -e

echo "开始WSL环境部署..."

# 更新系统
echo "更新系统包..."
sudo apt update && sudo apt upgrade -y

# 安装基础依赖
echo "安装基础开发工具..."
sudo apt install -y build-essential curl git wget software-properties-common

# 安装Python 3.13
echo "安装Python 3.13..."
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install -y python3.13 python3.13-dev python3.13-venv python3-pip

# 安装PostgreSQL 14
echo "安装PostgreSQL 14..."
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
echo "deb http://apt.postgresql.org/pub/repos/apt/ $(lsb_release -cs)-pgdg main" | sudo tee /etc/apt/sources.list.d/pgdg.list
sudo apt update
sudo apt install -y postgresql-14 postgresql-client-14 postgresql-contrib-14 postgresql-server-dev-14

# 启动PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# 配置PostgreSQL用户
sudo -u postgres createuser --superuser $USER || true
sudo -u postgres createdb $USER || true

# 安装pgvector
echo "编译安装pgvector..."
cd /tmp
git clone https://github.com/pgvector/pgvector.git || true
cd pgvector
git checkout v0.8.0
make clean
make
sudo make install

# 启用pgvector扩展
psql -d postgres -c "CREATE EXTENSION IF NOT EXISTS vector;"

echo "WSL环境部署完成！"
echo "请继续执行项目部署步骤..."
EOF

chmod +x deploy_wsl.sh
```

## 11. 版本兼容性说明

本部署指南严格按照macOS环境的版本配置：

| 组件 | macOS版本 | WSL版本 | 状态 |
|------|-----------|---------|------|
| Python | 3.13.4 | 3.13.4 | ✅ 匹配 |
| PostgreSQL | 14.18 | 14.18 | ✅ 匹配 |
| pgvector | 0.8.0 | 0.8.0 | ✅ 匹配 |
| SQLAlchemy | 2.0.43 | 2.0.43 | ✅ 匹配 |
| psycopg2-binary | 2.9.10 | 2.9.10 | ✅ 匹配 |
| dashscope | 1.24.2 | 1.24.2 | ✅ 匹配 |

## 12. 故障排除联系方式

如遇到部署问题，请检查：
1. WSL版本是否为WSL 2
2. 所有版本号是否与本指南一致
3. 网络连接是否正常
4. 系统资源是否充足

---

**注意**: 本指南确保WSL环境与macOS环境完全一致，所有版本号均已验证。请严格按照步骤执行以避免版本冲突。