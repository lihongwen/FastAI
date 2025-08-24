# pgvector CLI

一个用于管理PostgreSQL向量集合的命令行工具，基于pgvector扩展。

## 功能特性

- **集合管理**: 创建、列出、重命名和删除向量集合
- **向量操作**: 添加向量和搜索相似内容
- **嵌入服务**: 集成阿里云DashScope text-embedding-v4模型
- **丰富输出**: 美观的表格和JSON格式输出
- **数据库集成**: 直接访问PostgreSQL pgvector数据库

## 快速开始

1. **安装依赖**:
   ```bash
   pip install -r requirements.txt
   pip install -e .
   ```

2. **设置数据库**:
   ```bash
   psql postgres -c "CREATE EXTENSION IF NOT EXISTS vector;"
   ```

3. **配置环境变量** (创建.env文件):
   ```bash
   # Database Configuration
   DATABASE_URL=postgresql://lihongwen@localhost:5432/postgres
   
   # Application Settings
   DEBUG=false
   
   # DashScope Embedding Service Configuration (阿里云)
   DASHSCOPE_API_KEY=your_dashscope_api_key_here
   DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
   ```

## 完整命令参考

### 系统状态
```bash
# 检查数据库连接和pgvector扩展状态
python -m pgvector_cli status
```

### 集合管理命令

#### 创建集合
```bash
# 创建新集合（默认1536维度）
python -m pgvector_cli create-collection my_docs

# 指定维度和描述
python -m pgvector_cli create-collection my_docs --dimension 1024 --description "文档嵌入集合"

# 简写参数
python -m pgvector_cli create-collection articles -d 1536 --description "文章集合"
```

#### 列出集合
```bash
# 表格格式列出所有集合
python -m pgvector_cli list-collections

# JSON格式输出
python -m pgvector_cli list-collections --format json

# 表格格式（默认）
python -m pgvector_cli list-collections --format table
```

#### 查看集合详情
```bash
# 查看集合基本信息
python -m pgvector_cli show-collection my_docs

# 显示集合统计信息
python -m pgvector_cli show-collection my_docs --stats
```

#### 重命名集合
```bash
# 重命名集合
python -m pgvector_cli rename-collection old_name new_name
```

#### 删除集合
```bash
# 删除集合（需要确认）
python -m pgvector_cli delete-collection my_docs

# 跳过确认直接删除
python -m pgvector_cli delete-collection my_docs --confirm
```

### 向量操作命令

#### 添加向量
```bash
# 添加单个向量
python -m pgvector_cli add-vector my_docs --text "这是一个示例文档"

# 添加带元数据的向量
python -m pgvector_cli add-vector my_docs --text "技术文档" --metadata source=manual --metadata type=doc

# 添加多个元数据
python -m pgvector_cli add-vector my_docs \
  --text "人工智能相关内容" \
  --metadata category=AI \
  --metadata author=张三 \
  --metadata date=2024-01-01
```

#### 搜索向量
```bash
# 基本搜索
python -m pgvector_cli search my_docs --query "示例文档"

# 限制结果数量
python -m pgvector_cli search my_docs --query "技术" --limit 5

# JSON格式输出
python -m pgvector_cli search my_docs --query "人工智能" --format json

# 表格格式输出（默认）
python -m pgvector_cli search my_docs --query "机器学习" --format table --limit 10
```

## 使用示例

### 基础工作流程
```bash
# 1. 检查系统状态
python -m pgvector_cli status

# 2. 创建文档集合
python -m pgvector_cli create-collection documents --description "文档知识库"

# 3. 添加文档
python -m pgvector_cli add-vector documents --text "机器学习是人工智能的重要分支" --metadata type=knowledge
python -m pgvector_cli add-vector documents --text "深度学习使用神经网络进行学习" --metadata type=knowledge
python -m pgvector_cli add-vector documents --text "自然语言处理处理文本数据" --metadata type=knowledge

# 4. 搜索相关内容
python -m pgvector_cli search documents --query "深度学习" --limit 3

# 5. 查看集合统计
python -m pgvector_cli show-collection documents --stats
```

### 批量操作示例
```bash
# 创建多个专题集合
python -m pgvector_cli create-collection tech_docs --description "技术文档"
python -m pgvector_cli create-collection research_papers --description "研究论文"
python -m pgvector_cli create-collection meeting_notes --description "会议记录"

# 列出所有集合
python -m pgvector_cli list-collections

# 在不同集合中搜索
python -m pgvector_cli search tech_docs --query "API设计"
python -m pgvector_cli search research_papers --query "机器学习算法"
python -m pgvector_cli search meeting_notes --query "项目进展"
```

### JSON处理示例
```bash
# 导出集合列表到JSON文件
python -m pgvector_cli list-collections --format json > collections.json

# 搜索结果处理（需要jq工具）
python -m pgvector_cli search my_docs --query "搜索词" --format json | jq '.[] | .content'

# 提取高相似度结果
python -m pgvector_cli search my_docs --query "关键词" --format json | jq '.[] | select(.similarity_score > 0.8)'

# 统计集合数量
python -m pgvector_cli list-collections --format json | jq length
```

## 输出格式

### 表格格式 (默认)
- 美观的表格显示
- 适合命令行查看
- 自动调整列宽

### JSON格式
- 结构化数据输出
- 适合脚本处理
- 便于集成其他工具

## 环境要求

- **Python**: 3.8+ (推荐3.11+)
- **PostgreSQL**: 12+ 需启用pgvector扩展
- **阿里云DashScope**: API密钥用于文本嵌入
- **系统权限**: 数据库创建表权限

## 完整文档

详细配置和开发文档请参阅 [CLAUDE.md](CLAUDE.md)