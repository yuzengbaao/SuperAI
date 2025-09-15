# src/core/module_loader.py

import os
import importlib.util
import inspect
from pathlib import Path

class ModuleLoader:
    """
    AGI核心模块加载器
    负责动态扫描、加载和管理所有可插拔的AI功能模块。
    """
    def __init__(self, modules_base_path="src/modules"):
        self.base_path = Path(modules_base_path)
        self.modules = {}
        self.module_instances = {}

    def discover_and_load_modules(self):
        """
        发现并加载所有模块。
        这将遍历modules目录，导入所有.py文件，并查找模块类。
        """
        print("🧠 [Core] 开始发现并加载AGI模块...")
        if not self.base_path.is_dir():
            print(f"❌ [Core] 错误: 模块路径不存在: {self.base_path}")
            return self.module_instances # Return empty dict instead of None

        for root, _, files in os.walk(self.base_path):
            for file in files:
                if file.endswith(".py") and not file.startswith("__"):
                    module_path = Path(root) / file
                    
                    try:
                        # Convert file path to a Python import path.
                        # e.g., c:\project1\src\modules\planning\planning_module.py -> src.modules.planning.planning_module
                        # This relies on the project root (c:\project1) being in sys.path.
                        rel_path = os.path.relpath(module_path, self.base_path.parent.parent)
                        module_path_without_ext = os.path.splitext(rel_path)[0]
                        import_path = module_path_without_ext.replace(os.sep, '.')
        
                        # Dynamically import the module
                        module_spec = importlib.util.spec_from_file_location(import_path, module_path)
                        if module_spec and module_spec.loader:
                            module = importlib.util.module_from_spec(module_spec)
                            module_spec.loader.exec_module(module)
                            
                            # Find the class in the module by inspecting its members
                            found_class = False
                            for name, obj in inspect.getmembers(module, inspect.isclass):
                                # Ensure the class is defined in this module, not imported from another
                                if obj.__module__ == module.__name__:
                                    print(f"  - 发现模块: {name} ({import_path})")
                                    self.modules[name] = obj
                                    found_class = True
                            
                            if not found_class:
                                print(f"  - ⚠️ [Core] 在模块 '{import_path}' 中未找到任何在其中定义的类。")
                        else:
                            print(f"  - ⚠️ [Core] 无法为路径 '{module_path}' 创建模块规范。")
                            
                    except Exception as e:
                        print(f"⚠️ [Core] 加载模块 {module_path} 失败: {e}")
        
        print(f"✅ [Core] AGI模块加载完成。共发现 {len(self.modules)} 个模块。")
        self._instantiate_modules()
        return self.module_instances

    def _get_module_name_from_path(self, path: Path) -> str:
        """从文件路径生成一个唯一的模块名"""
        relative_path = path.relative_to(self.base_path.parent)
        return str(relative_path).replace(os.sep, ".").replace(".py", "")

    def _register_module_classes(self, module, module_name):
        """
        在给定的模块中查找并注册模块类。
        约定：每个模块文件中应该有一个与文件名（驼峰式）匹配的类。
        """
        for name, obj in inspect.getmembers(module, inspect.isclass):
            # 简单的约定：如果类定义在当前模块中，我们就认为它是模块主类
            if obj.__module__ == module.__name__:
                if name in self.modules:
                    print(f"⚠️ [Core] 警告: 模块类名冲突 '{name}'。旧的将被覆盖。")
                self.modules[name] = obj
                print(f"  - 发现模块: {name} ({module_name})")

    def _instantiate_modules(self):
        """
        实例化所有已加载的模块类。
        """
        print("🚀 [Core] 正在实例化所有AGI模块...")
        for name, module_class in self.modules.items():
            try:
                self.module_instances[name] = module_class()
                print(f"  - 实例化成功: {name}")
            except Exception as e:
                print(f"❌ [Core] 实例化模块 {name} 失败: {e}")

    def get_module(self, name):
        """获取一个已实例化的模块"""
        return self.module_instances.get(name)

if __name__ == '__main__':
    # 用于测试模块加载器
    loader = ModuleLoader(modules_base_path="../src/modules")
    loaded_modules = loader.discover_and_load_modules()
    
    print("\n--- 已加载的模块实例 ---")
    for name, instance in loaded_modules.items():
        print(f"{name}: {instance}")

    # 示例：获取并使用一个模块
    # trading_engine = loader.get_module('TradingEngine')
    # if trading_engine:
    #     print("\n--- 测试交易引擎 ---")
    #     trading_engine.start_continuous_trading() # 假设有这个方法
