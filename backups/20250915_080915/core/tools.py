#!/usr/bin/env python3
"""
多智能体协作系统 - 工具生态系统核心模块

本模块定义了智能体工具系统的核心接口和管理机制，为多智能体协作系统
提供标准化的工具集成能力。

核心组件:
- BaseTool: 所有工具的抽象基类
- ToolRegistry: 工具注册和管理中心
- ToolExecutor: 工具执行引擎
- ToolResult: 标准化的工具执行结果

设计原则:
1. 标准化接口: 所有工具遵循统一的执行接口
2. 动态注册: 支持运行时动态加载和注册工具
3. 类型安全: 强类型的参数验证和结果返回
4. 错误处理: 完善的异常处理和错误报告
5. 可扩展性: 支持插件式的工具扩展
"""

import abc
import json
import logging
import traceback
import os
from datetime import datetime
from typing import Dict, Any, Optional, List, Type, Union
from dataclasses import dataclass, asdict
from enum import Enum
from tavily import TavilyClient

# 配置日志
logger = logging.getLogger(__name__)

class ToolStatus(Enum):
    """工具执行状态枚举"""
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
    PERMISSION_DENIED = "permission_denied"
    NOT_FOUND = "not_found"

@dataclass
class ToolResult:
    """
    标准化的工具执行结果
    
    Attributes:
        status: 执行状态
        data: 执行结果数据
        error: 错误信息（如果有）
        execution_time: 执行耗时（秒）
        metadata: 额外的元数据
    """
    status: ToolStatus
    data: Any = None
    error: Optional[str] = None
    execution_time: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None
    timestamp: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        result = asdict(self)
        result['status'] = self.status.value
        return result
    
    def is_success(self) -> bool:
        """检查执行是否成功"""
        return self.status == ToolStatus.SUCCESS
    
    def is_error(self) -> bool:
        """检查是否有错误"""
        return self.status == ToolStatus.ERROR

class BaseTool(abc.ABC):
    """
    智能体工具的抽象基类
    
    所有智能体工具都必须继承此类并实现execute方法。
    这确保了所有工具都有统一的接口和行为。
    """
    
    def __init__(self, name: str, description: str = "", version: str = "1.0.0"):
        """
        初始化工具
        
        Args:
            name: 工具名称，必须唯一
            description: 工具描述
            version: 工具版本
        """
        self.name = name
        self.description = description
        self.version = version
        self.enabled = True
        self.permissions = set()
        self.config = {}
        
        # 执行统计
        self.execution_count = 0
        self.success_count = 0
        self.error_count = 0
        self.total_execution_time = 0.0
    
    @abc.abstractmethod
    def execute(self, params: Dict[str, Any]) -> ToolResult:
        """
        执行工具的核心方法
        
        Args:
            params: 工具执行参数
            
        Returns:
            ToolResult: 标准化的执行结果
            
        Raises:
            NotImplementedError: 子类必须实现此方法
        """
        raise NotImplementedError("子类必须实现execute方法")
    
    def validate_params(self, params: Dict[str, Any]) -> bool:
        """
        验证输入参数
        
        Args:
            params: 待验证的参数
            
        Returns:
            bool: 参数是否有效
        """
        # 默认实现，子类可以重写
        return isinstance(params, dict)
    
    def get_required_permissions(self) -> List[str]:
        """
        获取工具所需的权限列表
        
        Returns:
            List[str]: 权限列表
        """
        return list(self.permissions)
    
    def configure(self, config: Dict[str, Any]) -> None:
        """
        配置工具
        
        Args:
            config: 配置参数
        """
        self.config.update(config)
    
    def get_info(self) -> Dict[str, Any]:
        """
        获取工具信息
        
        Returns:
            Dict[str, Any]: 工具信息
        """
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "enabled": self.enabled,
            "permissions": list(self.permissions),
            "execution_count": self.execution_count,
            "success_count": self.success_count,
            "error_count": self.error_count,
            "success_rate": self.success_count / max(self.execution_count, 1),
            "average_execution_time": self.total_execution_time / max(self.execution_count, 1)
        }
    
    def _update_stats(self, result: ToolResult) -> None:
        """
        更新执行统计
        
        Args:
            result: 执行结果
        """
        self.execution_count += 1
        if result.is_success():
            self.success_count += 1
        else:
            self.error_count += 1
        
        if result.execution_time:
            self.total_execution_time += result.execution_time
    
    def __str__(self) -> str:
        return f"Tool({self.name}, v{self.version})"
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name='{self.name}', version='{self.version}')>"

