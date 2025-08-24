# pgvector CLI

一个用于管理PostgreSQL向量集合的命令行工具，基于pgvector扩展。

## 功能特性

- **集合管理**: 创建、列出、重命名和删除向量集合
- **向量操作**: 添加向量和搜索相似内容
- **智能总结**: 基于搜索结果的AI智能总结功能 🤖
- **嵌入服务**: 集成阿里云DashScope text-embedding-v4模型
- **LLM集成**: 使用通义千问qwen-max提供智能分析
- **丰富输出**: 美观的表格和JSON格式输出
- **数据库集成**: 直接访问PostgreSQL pgvector数据库

## 快速开始

1. **安装依赖**:
   ```bash
   pip install -r requirements.txt
   pip install -e .
   
   # LLM总结功能需要额外依赖
   pip install openai socksio
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
   
   # DashScope Configuration (阿里云) - 用于嵌入和LLM服务
   DASHSCOPE_API_KEY=your_dashscope_api_key_here
   DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
   ```

4. **🚀 快速体验AI总结功能**:
   ```bash
   # 创建测试集合
   python -m pgvector_cli create-collection demo --description "演示集合"
   
   # 添加示例内容
   python -m pgvector_cli add-vector demo --text "机器学习是人工智能的核心技术，通过算法让计算机从数据中学习"
   python -m pgvector_cli add-vector demo --text "深度学习是机器学习的子集，使用神经网络模型处理复杂问题"
   
   # 🤖 体验智能总结
   python -m pgvector_cli search demo --query "什么是机器学习" --summarize
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

# 🤖 AI智能总结搜索（新功能！）
python -m pgvector_cli search my_docs --query "什么是机器学习" --summarize

# 智能总结 + 限制结果数量
python -m pgvector_cli search my_docs --query "深度学习的应用" --summarize --limit 3

# 智能总结 + JSON格式输出
python -m pgvector_cli search my_docs --query "人工智能" --summarize --format json

# 不同精度级别的搜索
python -m pgvector_cli search my_docs --query "机器学习" --precision high --summarize
python -m pgvector_cli search my_docs --query "技术文档" --precision medium --limit 5
python -m pgvector_cli search my_docs --query "快速查询" --precision fast --limit 10
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

# 5. 🤖 使用AI智能总结
python -m pgvector_cli search documents --query "什么是机器学习" --summarize

# 6. 查看集合统计
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

### 🤖 AI智能总结示例
```bash
# 创建知识库集合
python -m pgvector_cli create-collection knowledge_base --description "技术知识库"

# 添加技术文档
python -m pgvector_cli add-vector knowledge_base --text "React是一个用于构建用户界面的JavaScript库，由Facebook开发维护"
python -m pgvector_cli add-vector knowledge_base --text "Vue.js是渐进式JavaScript框架，易于学习和集成到现有项目中"
python -m pgvector_cli add-vector knowledge_base --text "Angular是由Google开发的全功能Web应用框架，使用TypeScript编写"

# 🔍 智能问答：获得基于文档内容的总结回答
python -m pgvector_cli search knowledge_base --query "前端框架有哪些特点" --summarize

# 🎯 精确总结：严格基于搜索内容回答，不依赖AI的通用知识
python -m pgvector_cli search knowledge_base --query "React和Vue的区别" --summarize --limit 2

# 📊 JSON格式的智能总结输出（便于程序处理）
python -m pgvector_cli search knowledge_base --query "JavaScript框架对比" --summarize --format json

# 🚀 高精度搜索 + 智能总结
python -m pgvector_cli search knowledge_base --query "哪个框架更适合新项目" --precision high --summarize
```

### JSON处理示例
```bash
# 导出集合列表到JSON文件
python -m pgvector_cli list-collections --format json > collections.json

# 常规搜索结果处理（需要jq工具）
python -m pgvector_cli search my_docs --query "搜索词" --format json | jq '.results[] | .content'

# 🤖 提取AI智能总结内容
python -m pgvector_cli search my_docs --query "问题" --summarize --format json | jq '.ai_summary'

# 🔍 同时获取总结和搜索结果
python -m pgvector_cli search my_docs --query "关键词" --summarize --format json | jq '{summary: .ai_summary, top_result: .results[0].content}'

# 提取高相似度结果（注意JSON结构变化）
python -m pgvector_cli search my_docs --query "关键词" --format json | jq '.results[] | select(.similarity_score > 0.8)'

# 批量智能总结处理
python -m pgvector_cli search my_docs --query "技术问题" --summarize --format json > summary_output.json

# 统计集合数量
python -m pgvector_cli list-collections --format json | jq length
```

## 输出格式

### 表格格式 (默认)
- 美观的表格显示
- 适合命令行查看
- 自动调整列宽
- 🤖 智能总结显示为独立的蓝色边框面板

### JSON格式
- 结构化数据输出
- 适合脚本处理
- 便于集成其他工具
- 🤖 智能总结包含在 `ai_summary` 字段中
- 搜索结果在 `results` 数组中，保持原有结构

### 智能总结特性
- **严格基于文档**: 仅基于搜索结果内容回答，不使用LLM通用知识
- **结构化回答**: 包含要点总结和详细说明
- **来源标注**: 标注信息来源和相似度得分
- **优雅降级**: LLM服务不可用时不影响普通搜索功能
- **Token优化**: 自动限制处理结果数量，控制API成本

## 环境要求

- **Python**: 3.8+ (推荐3.11+)
- **PostgreSQL**: 12+ 需启用pgvector扩展
- **阿里云DashScope**: API密钥用于文本嵌入和LLM智能总结
- **网络环境**: 支持访问阿里云API（LLM功能需要）
- **系统权限**: 数据库创建表权限
- **依赖库**: openai, socksio (用于LLM功能)

## 完整文档

详细配置和开发文档请参阅 [CLAUDE.md](CLAUDE.md)