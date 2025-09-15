#!/bin/bash
# 超级AI系统启动脚本

echo "===  启动超级AI系统 ==="
echo ""

# 检查Docker服务
if ! docker --version > /dev/null 2>&1; then
    echo " Docker未安装或未启动"
    exit 1
fi

echo " Docker服务正常"

# 检查Docker Compose
if ! docker-compose --version > /dev/null 2>&1; then
    echo " Docker Compose未安装"
    exit 1
fi

echo " Docker Compose正常"

# 启动服务
echo " 启动超级AI微服务..."
docker-compose up -d

# 等待服务启动
echo " 等待服务启动..."
sleep 30

# 检查服务状态
echo " 检查服务状态:"
docker-compose ps

echo ""
echo "===  超级AI系统启动完成 ==="
echo " 监控面板: http://localhost:3000 (admin/admin)"
echo " 指标监控: http://localhost:9090"
echo " 千问服务: http://localhost:8201"
echo " 健康检查: http://localhost:8105"