class ToolRegistry:
    """
    工具注册和管理中心
    
    负责工具的注册、发现、加载和管理。支持动态注册和运行时工具管理。
    """
    
    def __init__(self):
        """
        初始化工具注册中心
        """
        self._tools: Dict[str, BaseTool] = {}
        self._tool_classes: Dict[str, Type[BaseTool]] = {}
        self._categories: Dict[str, List[str]] = {}
        self.logger = logging.getLogger(f"{__name__}.ToolRegistry")
        
        self.logger.info("🔧 [ToolRegistry] 工具注册中心初始化完成")
    
    def register_tool(self, tool: BaseTool, category: str = "general") -> bool:
        """
        注册工具实例
        
        Args:
            tool: 工具实例
            category: 工具分类
            
        Returns:
            bool: 注册是否成功
        """
        if not isinstance(tool, BaseTool):
            self.logger.error(f"❌ [ToolRegistry] 工具必须继承BaseTool: {type(tool)}")
            return False
        
        if tool.name in self._tools:
            self.logger.warning(f"⚠️ [ToolRegistry] 工具已存在，将被覆盖: {tool.name}")
        
        self._tools[tool.name] = tool
        
        # 添加到分类
        if category not in self._categories:
            self._categories[category] = []
        if tool.name not in self._categories[category]:
            self._categories[category].append(tool.name)
        
        self.logger.info(f"✅ [ToolRegistry] 工具注册成功: {tool.name} (分类: {category})")
        return True
    
    def register_tool_class(self, tool_class: Type[BaseTool], name: str = None) -> bool:
        """
        注册工具类（延迟实例化）
        
        Args:
            tool_class: 工具类
            name: 工具名称（可选，默认使用类名）
            
        Returns:
            bool: 注册是否成功
        """
        if not issubclass(tool_class, BaseTool):
            self.logger.error(f"❌ [ToolRegistry] 工具类必须继承BaseTool: {tool_class}")
            return False
        
        tool_name = name or tool_class.__name__.lower().replace('tool', '')
        self._tool_classes[tool_name] = tool_class
        
        self.logger.info(f"✅ [ToolRegistry] 工具类注册成功: {tool_name} -> {tool_class.__name__}")
        return True
    
    def get_tool(self, name: str) -> Optional[BaseTool]:
        """
        获取工具实例
        
        Args:
            name: 工具名称
            
        Returns:
            Optional[BaseTool]: 工具实例，如果不存在则返回None
        """
        tool = self._tools.get(name)
        if tool:
            return tool
        
        # 尝试从工具类创建实例
        tool_class = self._tool_classes.get(name)
        if tool_class:
            try:
                tool_instance = tool_class(name=name)
                self.register_tool(tool_instance)
                return tool_instance
            except Exception as e:
                self.logger.error(f"❌ [ToolRegistry] 创建工具实例失败: {name}, 错误: {e}")
        
        return None
    
    def list_tools(self, category: str = None, enabled_only: bool = True) -> List[str]:
        """
        列出所有工具
        
        Args:
            category: 工具分类过滤
            enabled_only: 是否只返回启用的工具
            
        Returns:
            List[str]: 工具名称列表
        """
        if category:
            tools = self._categories.get(category, [])
        else:
            tools = list(self._tools.keys())
        
        if enabled_only:
            tools = [name for name in tools 
                    if name in self._tools and self._tools[name].enabled]
        
        return tools
    
    def get_tool_info(self, name: str) -> Optional[Dict[str, Any]]:
        """
        获取工具详细信息
        
        Args:
            name: 工具名称
            
        Returns:
            Optional[Dict[str, Any]]: 工具信息，如果不存在则返回None
        """
        tool = self.get_tool(name)
        return tool.get_info() if tool else None
    
    def enable_tool(self, name: str) -> bool:
        """
        启用工具
        
        Args:
            name: 工具名称
            
        Returns:
            bool: 操作是否成功
        """
        tool = self.get_tool(name)
        if tool:
            tool.enabled = True
            self.logger.info(f"✅ [ToolRegistry] 工具已启用: {name}")
            return True
        return False
    
    def disable_tool(self, name: str) -> bool:
        """
        禁用工具
        
        Args:
            name: 工具名称
            
        Returns:
            bool: 操作是否成功
        """
        tool = self.get_tool(name)
        if tool:
            tool.enabled = False
            self.logger.info(f"⏸️ [ToolRegistry] 工具已禁用: {name}")
            return True
        return False
    
    def unregister_tool(self, name: str) -> bool:
        """
        注销工具
        
        Args:
            name: 工具名称
            
        Returns:
            bool: 操作是否成功
        """
        if name in self._tools:
            del self._tools[name]
            
            # 从分类中移除
            for category_tools in self._categories.values():
                if name in category_tools:
                    category_tools.remove(name)
            
            self.logger.info(f"🗑️ [ToolRegistry] 工具已注销: {name}")
            return True
        return False
    
    def get_categories(self) -> List[str]:
        """
        获取所有工具分类
        
        Returns:
            List[str]: 分类列表
        """
        return list(self._categories.keys())
    
    def get_registry_stats(self) -> Dict[str, Any]:
        """
        获取注册中心统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        total_tools = len(self._tools)
        enabled_tools = len([t for t in self._tools.values() if t.enabled])
        
        return {
            "total_tools": total_tools,
            "enabled_tools": enabled_tools,
            "disabled_tools": total_tools - enabled_tools,
            "categories": len(self._categories),
            "tool_classes": len(self._tool_classes),
            "categories_detail": {cat: len(tools) for cat, tools in self._categories.items()}
        }
    
    def __len__(self) -> int:
        return len(self._tools)
    
    def __contains__(self, name: str) -> bool:
        return name in self._tools or name in self._tool_classes
    
    def __iter__(self):
        return iter(self._tools.values())

class ToolExecutor:
    """
    工具执行引擎
    
    负责安全地执行工具，包括权限检查、参数验证、错误处理和结果标准化。
    """
    
    def __init__(self, registry: ToolRegistry):
        """
        初始化工具执行引擎
        
        Args:
            registry: 工具注册中心
        """
        self.registry = registry
        self.logger = logging.getLogger(f"{__name__}.ToolExecutor")
        self.permissions = set()  # 当前执行上下文的权限
        
        self.logger.info("⚡ [ToolExecutor] 工具执行引擎初始化完成")
    
    def set_permissions(self, permissions: List[str]) -> None:
        """
        设置执行权限
        
        Args:
            permissions: 权限列表
        """
        self.permissions = set(permissions)
        self.logger.info(f"🔐 [ToolExecutor] 权限已设置: {permissions}")
    
    def execute_tool(self, tool_name: str, params: Dict[str, Any]) -> ToolResult:
        """
        执行工具
        
        Args:
            tool_name: 工具名称
            params: 执行参数
            
        Returns:
            ToolResult: 执行结果
        """
        start_time = datetime.utcnow()
        
        try:
            # 获取工具
            tool = self.registry.get_tool(tool_name)
            if not tool:
                return ToolResult(
                    status=ToolStatus.NOT_FOUND,
                    error=f"工具不存在: {tool_name}"
                )
            
            # 检查工具是否启用
            if not tool.enabled:
                return ToolResult(
                    status=ToolStatus.ERROR,
                    error=f"工具已禁用: {tool_name}"
                )
            
            # 权限检查
            required_permissions = tool.get_required_permissions()
            if required_permissions and not self.permissions.issuperset(required_permissions):
                missing_permissions = set(required_permissions) - self.permissions
                return ToolResult(
                    status=ToolStatus.PERMISSION_DENIED,
                    error=f"权限不足，缺少权限: {missing_permissions}"
                )
            
            # 参数验证
            if not tool.validate_params(params):
                return ToolResult(
                    status=ToolStatus.ERROR,
                    error=f"参数验证失败: {params}"
                )
            
            # 执行工具
            self.logger.info(f"🔧 [ToolExecutor] 开始执行工具: {tool_name}")
            result = tool.execute(params)
            
            # 计算执行时间
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            result.execution_time = execution_time
            
            # 更新工具统计
            tool._update_stats(result)
            
            if result.is_success():
                self.logger.info(f"✅ [ToolExecutor] 工具执行成功: {tool_name} ({execution_time:.3f}s)")
            else:
                self.logger.warning(f"⚠️ [ToolExecutor] 工具执行失败: {tool_name}, 错误: {result.error}")
            
            return result
            
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            error_msg = f"工具执行异常: {str(e)}"
            
            self.logger.error(f"❌ [ToolExecutor] {error_msg}")
            self.logger.error(f"❌ [ToolExecutor] 异常堆栈: {traceback.format_exc()}")
            
            return ToolResult(
                status=ToolStatus.ERROR,
                error=error_msg,
                execution_time=execution_time,
                metadata={"exception_type": type(e).__name__, "traceback": traceback.format_exc()}
            )

# 全局工具注册中心实例
_global_registry = None

def get_global_registry() -> ToolRegistry:
    """
    获取全局工具注册中心实例
    
    Returns:
        ToolRegistry: 全局注册中心实例
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = ToolRegistry()
    return _global_registry

