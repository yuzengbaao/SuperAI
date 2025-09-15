#!/bin/bash
# SuperAI Production 环境密钥配置脚本
# 生成时间: 2025-09-15T06:37:44.840743
# 使用方法: 修改下面的值，然后运行此脚本

echo "配置 SuperAI production 环境密钥..."

# 检查Docker Swarm模式
if ! docker info --format '{{.Swarm.LocalNodeState}}' | grep -q active; then
    echo "初始化Docker Swarm模式..."
    docker swarm init
fi


# 配置 REDIS_PASSWORD_SECRET
echo "配置密钥: REDIS_PASSWORD_SECRET"
echo "请输入 REDIS_PASSWORD_SECRET 的值:"
read -s redis_password_secret_value
echo "$redis_password_secret_value" | docker secret create REDIS_PASSWORD_SECRET - || echo "密钥 REDIS_PASSWORD_SECRET 已存在"

# 配置 GRAFANA_ADMIN_PASSWORD_SECRET
echo "配置密钥: GRAFANA_ADMIN_PASSWORD_SECRET"
echo "请输入 GRAFANA_ADMIN_PASSWORD_SECRET 的值:"
read -s grafana_admin_password_secret_value
echo "$grafana_admin_password_secret_value" | docker secret create GRAFANA_ADMIN_PASSWORD_SECRET - || echo "密钥 GRAFANA_ADMIN_PASSWORD_SECRET 已存在"

# 配置 TAVILY_API_KEY_SECRET
echo "配置密钥: TAVILY_API_KEY_SECRET"
echo "请输入 TAVILY_API_KEY_SECRET 的值:"
read -s tavily_api_key_secret_value
echo "$tavily_api_key_secret_value" | docker secret create TAVILY_API_KEY_SECRET - || echo "密钥 TAVILY_API_KEY_SECRET 已存在"

# 配置 OPENAI_API_KEY_SECRET
echo "配置密钥: OPENAI_API_KEY_SECRET"
echo "请输入 OPENAI_API_KEY_SECRET 的值:"
read -s openai_api_key_secret_value
echo "$openai_api_key_secret_value" | docker secret create OPENAI_API_KEY_SECRET - || echo "密钥 OPENAI_API_KEY_SECRET 已存在"

# 配置 SECRET_KEY_SECRET
echo "配置密钥: SECRET_KEY_SECRET"
echo "请输入 SECRET_KEY_SECRET 的值:"
read -s secret_key_secret_value
echo "$secret_key_secret_value" | docker secret create SECRET_KEY_SECRET - || echo "密钥 SECRET_KEY_SECRET 已存在"

# 配置 JWT_SECRET_SECRET
echo "配置密钥: JWT_SECRET_SECRET"
echo "请输入 JWT_SECRET_SECRET 的值:"
read -s jwt_secret_secret_value
echo "$jwt_secret_secret_value" | docker secret create JWT_SECRET_SECRET - || echo "密钥 JWT_SECRET_SECRET 已存在"

# 配置 DATABASE_URL_SECRET
echo "配置密钥: DATABASE_URL_SECRET"
echo "请输入 DATABASE_URL_SECRET 的值:"
read -s database_url_secret_value
echo "$database_url_secret_value" | docker secret create DATABASE_URL_SECRET - || echo "密钥 DATABASE_URL_SECRET 已存在"

# 配置 ALERT_WEBHOOK_URL_SECRET
echo "配置密钥: ALERT_WEBHOOK_URL_SECRET"
echo "请输入 ALERT_WEBHOOK_URL_SECRET 的值:"
read -s alert_webhook_url_secret_value
echo "$alert_webhook_url_secret_value" | docker secret create ALERT_WEBHOOK_URL_SECRET - || echo "密钥 ALERT_WEBHOOK_URL_SECRET 已存在"

# 配置 SMTP_HOST_SECRET
echo "配置密钥: SMTP_HOST_SECRET"
echo "请输入 SMTP_HOST_SECRET 的值:"
read -s smtp_host_secret_value
echo "$smtp_host_secret_value" | docker secret create SMTP_HOST_SECRET - || echo "密钥 SMTP_HOST_SECRET 已存在"

# 配置 SMTP_USERNAME_SECRET
echo "配置密钥: SMTP_USERNAME_SECRET"
echo "请输入 SMTP_USERNAME_SECRET 的值:"
read -s smtp_username_secret_value
echo "$smtp_username_secret_value" | docker secret create SMTP_USERNAME_SECRET - || echo "密钥 SMTP_USERNAME_SECRET 已存在"

# 配置 SMTP_PASSWORD_SECRET
echo "配置密钥: SMTP_PASSWORD_SECRET"
echo "请输入 SMTP_PASSWORD_SECRET 的值:"
read -s smtp_password_secret_value
echo "$smtp_password_secret_value" | docker secret create SMTP_PASSWORD_SECRET - || echo "密钥 SMTP_PASSWORD_SECRET 已存在"


echo "密钥配置完成！"
echo "可以使用以下命令查看已配置的密钥:"
echo "docker secret ls"
