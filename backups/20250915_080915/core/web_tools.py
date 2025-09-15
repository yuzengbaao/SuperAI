#!/usr/bin/env python3
"""
网络搜索工具模块

为多智能体协作系统提供网络搜索能力，支持实时信息获取和知识边界突破。
使用Tavily API作为主要搜索服务，提供为AI优化的搜索结果。
"""

import os
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import logging
import certifi

from .tools import BaseTool, ToolResult, ToolStatus

# 配置日志
logger = logging.getLogger(__name__)

# 尝试导入TavilyClient并处理可能的ImportError
try:
    from tavily import TavilyClient
except ImportError:
    TavilyClient = None
    logger.warning("Tavily库未安装，WebSearchTool将不可用。请运行: pip install tavily-python")

class WebSearchTool(BaseTool):
    """
    通用网络搜索工具，集成Tavily API。
    """
    
    def __init__(self, api_key: Optional[str] = None, max_results: int = 5, cache_ttl: int = 3600):
        """
        初始化网络搜索工具。
        
        Args:
            api_key (Optional[str]): Tavily API密钥。如果为None，则从环境变量'TAVILY_API_KEY'读取。
            max_results (int): 默认的最大搜索结果数量。
            cache_ttl (int): 缓存生存时间（秒）。
        """
        super().__init__(
            name="web_search",
            description="执行网络搜索以获取实时信息或知识。",
            version="1.2.0"
        )
        
        self.api_key = api_key or os.getenv('TAVILY_API_KEY')
        self.max_results = max_results
        self.cache_ttl = cache_ttl
        
        self.permissions.add('web_access')
        self.permissions.add('external_api')
        
        self.tavily_client: Optional[TavilyClient] = None
        if self.api_key and TavilyClient:
            try:
                # TavilyClient/requests会自动使用certifi，无需手动配置SSL上下文
                self.tavily_client = TavilyClient(api_key=self.api_key)
                logger.info(f"Tavily客户端初始化成功。使用Certifi CA bundle: {certifi.where()}")
            except Exception as e:
                logger.error(f"Tavily客户端初始化失败: {e}")
        elif not self.api_key:
            logger.warning("Tavily API密钥未设置，搜索功能将不可用。")

        self.search_cache: Dict[str, Any] = {}
        
        self.supported_operations = {
            'search': self._search,
            'get_page_content': self._get_page_content
        }
    
    def validate_params(self, params: Dict[str, Any]) -> bool:
        """验证输入参数的有效性。"""
        if not isinstance(params, dict):
            return False
        
        operation = params.get('operation', 'search')
        if operation not in self.supported_operations:
            return False
        
        if operation == 'get_page_content':
            return 'url' in params and isinstance(params['url'], str) and bool(params['url'].strip())
        else:
            return 'query' in params and isinstance(params['query'], str) and bool(params['query'].strip())
    
    def execute(self, params: Dict[str, Any]) -> ToolResult:
        """执行指定的搜索操作。"""
        if not self.tavily_client:
            msg = "Tavily搜索服务未初始化。请检查TAVILY_API_KEY和tavily-python库。"
            logger.error(msg)
            return ToolResult(status=ToolStatus.ERROR, error=msg)

        operation = params.get('operation', 'search')
        operation_func = self.supported_operations.get(operation)

        if not operation_func:
            return ToolResult(status=ToolStatus.ERROR, error=f"不支持的操作: {operation}")
            
        try:
            result = operation_func(params)
            return ToolResult(
                status=ToolStatus.SUCCESS,
                data=result,
                metadata={"operation": operation, "tool": self.name}
            )
        except Exception as e:
            logger.error(f"网络搜索操作 '{operation}' 失败: {e}", exc_info=True)
            return ToolResult(status=ToolStatus.ERROR, error=f"网络搜索失败: {str(e)}")
    
    def _get_cache_key(self, text: str, operation: str) -> str:
        """为给定的操作和文本生成MD5缓存键。"""
        return hashlib.md5(f"{operation}:{text}".encode()).hexdigest()
    
    def _get_cached_result(self, cache_key: str) -> Optional[Any]:
        """如果存在且未过期，则从缓存中检索结果。"""
        cached = self.search_cache.get(cache_key)
        if cached and (datetime.now() - cached['timestamp']) < timedelta(seconds=self.cache_ttl):
            logger.info(f"命中缓存: {cache_key}")
            return cached['result']
        if cache_key in self.search_cache:
            del self.search_cache[cache_key] # 删除过期缓存
        return None
    
    def _cache_result(self, cache_key: str, result: Any):
        """将结果存入缓存。"""
        if len(self.search_cache) > 100: # 简单缓存清理
            try:
                oldest_key = min(self.search_cache, key=lambda k: self.search_cache[k]['timestamp'])
                del self.search_cache[oldest_key]
            except (KeyError, ValueError):
                pass
        self.search_cache[cache_key] = {'result': result, 'timestamp': datetime.now()}
    
    def _search(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行通用搜索。"""
        # 再次检查客户端，以防在运行时出现问题
        if not self.tavily_client:
            raise RuntimeError("Tavily client not initialized")

        query = params['query'].strip()
        cache_key = self._get_cache_key(query, 'search')
        
        cached_result = self._get_cached_result(cache_key)
        if cached_result is not None:
            return cached_result
        
        logger.info(f"执行Tavily搜索: {query}")
        
        search_params = {
            'query': query,
            'max_results': params.get('max_results', self.max_results),
            'search_depth': 'basic',
            'include_answer': True,
        }
        
        response = self.tavily_client.search(**search_params)
        
        processed_results = self._process_search_results(response, query)
        self._cache_result(cache_key, processed_results)
        return processed_results
            
    def _get_page_content(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """获取并返回单个URL的内容。"""
        # 再次检查客户端
        if not self.tavily_client:
            raise RuntimeError("Tavily client not initialized")

        url = params['url'].strip()
        logger.info(f"使用Tavily提取网页内容: {url}")
        
        # Tavily的get_content返回一个字符串列表
        response_list = self.tavily_client.get_content(urls=[url])
        
        if response_list and isinstance(response_list, list) and response_list[0]:
            return {"url": url, "content": response_list[0]}
        else:
            raise ValueError(f"无法从URL提取内容: {url}")
    
    def _process_search_results(self, response: Dict[str, Any], query: str) -> Dict[str, Any]:
        """将Tavily的原始搜索结果处理为标准格式。"""
        results = [
            {
                "title": item.get('title', ''),
                "url": item.get('url', ''),
                "content": item.get('content', ''),
                "score": item.get('score', 0),
                "source": self._extract_domain(item.get('url', ''))
            }
            for item in response.get('results', [])
        ]
        
        return {
            "query": query,
            "total_results": len(results),
            "results": results,
            "answer": response.get('answer', ''),
        }
    
    def _extract_domain(self, url: str) -> str:
        """从URL中安全地提取域名。"""
        if not url: return ""
        try:
            from urllib.parse import urlparse
            return urlparse(url).netloc
        except Exception:
            return url

def _register_web_tools():
    """将WebSearchTool注册到全局工具注册中心。"""
    from .tools import get_global_registry
    registry = get_global_registry()
    if TavilyClient:
        registry.register_tool(WebSearchTool(), "web_search")
        print("🌐 [WebTools] 网络搜索工具(WebSearchTool)注册完成。")
    else:
        print("⚠️ [WebTools] Tavily库未安装，无法注册网络搜索工具。")

# 模块加载时自动注册
_register_web_tools()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - [%(levelname)s] - %(message)s')
    
    print("🌐 网络搜索工具测试")
    print("=" * 50)
    
    api_key = os.getenv('TAVILY_API_KEY')
    if not api_key:
        print("⚠️ 警告: TAVILY_API_KEY环境变量未设置。测试将跳过。")
    elif not TavilyClient:
        print("⚠️ 警告: tavily-python库未安装。测试将跳过。")
    else:
        print(f"✅ API密钥已配置: {api_key[:8]}...")
        search_tool = WebSearchTool()
        
        print("\n🔍 测试网络搜索:")
        search_result = search_tool.execute({
            "operation": "search",
            "query": "What are the new features in Python 3.12?",
            "max_results": 3
        })
        
        if search_result.status == ToolStatus.SUCCESS:
            print(f"搜索成功: {json.dumps(search_result.to_dict(), indent=2, ensure_ascii=False)}")
        else:
            print(f"搜索失败: {search_result.error}")
    
    print("\n✅ 网络搜索工具测试完成。")