def register_tool(tool: BaseTool, category: str = "general") -> bool:
    """
    注册工具到全局注册中心
    
    Args:
        tool: 工具实例
        category: 工具分类
        
    Returns:
        bool: 注册是否成功
    """
    return get_global_registry().register_tool(tool, category)

def get_tool(name: str) -> Optional[BaseTool]:
    """
    从全局注册中心获取工具
    
    Args:
        name: 工具名称
        
    Returns:
        Optional[BaseTool]: 工具实例
    """
    return get_global_registry().get_tool(name)

# 示例工具实现
class EchoTool(BaseTool):
    """
    回声工具 - 用于测试和演示
    
    简单地返回输入的内容，用于验证工具系统的基本功能。
    """
    
    def __init__(self):
        super().__init__(
            name="echo",
            description="回声工具，返回输入的内容",
            version="1.0.0"
        )
    
    def execute(self, params: Dict[str, Any]) -> ToolResult:
        """
        执行回声操作
        
        Args:
            params: 包含'message'字段的参数字典
            
        Returns:
            ToolResult: 包含回声内容的结果
        """
        message = params.get('message', '')
        
        return ToolResult(
            status=ToolStatus.SUCCESS,
            data={
                "echo": message,
                "length": len(str(message)),
                "type": type(message).__name__
            },
            metadata={
                "tool": self.name,
                "operation": "echo"
            }
        )
    
    def validate_params(self, params: Dict[str, Any]) -> bool:
        """
        验证参数
        
        Args:
            params: 待验证的参数
            
        Returns:
            bool: 参数是否有效
        """
        return isinstance(params, dict) and 'message' in params

