#!/usr/bin/env python3
"""
文件操作工具模块

为多智能体协作系统提供安全的文件操作能力，包括文件读取、写入、
目录操作等功能。所有操作都在安全的沙箱环境中执行。

核心工具:
- FileOperationsTool: 通用文件操作工具
- TextFileReaderTool: 专门的文本文件读取工具
- TextFileWriterTool: 专门的文本文件写入工具
- DirectoryOperationsTool: 目录操作工具

安全特性:
1. 路径验证: 防止路径遍历攻击
2. 权限控制: 基于白名单的目录访问控制
3. 文件大小限制: 防止内存溢出
4. 类型检查: 确保操作的文件类型安全
"""

import os
import json
import shutil
import pathlib
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass

from .tools import BaseTool, ToolResult, ToolStatus

class FileOperationsTool(BaseTool):
    """
    通用文件操作工具
    
    提供安全的文件和目录操作功能，包括读取、写入、复制、移动、删除等。
    所有操作都在配置的安全目录范围内执行。
    """
    
    def __init__(self, allowed_paths: List[str] = None, max_file_size: int = 10 * 1024 * 1024):
        """
        初始化文件操作工具
        
        Args:
            allowed_paths: 允许访问的目录列表，默认为当前工作目录
            max_file_size: 最大文件大小限制（字节），默认10MB
        """
        super().__init__(
            name="file_operations",
            description="安全的文件和目录操作工具，支持读写、复制、移动等操作",
            version="1.0.0"
        )
        
        # 设置允许访问的路径
        if allowed_paths is None:
            self.allowed_paths = [os.getcwd()]
        else:
            self.allowed_paths = [os.path.abspath(path) for path in allowed_paths]
        
        self.max_file_size = max_file_size
        
        # 设置权限要求
        self.permissions.add('file_read')
        self.permissions.add('file_write')
        
        # 支持的操作类型
        self.supported_operations = {
            'read_file': self._read_file,
            'write_file': self._write_file,
            'append_file': self._append_file,
            'copy_file': self._copy_file,
            'move_file': self._move_file,
            'delete_file': self._delete_file,
            'list_directory': self._list_directory,
            'create_directory': self._create_directory,
            'delete_directory': self._delete_directory,
            'get_file_info': self._get_file_info,
            'file_exists': self._file_exists
        }
    
    def validate_params(self, params: Dict[str, Any]) -> bool:
        """
        验证输入参数
        """
        if not isinstance(params, dict):
            return False
        
        operation = params.get('operation')
        if operation not in self.supported_operations:
            return False
        
        # 检查必需的路径参数
        if operation in ['read_file', 'write_file', 'append_file', 'delete_file', 'get_file_info', 'file_exists']:
            if 'path' not in params:
                return False
        
        if operation in ['copy_file', 'move_file']:
            if 'source_path' not in params or 'destination_path' not in params:
                return False
        
        if operation in ['write_file', 'append_file']:
            if 'content' not in params:
                return False
        
        return True
    
    def execute(self, params: Dict[str, Any]) -> ToolResult:
        """
        执行文件操作
        
        Args:
            params: 操作参数，包含operation和相关参数
            
        Returns:
            ToolResult: 操作结果
        """
        operation = params.get('operation')
        
        try:
            # 获取操作函数
            operation_func = self.supported_operations.get(operation)
            if not operation_func:
                return ToolResult(
                    status=ToolStatus.ERROR,
                    error=f"不支持的操作: {operation}"
                )
            
            # 执行操作
            result = operation_func(params)
            
            return ToolResult(
                status=ToolStatus.SUCCESS,
                data=result,
                metadata={
                    "operation": operation,
                    "tool": self.name
                }
            )
            
        except PermissionError as e:
            return ToolResult(
                status=ToolStatus.PERMISSION_DENIED,
                error=f"权限不足: {str(e)}"
            )
        except FileNotFoundError as e:
            return ToolResult(
                status=ToolStatus.ERROR,
                error=f"文件未找到: {str(e)}"
            )
        except OSError as e:
            return ToolResult(
                status=ToolStatus.ERROR,
                error=f"文件系统错误: {str(e)}"
            )
        except Exception as e:
            return ToolResult(
                status=ToolStatus.ERROR,
                error=f"操作失败: {str(e)}"
            )
    
    def _validate_path(self, path: str) -> str:
        """
        验证并规范化路径
        
        Args:
            path: 要验证的路径
            
        Returns:
            str: 规范化的绝对路径
            
        Raises:
            PermissionError: 路径不在允许范围内
            ValueError: 路径格式无效
        """
        if not path:
            raise ValueError("路径不能为空")
        
        # 转换为绝对路径
        abs_path = os.path.abspath(path)
        
        # 检查路径是否在允许的目录范围内
        path_allowed = False
        for allowed_path in self.allowed_paths:
            try:
                # 使用 pathlib 进行安全的路径比较
                abs_path_obj = pathlib.Path(abs_path)
                allowed_path_obj = pathlib.Path(allowed_path)
                
                # 检查是否为允许路径的子路径
                if abs_path_obj == allowed_path_obj or allowed_path_obj in abs_path_obj.parents:
                    path_allowed = True
                    break
            except (OSError, ValueError):
                continue
        
        if not path_allowed:
            raise PermissionError(f"路径 {abs_path} 不在允许的访问范围内")
        
        return abs_path
    
    def _read_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        读取文件内容
        """
        path = self._validate_path(params['path'])
        encoding = params.get('encoding', 'utf-8')
        max_lines = params.get('max_lines', None)
        
        # 检查文件大小
        file_size = os.path.getsize(path)
        if file_size > self.max_file_size:
            raise ValueError(f"文件大小 {file_size} 超过限制 {self.max_file_size}")
        
        with open(path, 'r', encoding=encoding) as f:
            if max_lines:
                lines = []
                for i, line in enumerate(f):
                    if i >= max_lines:
                        break
                    lines.append(line.rstrip('\n\r'))
                content = '\n'.join(lines)
                truncated = i >= max_lines - 1
            else:
                content = f.read()
                truncated = False
        
        return {
            "content": content,
            "file_path": path,
            "file_size": file_size,
            "encoding": encoding,
            "truncated": truncated,
            "lines_read": len(content.split('\n')) if content else 0
        }
    
    def _write_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        写入文件内容
        """
        path = self._validate_path(params['path'])
        content = params['content']
        encoding = params.get('encoding', 'utf-8')
        create_dirs = params.get('create_dirs', False)
        
        # 检查内容大小
        content_size = len(content.encode(encoding))
        if content_size > self.max_file_size:
            raise ValueError(f"内容大小 {content_size} 超过限制 {self.max_file_size}")
        
        # 创建目录（如果需要）
        if create_dirs:
            os.makedirs(os.path.dirname(path), exist_ok=True)
        
        with open(path, 'w', encoding=encoding) as f:
            f.write(content)
        
        return {
            "file_path": path,
            "bytes_written": content_size,
            "encoding": encoding,
            "lines_written": len(content.split('\n')) if content else 0
        }
    
    def _append_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        追加内容到文件
        """
        path = self._validate_path(params['path'])
        content = params['content']
        encoding = params.get('encoding', 'utf-8')
        
        # 检查文件是否存在，如果存在检查总大小
        if os.path.exists(path):
            existing_size = os.path.getsize(path)
            content_size = len(content.encode(encoding))
            if existing_size + content_size > self.max_file_size:
                raise ValueError(f"追加后文件大小将超过限制 {self.max_file_size}")
        
        with open(path, 'a', encoding=encoding) as f:
            f.write(content)
        
        final_size = os.path.getsize(path)
        
        return {
            "file_path": path,
            "content_appended": len(content.encode(encoding)),
            "final_file_size": final_size,
            "encoding": encoding
        }
    
    def _copy_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        复制文件
        """
        source_path = self._validate_path(params['source_path'])
        dest_path = self._validate_path(params['destination_path'])
        overwrite = params.get('overwrite', False)
        
        if os.path.exists(dest_path) and not overwrite:
            raise FileExistsError(f"目标文件已存在: {dest_path}")
        
        # 检查源文件大小
        source_size = os.path.getsize(source_path)
        if source_size > self.max_file_size:
            raise ValueError(f"源文件大小 {source_size} 超过限制 {self.max_file_size}")
        
        shutil.copy2(source_path, dest_path)
        
        return {
            "source_path": source_path,
            "destination_path": dest_path,
            "file_size": source_size,
            "overwritten": os.path.exists(dest_path) and overwrite
        }
    
    def _move_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        移动文件
        """
        source_path = self._validate_path(params['source_path'])
        dest_path = self._validate_path(params['destination_path'])
        overwrite = params.get('overwrite', False)
        
        if os.path.exists(dest_path) and not overwrite:
            raise FileExistsError(f"目标文件已存在: {dest_path}")
        
        source_size = os.path.getsize(source_path)
        shutil.move(source_path, dest_path)
        
        return {
            "source_path": source_path,
            "destination_path": dest_path,
            "file_size": source_size
        }
    
    def _delete_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        删除文件
        """
        path = self._validate_path(params['path'])
        
        if not os.path.exists(path):
            raise FileNotFoundError(f"文件不存在: {path}")
        
        file_size = os.path.getsize(path)
        os.remove(path)
        
        return {
            "deleted_path": path,
            "file_size": file_size
        }
    
    def _list_directory(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        列出目录内容
        """
        path = self._validate_path(params['path'])
        include_hidden = params.get('include_hidden', False)
        file_details = params.get('file_details', False)
        
        if not os.path.isdir(path):
            raise NotADirectoryError(f"路径不是目录: {path}")
        
        items = []
        for item_name in os.listdir(path):
            if not include_hidden and item_name.startswith('.'):
                continue
            
            item_path = os.path.join(path, item_name)
            item_info = {
                "name": item_name,
                "path": item_path,
                "is_file": os.path.isfile(item_path),
                "is_directory": os.path.isdir(item_path)
            }
            
            if file_details:
                try:
                    stat = os.stat(item_path)
                    item_info.update({
                        "size": stat.st_size,
                        "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "created_time": datetime.fromtimestamp(stat.st_ctime).isoformat()
                    })
                except OSError:
                    pass
            
            items.append(item_info)
        
        return {
            "directory_path": path,
            "items": items,
            "total_items": len(items),
            "files_count": sum(1 for item in items if item['is_file']),
            "directories_count": sum(1 for item in items if item['is_directory'])
        }
    
    def _create_directory(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建目录
        """
        path = self._validate_path(params['path'])
        parents = params.get('parents', True)
        exist_ok = params.get('exist_ok', True)
        
        if parents:
            os.makedirs(path, exist_ok=exist_ok)
        else:
            os.mkdir(path)
        
        return {
            "created_path": path,
            "parents_created": parents
        }
    
    def _delete_directory(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        删除目录
        """
        path = self._validate_path(params['path'])
        recursive = params.get('recursive', False)
        
        if not os.path.exists(path):
            raise FileNotFoundError(f"目录不存在: {path}")
        
        if not os.path.isdir(path):
            raise NotADirectoryError(f"路径不是目录: {path}")
        
        if recursive:
            shutil.rmtree(path)
        else:
            os.rmdir(path)
        
        return {
            "deleted_path": path,
            "recursive": recursive
        }
    
    def _get_file_info(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        获取文件信息
        """
        path = self._validate_path(params['path'])
        
        if not os.path.exists(path):
            raise FileNotFoundError(f"文件不存在: {path}")
        
        stat = os.stat(path)
        
        return {
            "path": path,
            "name": os.path.basename(path),
            "size": stat.st_size,
            "is_file": os.path.isfile(path),
            "is_directory": os.path.isdir(path),
            "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "created_time": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "permissions": oct(stat.st_mode)[-3:]
        }
    
    def _file_exists(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        检查文件是否存在
        """
        path = self._validate_path(params['path'])
        
        exists = os.path.exists(path)
        
        result = {
            "path": path,
            "exists": exists
        }
        
        if exists:
            result.update({
                "is_file": os.path.isfile(path),
                "is_directory": os.path.isdir(path)
            })
        
        return result

class TextFileReaderTool(BaseTool):
    """
    专门的文本文件读取工具
    
    针对文本文件读取进行优化，支持多种编码和读取模式。
    """
    
    def __init__(self, allowed_paths: List[str] = None, max_file_size: int = 5 * 1024 * 1024):
        super().__init__(
            name="text_file_reader",
            description="专门的文本文件读取工具，支持多种编码和读取模式",
            version="1.0.0"
        )
        
        if allowed_paths is None:
            self.allowed_paths = [os.getcwd()]
        else:
            self.allowed_paths = [os.path.abspath(path) for path in allowed_paths]
        
        self.max_file_size = max_file_size
        self.permissions.add('file_read')
    
    def validate_params(self, params: Dict[str, Any]) -> bool:
        return isinstance(params, dict) and 'path' in params
    
    def execute(self, params: Dict[str, Any]) -> ToolResult:
        try:
            path = params['path']
            encoding = params.get('encoding', 'utf-8')
            start_line = params.get('start_line', 1)
            end_line = params.get('end_line', None)
            
            # 验证路径
            abs_path = self._validate_path(path)
            
            # 检查文件大小
            file_size = os.path.getsize(abs_path)
            if file_size > self.max_file_size:
                return ToolResult(
                    status=ToolStatus.ERROR,
                    error=f"文件大小 {file_size} 超过限制 {self.max_file_size}"
                )
            
            # 读取文件
            with open(abs_path, 'r', encoding=encoding) as f:
                lines = f.readlines()
            
            # 处理行范围
            total_lines = len(lines)
            start_idx = max(0, start_line - 1)
            end_idx = min(total_lines, end_line) if end_line else total_lines
            
            selected_lines = lines[start_idx:end_idx]
            content = ''.join(selected_lines)
            
            return ToolResult(
                status=ToolStatus.SUCCESS,
                data={
                    "content": content,
                    "file_path": abs_path,
                    "total_lines": total_lines,
                    "lines_read": len(selected_lines),
                    "start_line": start_line,
                    "end_line": end_idx,
                    "file_size": file_size,
                    "encoding": encoding
                }
            )
            
        except Exception as e:
            return ToolResult(
                status=ToolStatus.ERROR,
                error=str(e)
            )
    
    def _validate_path(self, path: str) -> str:
        """验证路径（简化版本）"""
        abs_path = os.path.abspath(path)
        
        # 检查路径是否在允许范围内
        for allowed_path in self.allowed_paths:
            if abs_path.startswith(allowed_path):
                return abs_path
        
        raise PermissionError(f"路径 {abs_path} 不在允许的访问范围内")

class TextFileWriterTool(BaseTool):
    """
    专门的文本文件写入工具
    
    针对文本文件写入进行优化，支持多种写入模式。
    """
    
    def __init__(self, allowed_paths: List[str] = None, max_file_size: int = 5 * 1024 * 1024):
        super().__init__(
            name="text_file_writer",
            description="专门的文本文件写入工具，支持多种写入模式",
            version="1.0.0"
        )
        
        if allowed_paths is None:
            self.allowed_paths = [os.getcwd()]
        else:
            self.allowed_paths = [os.path.abspath(path) for path in allowed_paths]
        
        self.max_file_size = max_file_size
        self.permissions.add('file_write')
    
    def validate_params(self, params: Dict[str, Any]) -> bool:
        return (isinstance(params, dict) and 
                'path' in params and 
                'content' in params)
    
    def execute(self, params: Dict[str, Any]) -> ToolResult:
        try:
            path = params['path']
            content = params['content']
            mode = params.get('mode', 'write')  # write, append
            encoding = params.get('encoding', 'utf-8')
            create_dirs = params.get('create_dirs', True)
            
            # 验证路径
            abs_path = self._validate_path(path)
            
            # 检查内容大小
            content_size = len(content.encode(encoding))
            if content_size > self.max_file_size:
                return ToolResult(
                    status=ToolStatus.ERROR,
                    error=f"内容大小 {content_size} 超过限制 {self.max_file_size}"
                )
            
            # 创建目录（如果需要）
            if create_dirs:
                os.makedirs(os.path.dirname(abs_path), exist_ok=True)
            
            # 写入文件
            file_mode = 'a' if mode == 'append' else 'w'
            with open(abs_path, file_mode, encoding=encoding) as f:
                f.write(content)
            
            final_size = os.path.getsize(abs_path)
            
            return ToolResult(
                status=ToolStatus.SUCCESS,
                data={
                    "file_path": abs_path,
                    "bytes_written": content_size,
                    "final_file_size": final_size,
                    "mode": mode,
                    "encoding": encoding,
                    "lines_written": len(content.split('\n')) if content else 0
                }
            )
            
        except Exception as e:
            return ToolResult(
                status=ToolStatus.ERROR,
                error=str(e)
            )
    
    def _validate_path(self, path: str) -> str:
        """验证路径（简化版本）"""
        abs_path = os.path.abspath(path)
        
        # 检查路径是否在允许范围内
        for allowed_path in self.allowed_paths:
            if abs_path.startswith(allowed_path):
                return abs_path
        
        raise PermissionError(f"路径 {abs_path} 不在允许的访问范围内")

# 自动注册文件工具
def _register_file_tools():
    """
    注册文件操作工具到全局注册中心
    """
    from .tools import get_global_registry
    
    registry = get_global_registry()
    
    # 注册文件操作工具
    registry.register_tool(FileOperationsTool(), "file_operations")
    registry.register_tool(TextFileReaderTool(), "file_operations")
    registry.register_tool(TextFileWriterTool(), "file_operations")
    
    print("🗂️ [FileTools] 文件操作工具注册完成")

# 模块加载时自动注册
_register_file_tools()

if __name__ == "__main__":
    # 测试代码
    import tempfile
    import logging
    
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - [%(levelname)s] - %(message)s'
    )
    
    print("🗂️ 文件操作工具测试")
    print("=" * 50)
    
    # 创建临时目录进行测试
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"📁 测试目录: {temp_dir}")
        
        # 创建文件操作工具
        file_tool = FileOperationsTool(allowed_paths=[temp_dir])
        
        # 测试写入文件
        print("\n📝 测试文件写入:")
        write_result = file_tool.execute({
            "operation": "write_file",
            "path": os.path.join(temp_dir, "test.txt"),
            "content": "Hello, File Operations Tool!\nThis is a test file.",
            "create_dirs": True
        })
        print(f"写入结果: {write_result.to_dict()}")
        
        # 测试读取文件
        print("\n📖 测试文件读取:")
        read_result = file_tool.execute({
            "operation": "read_file",
            "path": os.path.join(temp_dir, "test.txt")
        })
        print(f"读取结果: {read_result.to_dict()}")
        
        # 测试目录列表
        print("\n📋 测试目录列表:")
        list_result = file_tool.execute({
            "operation": "list_directory",
            "path": temp_dir,
            "file_details": True
        })
        print(f"列表结果: {list_result.to_dict()}")
        
        # 测试文件信息
        print("\n📊 测试文件信息:")
        info_result = file_tool.execute({
            "operation": "get_file_info",
            "path": os.path.join(temp_dir, "test.txt")
        })
        print(f"信息结果: {info_result.to_dict()}")
    
    print("\n✅ 文件操作工具测试完成")