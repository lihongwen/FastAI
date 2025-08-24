# WSL部署检查清单

本检查清单确保WSL环境与macOS生产环境完全一致。请逐项核查每个步骤。

## 📋 部署前检查清单

### ✅ 系统准备
- [ ] WSL 2 已正确安装 (Ubuntu 22.04 LTS)
- [ ] 系统已更新到最新版本
- [ ] 基础开发工具已安装 (build-essential, git, curl, wget)

### ✅ Python 环境
- [ ] Python 3.13.4 已安装 (`python3.13 --version`)
- [ ] Python 3.13.4 已设为默认版本
- [ ] python3.13-dev 和 python3.13-venv 已安装
- [ ] 虚拟环境创建成功 (`python3.13 -m venv venv`)

### ✅ PostgreSQL 数据库
- [ ] PostgreSQL 14.18 已安装 (`psql --version`)
- [ ] PostgreSQL 服务已启动并开机自启
- [ ] 数据库用户已创建并有适当权限
- [ ] 可以正常连接到数据库

### ✅ pgvector 扩展
- [ ] postgresql-server-dev-14 已安装
- [ ] pgvector 源码已下载 (v0.8.0)
- [ ] pgvector 编译安装成功
- [ ] pgvector 扩展已在数据库中启用
- [ ] pgvector 版本为 0.8.0 (`SELECT * FROM pg_extension WHERE extname = 'vector';`)

## 📋 部署过程检查清单

### ✅ 项目安装
- [ ] 项目代码已克隆到WSL环境
- [ ] 虚拟环境已激活
- [ ] requirements.txt 中的所有依赖已安装
- [ ] 项目包已安装 (`pip install -e .`)

### ✅ 环境配置
- [ ] .env 文件已创建
- [ ] DATABASE_URL 配置正确
- [ ] DASHSCOPE_API_KEY 已设置 (如需要)
- [ ] 其他必要环境变量已配置

## 📋 功能验证检查清单

### ✅ 兼容性验证
- [ ] `python verify_wsl_compatibility.py` 执行成功
- [ ] 所有系统版本显示 ✅ (Python, PostgreSQL, pgvector)
- [ ] 所有Python包版本显示 ✅
- [ ] 总体状态显示 "环境完全兼容"

### ✅ 基础功能测试
- [ ] `python -m pgvector_cli status` 显示所有组件正常
- [ ] 可以创建测试集合
- [ ] 可以添加向量到集合
- [ ] 可以搜索向量
- [ ] 可以删除集合

### ✅ 高级功能测试
- [ ] 文档处理功能正常 (PDF, TXT, CSV)
- [ ] AI摘要功能正常 (如配置了API)
- [ ] 批量操作功能正常
- [ ] 索引重建功能正常

## 📋 版本对比检查清单

以下版本必须与macOS环境完全一致：

### 系统组件版本
- [ ] Python: 3.13.4 ✓
- [ ] PostgreSQL: 14.18 ✓  
- [ ] pgvector Extension: 0.8.0 ✓

### 核心依赖版本
- [ ] sqlalchemy: 2.0.43 ✓
- [ ] psycopg2-binary: 2.9.10 ✓
- [ ] pgvector: 0.4.1 ✓
- [ ] python-dotenv: 1.1.1 ✓

### 数据模型版本
- [ ] pydantic: 2.11.7 ✓
- [ ] pydantic-settings: 2.10.1 ✓

### CLI和UI版本
- [ ] click: 8.2.1 ✓
- [ ] rich: 14.1.0 ✓
- [ ] tabulate: 0.9.0 ✓

### AI服务版本
- [ ] dashscope: 1.24.2 ✓
- [ ] openai: 1.101.0 ✓
- [ ] numpy: 2.3.2 ✓

### 网络库版本
- [ ] httpx: 0.28.1 ✓
- [ ] socksio: 1.0.0 ✓

### 文档处理版本
- [ ] pymupdf4llm: 0.0.27 ✓
- [ ] python-docx: 1.2.0 ✓
- [ ] openpyxl: 3.1.5 ✓
- [ ] python-pptx: 1.0.2 ✓
- [ ] pandas: 2.3.2 ✓
- [ ] chardet: 5.2.0 ✓
- [ ] langchain-text-splitters: 0.3.9 ✓

### 开发工具版本
- [ ] pytest: 8.4.1 ✓
- [ ] pytest-cov: 6.2.1 ✓
- [ ] pytest-mock: 3.14.1 ✓
- [ ] ruff: 0.12.10 ✓
- [ ] mypy: 1.17.1 ✓

## 📋 性能验证检查清单

### ✅ 数据库性能
- [ ] 向量索引创建速度正常
- [ ] 向量搜索响应时间 < 100ms (1000条记录)
- [ ] 批量插入性能正常
- [ ] 数据库连接池正常

### ✅ 内存和CPU
- [ ] 空闲内存使用 < 500MB
- [ ] 处理大文档时内存使用合理
- [ ] CPU使用率在正常范围内
- [ ] 无内存泄漏

## 📋 部署后维护检查清单

### ✅ 监控设置
- [ ] PostgreSQL 日志配置正确
- [ ] 应用日志级别适当
- [ ] 磁盘空间监控
- [ ] 数据库备份策略

### ✅ 安全配置
- [ ] 数据库用户权限最小化
- [ ] API密钥安全存储
- [ ] 网络访问控制
- [ ] 系统更新策略

## 🚨 故障排查检查清单

如果遇到问题，请按以下顺序检查：

### 连接问题
- [ ] PostgreSQL 服务状态 (`sudo systemctl status postgresql`)
- [ ] 端口占用情况 (`netstat -tlnp | grep 5432`)
- [ ] 防火墙设置
- [ ] 数据库用户权限

### 版本冲突
- [ ] 运行 `python verify_wsl_compatibility.py`
- [ ] 检查虚拟环境是否正确激活
- [ ] 确认 pip 版本和包源
- [ ] 清理并重新安装有问题的包

### 性能问题  
- [ ] 检查系统资源使用情况
- [ ] 优化 PostgreSQL 配置
- [ ] 检查索引状态
- [ ] 调整批处理大小

## ✅ 最终确认

部署完成后，请确认以下所有项目：

- [ ] 所有检查清单项目都已完成 ✅
- [ ] 兼容性验证脚本通过 ✅
- [ ] 基础功能测试通过 ✅
- [ ] 性能满足预期 ✅
- [ ] 生产环境就绪 ✅

---

**部署确认签名:**
- 部署日期: ___________
- 部署人员: ___________
- 验证人员: ___________

**环境信息记录:**
- WSL版本: ___________
- Ubuntu版本: ___________
- 硬件配置: ___________