class MathTool(BaseTool):
    """
    数学计算工具 - 用于基本数学运算
    
    支持基本的数学运算，如加法、减法、乘法、除法等。
    """
    
    def __init__(self):
        super().__init__(
            name="math",
            description="数学计算工具，支持基本运算",
            version="1.0.0"
        )
    
    def execute(self, params: Dict[str, Any]) -> ToolResult:
        """
        执行数学运算
        
        Args:
            params: 包含'operation', 'a', 'b'字段的参数字典
            
        Returns:
            ToolResult: 包含计算结果的结果
        """
        operation = params.get('operation')
        a = params.get('a')
        b = params.get('b')
        
        try:
            if operation == 'add':
                result = a + b
            elif operation == 'subtract':
                result = a - b
            elif operation == 'multiply':
                result = a * b
            elif operation == 'divide':
                if b == 0:
                    return ToolResult(
                        status=ToolStatus.ERROR,
                        error="除数不能为零"
                    )
                result = a / b
            else:
                return ToolResult(
                    status=ToolStatus.ERROR,
                    error=f"不支持的运算: {operation}"
                )
            
            return ToolResult(
                status=ToolStatus.SUCCESS,
                data={
                    "result": result,
                    "operation": operation,
                    "operands": [a, b]
                },
                metadata={
                    "tool": self.name,
                    "operation": operation
                }
            )
            
        except Exception as e:
            return ToolResult(
                status=ToolStatus.ERROR,
                error=f"计算错误: {str(e)}"
            )
    
    def validate_params(self, params: Dict[str, Any]) -> bool:
        """
        验证参数
        
        Args:
            params: 待验证的参数
            
        Returns:
            bool: 参数是否有效
        """
        required_fields = ['operation', 'a', 'b']
        if not all(field in params for field in required_fields):
            return False
        
        # 检查操作类型
        valid_operations = ['add', 'subtract', 'multiply', 'divide']
        if params['operation'] not in valid_operations:
            return False
        
        # 检查操作数是否为数字
        try:
            float(params['a'])
            float(params['b'])
            return True
        except (ValueError, TypeError):
            return False

