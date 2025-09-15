#!/usr/bin/env python3
"""
SuperAI 配置管理器
用于管理多环境配置和密钥管理
"""

import os
import sys
import argparse
import json
from pathlib import Path
from typing import Dict, Any, Optional
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('config_manager')

class ConfigManager:
    """SuperAI配置管理器"""
    
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root or os.getcwd())
        self.config_dir = self.project_root
        self.environments = ['development', 'staging', 'production']
        
    def list_environments(self) -> list:
        """列出所有可用环境"""
        env_files = []
        for env in self.environments:
            env_file = self.config_dir / f'.env.{env}'
            if env_file.exists():
                env_files.append(env)
        return env_files
    
    def validate_config(self, environment: str) -> Dict[str, Any]:
        """验证环境配置"""
        env_file = self.config_dir / f'.env.{environment}'
        
        if not env_file.exists():
            raise FileNotFoundError(f"配置文件不存在: {env_file}")
        
        config = {}
        missing_vars = []
        invalid_vars = []
        
        # 必需的配置项
        required_vars = {
            'ENVIRONMENT': str,
            'AGENT_PLANNER_PORT': int,
            'AGENT_EXECUTOR_PORT': int,
            'REDIS_HOST': str,
            'REDIS_PORT': int,
        }
        
        # 生产环境额外必需项
        if environment == 'production':
            required_vars.update({
                'REDIS_PASSWORD': str,
                'SECRET_KEY': str,
                'JWT_SECRET': str,
            })
        
        # 读取配置文件
        with open(env_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # 处理引用变量
                    if value.startswith('${') and value.endswith('}'):
                        config[key] = f"SECRET_REFERENCE: {value}"
                    else:
                        config[key] = value
        
        # 验证必需变量
        for var_name, var_type in required_vars.items():
            if var_name not in config:
                missing_vars.append(var_name)
            else:
                value = config[var_name]
                if var_type == int:
                    try:
                        int(value)
                    except ValueError:
                        invalid_vars.append(f"{var_name}: 应为整数，实际为 '{value}'")
        
        # 验证端口范围
        port_vars = ['AGENT_PLANNER_PORT', 'AGENT_EXECUTOR_PORT', 'REDIS_PORT']
        for port_var in port_vars:
            if port_var in config:
                try:
                    port = int(config[port_var])
                    if not (1024 <= port <= 65535):
                        invalid_vars.append(f"{port_var}: 端口应在1024-65535范围内")
                except ValueError:
                    pass  # 已在上面检查过
        
        return {
            'environment': environment,
            'config_file': str(env_file),
            'total_vars': len(config),
            'missing_vars': missing_vars,
            'invalid_vars': invalid_vars,
            'is_valid': len(missing_vars) == 0 and len(invalid_vars) == 0,
            'config': config
        }
    
    def generate_docker_env(self, environment: str, output_file: str = None) -> str:
        """生成Docker Compose使用的环境文件"""
        env_file = self.config_dir / f'.env.{environment}'
        
        if not env_file.exists():
            raise FileNotFoundError(f"配置文件不存在: {env_file}")
        
        output_file = output_file or f'.env.{environment}.docker'
        output_path = self.config_dir / output_file
        
        # 读取原始配置
        with open(env_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 添加Docker特定配置
        docker_content = f"""# Docker Compose环境文件
# 基于: {env_file.name}
# 生成时间: {datetime.now().isoformat()}
# 警告: 此文件由config_manager.py自动生成，请勿手动编辑

{content}

# === Docker特定配置 ===
COMPOSE_PROJECT_NAME=superai
COMPOSE_FILE=docker-compose.yml
DOCKER_BUILDKIT=1
COMPOSE_DOCKER_CLI_BUILD=1

# === 容器网络配置 ===
NETWORK_INTERNAL=agi-internal
NETWORK_PUBLIC=agi-public
"""
        
        # 写入输出文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(docker_content)
        
        logger.info(f"Docker环境文件已生成: {output_path}")
        return str(output_path)
    
    def check_secrets(self, environment: str) -> Dict[str, Any]:
        """检查密钥配置状态"""
        validation = self.validate_config(environment)
        config = validation['config']
        
        secret_vars = []
        missing_secrets = []
        
        for key, value in config.items():
            if isinstance(value, str) and value.startswith('SECRET_REFERENCE:'):
                secret_vars.append(key)
                # 检查对应的Docker Secret是否存在
                secret_name = value.split('${')[1].split('}')[0]
                # 这里可以添加实际的Docker Secret检查逻辑
                # 目前只是标记为需要配置
                missing_secrets.append(secret_name)
        
        return {
            'environment': environment,
            'secret_vars': secret_vars,
            'missing_secrets': missing_secrets,
            'secrets_configured': len(missing_secrets) == 0
        }
    
    def create_secrets_template(self, environment: str) -> str:
        """创建密钥配置模板"""
        secrets_info = self.check_secrets(environment)
        
        template_content = f"""#!/bin/bash
# SuperAI {environment.title()} 环境密钥配置脚本
# 生成时间: {datetime.now().isoformat()}
# 使用方法: 修改下面的值，然后运行此脚本

echo "配置 SuperAI {environment} 环境密钥..."

# 检查Docker Swarm模式
if ! docker info --format '{{{{.Swarm.LocalNodeState}}}}' | grep -q active; then
    echo "初始化Docker Swarm模式..."
    docker swarm init
fi

"""
        
        # 添加每个密钥的配置命令
        for secret in secrets_info['missing_secrets']:
            secret_var = secret.lower() + '_value'
            template_content += f"""
# 配置 {secret}
echo "配置密钥: {secret}"
echo "请输入 {secret} 的值:"
read -s {secret_var}
echo "${secret_var}" | docker secret create {secret} - || echo "密钥 {secret} 已存在"
"""
        
        template_content += """

echo "密钥配置完成！"
echo "可以使用以下命令查看已配置的密钥:"
echo "docker secret ls"
"""
        
        # 保存模板文件
        template_file = self.config_dir / f'setup_secrets_{environment}.sh'
        with open(template_file, 'w', encoding='utf-8') as f:
            f.write(template_content)
        
        # 设置执行权限
        os.chmod(template_file, 0o755)
        
        logger.info(f"密钥配置模板已创建: {template_file}")
        return str(template_file)
    
    def export_config(self, environment: str, format: str = 'json') -> str:
        """导出配置为指定格式"""
        validation = self.validate_config(environment)
        
        if format.lower() == 'json':
            output_file = self.config_dir / f'config_{environment}.json'
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(validation, f, indent=2, ensure_ascii=False)
        
        elif format.lower() == 'yaml':
            try:
                import yaml
                output_file = self.config_dir / f'config_{environment}.yaml'
                with open(output_file, 'w', encoding='utf-8') as f:
                    yaml.dump(validation, f, default_flow_style=False, allow_unicode=True)
            except ImportError:
                raise ImportError("需要安装PyYAML: pip install PyYAML")
        
        else:
            raise ValueError(f"不支持的格式: {format}")
        
        logger.info(f"配置已导出: {output_file}")
        return str(output_file)

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='SuperAI配置管理器')
    parser.add_argument('command', choices=[
        'list', 'validate', 'generate-docker', 'check-secrets', 
        'create-secrets-template', 'export'
    ], help='要执行的命令')
    parser.add_argument('-e', '--environment', 
                       choices=['development', 'staging', 'production'],
                       help='目标环境')
    parser.add_argument('-o', '--output', help='输出文件路径')
    parser.add_argument('-f', '--format', choices=['json', 'yaml'], 
                       default='json', help='导出格式')
    parser.add_argument('--project-root', help='项目根目录路径')
    
    args = parser.parse_args()
    
    try:
        config_manager = ConfigManager(args.project_root)
        
        if args.command == 'list':
            environments = config_manager.list_environments()
            print("可用环境:")
            for env in environments:
                print(f"  - {env}")
        
        elif args.command == 'validate':
            if not args.environment:
                print("错误: 需要指定环境 (-e/--environment)")
                sys.exit(1)
            
            result = config_manager.validate_config(args.environment)
            print(f"\n环境: {result['environment']}")
            print(f"配置文件: {result['config_file']}")
            print(f"配置项总数: {result['total_vars']}")
            print(f"验证状态: {'✅ 通过' if result['is_valid'] else '❌ 失败'}")
            
            if result['missing_vars']:
                print(f"\n缺失变量 ({len(result['missing_vars'])}):")
                for var in result['missing_vars']:
                    print(f"  - {var}")
            
            if result['invalid_vars']:
                print(f"\n无效变量 ({len(result['invalid_vars'])}):")
                for var in result['invalid_vars']:
                    print(f"  - {var}")
        
        elif args.command == 'generate-docker':
            if not args.environment:
                print("错误: 需要指定环境 (-e/--environment)")
                sys.exit(1)
            
            output_file = config_manager.generate_docker_env(args.environment, args.output)
            print(f"Docker环境文件已生成: {output_file}")
        
        elif args.command == 'check-secrets':
            if not args.environment:
                print("错误: 需要指定环境 (-e/--environment)")
                sys.exit(1)
            
            result = config_manager.check_secrets(args.environment)
            print(f"\n环境: {result['environment']}")
            print(f"密钥变量数: {len(result['secret_vars'])}")
            print(f"配置状态: {'✅ 已配置' if result['secrets_configured'] else '❌ 需要配置'}")
            
            if result['missing_secrets']:
                print(f"\n需要配置的密钥 ({len(result['missing_secrets'])}):")
                for secret in result['missing_secrets']:
                    print(f"  - {secret}")
        
        elif args.command == 'create-secrets-template':
            if not args.environment:
                print("错误: 需要指定环境 (-e/--environment)")
                sys.exit(1)
            
            template_file = config_manager.create_secrets_template(args.environment)
            print(f"密钥配置模板已创建: {template_file}")
            print(f"使用方法: chmod +x {template_file} && ./{template_file}")
        
        elif args.command == 'export':
            if not args.environment:
                print("错误: 需要指定环境 (-e/--environment)")
                sys.exit(1)
            
            output_file = config_manager.export_config(args.environment, args.format)
            print(f"配置已导出: {output_file}")
    
    except Exception as e:
        logger.error(f"执行失败: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()