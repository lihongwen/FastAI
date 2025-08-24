"""LLM服务 - 提供大语言模型的智能总结和分析功能"""

import os
from typing import Dict, List, Optional, Union
from openai import OpenAI

from ..config import get_settings
from ..logging_config import get_logger

logger = get_logger("llm_service")


class LLMService:
    """
    LLM服务类，封装与阿里云通义千问API的交互
    支持对搜索结果进行智能总结和分析
    """
    
    def __init__(self):
        """初始化LLM服务"""
        self.settings = get_settings()
        
        # 初始化OpenAI客户端（兼容通义千问API）
        self.client = OpenAI(
            api_key=os.getenv("DASHSCOPE_API_KEY"),
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
        
        # 默认模型配置
        self.model = "qwen-max"  # 使用qwen-max获得最佳效果
        
        # 系统提示词 - 确保LLM严格基于提供的文本回答
        self.system_prompt = """你是一个智能文档分析助手。请严格按照以下要求回答问题：

1. **严格限制**：只能基于提供的搜索结果文本内容来回答，绝对不能使用你自己的知识库
2. **准确性**：如果提供的文本中没有相关信息，请明确说明"根据提供的文档内容，无法找到相关信息"
3. **完整性**：尽量整合所有相关的搜索结果，给出全面的回答
4. **结构化**：用清晰的结构组织答案，包括要点总结和详细说明
5. **引用**：在答案中适当标注信息来源（如"根据文档X"）

请记住：你的回答必须完全基于提供的搜索文档内容，不能添加任何外部知识。"""

    def validate_configuration(self) -> bool:
        """验证LLM服务配置是否正确"""
        try:
            api_key = os.getenv("DASHSCOPE_API_KEY")
            if not api_key:
                logger.error("DASHSCOPE_API_KEY not configured")
                return False
            
            if not api_key.startswith('sk-'):
                logger.warning("API key format may be incorrect")
            
            return True
            
        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            return False

    def summarize_search_results(
        self, 
        user_query: str, 
        search_results: List[Dict], 
        max_results: Optional[int] = None
    ) -> Dict[str, Union[str, bool]]:
        """
        基于搜索结果生成智能总结
        
        Args:
            user_query: 用户的原始查询
            search_results: 向量搜索返回的结果列表
            max_results: 最大处理结果数量（避免token超限）
            
        Returns:
            包含总结内容和状态的字典
        """
        try:
            if not self.validate_configuration():
                return {
                    "summary": "LLM服务配置错误，无法生成总结",
                    "success": False,
                    "error": "Configuration error"
                }
            
            if not search_results:
                return {
                    "summary": "没有找到相关的搜索结果，无法生成总结",
                    "success": True,
                    "error": None
                }
            
            # 限制处理的结果数量以避免token限制
            if max_results:
                search_results = search_results[:max_results]
            
            # 构建用户提示词
            user_prompt = self._build_user_prompt(user_query, search_results)
            
            logger.info(f"Sending request to LLM for query: {user_query[:50]}...")
            
            # 调用LLM API
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {'role': 'system', 'content': self.system_prompt},
                    {'role': 'user', 'content': user_prompt}
                ],
                stream=False,  # 简化处理，不使用流式输出
                temperature=0.1,  # 低温度确保一致性
                max_tokens=2000   # 限制响应长度
            )
            
            summary = completion.choices[0].message.content.strip()
            
            logger.info("LLM summary generated successfully")
            
            return {
                "summary": summary,
                "success": True,
                "error": None,
                "token_usage": {
                    "prompt_tokens": completion.usage.prompt_tokens if completion.usage else 0,
                    "completion_tokens": completion.usage.completion_tokens if completion.usage else 0,
                    "total_tokens": completion.usage.total_tokens if completion.usage else 0
                }
            }
            
        except Exception as e:
            error_msg = f"LLM API调用失败: {str(e)}"
            logger.error(error_msg, exc_info=True)
            
            return {
                "summary": f"生成总结时发生错误: {error_msg}",
                "success": False,
                "error": str(e)
            }

    def _build_user_prompt(self, user_query: str, search_results: List[Dict]) -> str:
        """构建发送给LLM的用户提示词"""
        
        # LLM API限制：输入长度应在[1, 30720]范围内，我们留一些缓冲
        MAX_PROMPT_LENGTH = 28000
        
        # 构建文档内容部分
        documents_text = ""
        total_length = len(user_query) + 500  # 预留查询和模板文本的长度
        
        for i, result in enumerate(search_results, 1):
            content = result.get('content', '')
            similarity = result.get('similarity_score', 0)
            metadata = result.get('metadata', {})
            
            # 获取文档来源信息
            source_info = ""
            if isinstance(metadata, dict):
                if 'source_file' in metadata:
                    source_info = f"[来源: {metadata['source_file']}]"
                elif 'chunk_index' in metadata:
                    source_info = f"[文档片段 {metadata['chunk_index']}]"
            
            # 构建这个文档的文本
            doc_text = f"""
文档 {i} {source_info}（相似度: {similarity:.3f}）:
{content}

---
"""
            
            # 检查加入这个文档后是否会超过长度限制
            if total_length + len(doc_text) > MAX_PROMPT_LENGTH:
                logger.warning(f"Prompt too long, truncating at document {i-1}")
                break
            
            documents_text += doc_text
            total_length += len(doc_text)
        
        # 构建完整的用户提示词
        user_prompt = f"""用户查询: {user_query}

基于以下搜索到的文档内容，请回答用户的问题：

{documents_text}

请基于以上文档内容回答用户的问题。记住：
1. 只能使用提供的文档内容
2. 如果文档中没有相关信息，请明确说明
3. 整合多个文档的信息给出完整回答
4. 保持客观和准确"""

        # 最终安全检查
        if len(user_prompt) > MAX_PROMPT_LENGTH:
            logger.warning("Prompt still too long, force truncating")
            user_prompt = user_prompt[:MAX_PROMPT_LENGTH]

        return user_prompt

    def get_model_info(self) -> Dict[str, str]:
        """获取当前使用的模型信息"""
        return {
            "model": self.model,
            "provider": "阿里云通义千问",
            "api_base": "https://dashscope.aliyuncs.com/compatible-mode/v1"
        }