# 网络搜索工具实现
class WebSearchTool(BaseTool):
    """
    网络搜索工具 - 使用Tavily API执行网络搜索
    """
    
    def __init__(self, name: str = "web_search", tavily_client: Optional[TavilyClient] = None):
        super().__init__(
            name=name,
            description="执行网络搜索并返回结果",
            version="1.0.0"
        )
        self.permissions = {"web_access", "external_api"}
        
        if tavily_client:
            self.client = tavily_client
        else:
            self.api_key = os.getenv("TAVILY_API_KEY")
            if not self.api_key:
                logger.warning("⚠️ [WebSearchTool] TAVILY_API_KEY not found in environment variables.")
                self.client = None
            else:
                self.client = TavilyClient(api_key=self.api_key)
    
    def execute(self, params: Dict[str, Any]) -> ToolResult:
        """
        执行网络搜索
        
        Args:
            params: 包含 'query' 字段的参数字典
            
        Returns:
            ToolResult: 包含搜索结果的 ToolResult
        """
        if not self.client:
            return ToolResult(
                status=ToolStatus.ERROR,
                error="Tavily API key not configured."
            )
            
        query = params.get('query')
        if not query:
            return ToolResult(
                status=ToolStatus.ERROR,
                error="参数 'query' 不能为空"
            )
        
        try:
            logger.info(f"🔍 [WebSearchTool] Performing search for: {query}")
            response = self.client.search(query=query, search_depth="basic")
            
            return ToolResult(
                status=ToolStatus.SUCCESS,
                data=response,
                metadata={"tool": self.name, "operation": "search", "query": query}
            )
            
        except Exception as e:
            logger.error(f"❌ [WebSearchTool] Search failed: {e}", exc_info=True)
            return ToolResult(
                status=ToolStatus.ERROR,
                error=f"网络搜索失败: {str(e)}"
            )

# 自动注册示例工具
def _register_builtin_tools():
    """
    注册内置工具
    """
    registry = get_global_registry()
    
    # 注册示例工具
    registry.register_tool(EchoTool(), "utility")
    registry.register_tool(MathTool(), "computation")
    registry.register_tool(WebSearchTool(), "external_api")
    
    logger.info("🔧 [Tools] 内置工具注册完成")

# 模块加载时自动注册内置工具
_register_builtin_tools()

if __name__ == "__main__":
    # 测试代码
    import sys
    
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - [%(levelname)s] - %(message)s'
    )
    
    print("🔧 工具系统测试")
    print("=" * 50)
    
    # 获取注册中心
    registry = get_global_registry()
    executor = ToolExecutor(registry)
    
    # 显示注册的工具
    print(f"📋 已注册工具: {registry.list_tools()}")
    print(f"📊 注册中心统计: {registry.get_registry_stats()}")
    
    # 测试回声工具
    print("\n🔍 测试回声工具:")
    result = executor.execute_tool("echo", {"message": "Hello, Multi-Agent System!"})
    print(f"结果: {result.to_dict()}")
    
    # 测试数学工具
    print("\n🔍 测试数学工具:")
    result = executor.execute_tool("math", {"operation": "add", "a": 10, "b": 5})
    print(f"结果: {result.to_dict()}")
    
    # 测试错误情况
    print("\n🔍 测试错误情况:")
    result = executor.execute_tool("nonexistent", {})
    print(f"结果: {result.to_dict()}")
    
    print("\n✅ 工具系统测试完成")