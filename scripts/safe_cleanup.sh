#!/bin/bash
# 安全磁盘清理脚本 - 只清理安全的临时文件

set -e

echo "=== 安全磁盘清理 ==="
echo "时间: $(date)"
echo ""

# 显示清理前的磁盘使用
echo "📊 清理前:"
df -h / | tail -1
echo ""

CLEANED_SIZE=0

# 1. 清理 apt 缓存（安全）
echo "🗑️  清理 apt 缓存..."
APT_CLEANED=$(apt-get clean -y -qq 2>&1 || echo "apt 清理跳过")
echo "   $APT_CLEANED"

# 2. 清理 systemd 日志（保留最近 3 天）
echo "🗑️  清理 systemd 日志（保留 3 天）..."
if command -v journalctl &> /dev/null; then
    journalctl --vacuum-time=3d 2>/dev/null || echo "   journalctl 清理跳过"
fi

# 3. 清理用户临时文件
echo "🗑️  清理 /tmp 目录（>7 天的文件）..."
if [ -d "/tmp" ]; then
    TMP_CLEANED=$(find /tmp -type f -mtime +7 -delete -print 2>/dev/null | wc -l)
    echo "   删除了 $TMP_CLEANED 个旧临时文件"
fi

# 4. 清理用户缓存目录
echo "🗑️  清理 ~/.cache 目录（>30 天的文件）..."
if [ -d "$HOME/.cache" ]; then
    CACHE_CLEANED=$(find $HOME/.cache -type f -mtime +30 -delete -print 2>/dev/null | wc -l)
    echo "   删除了 $CACHE_CLEANED 个旧缓存文件"
fi

# 5. 清理 npm 缓存（如果存在）
echo "🗑️  清理 npm 缓存..."
if command -v npm &> /dev/null; then
    npm cache clean --force 2>/dev/null || echo "   npm 缓存清理跳过"
fi

# 6. 清理 pip 缓存（如果存在）
echo "🗑️  清理 pip 缓存..."
if command -v pip &> /dev/null; then
    pip cache purge 2>/dev/null || echo "   pip 缓存清理跳过"
fi

# 7. 清理 docker 悬空镜像（如果 docker 存在）
echo "🗑️  清理 Docker 悬空镜像..."
if command -v docker &> /dev/null; then
    docker system prune -f 2>/dev/null || echo "   Docker 清理跳过"
fi

# 8. 清理旧日志文件
echo "🗑️  清理 /var/log 旧日志（>30 天）..."
if [ -d "/var/log" ]; then
    LOG_CLEANED=$(find /var/log -type f -name "*.log" -mtime +30 -delete -print 2>/dev/null | wc -l)
    echo "   删除了 $LOG_CLEANED 个旧日志文件"
fi

# 9. 清理缩略图缓存
echo "🗑️  清理缩略图缓存..."
if [ -d "$HOME/.cache/thumbnails" ]; then
    rm -rf $HOME/.cache/thumbnails/* 2>/dev/null || echo "   缩略图清理跳过"
fi

echo ""
echo "📊 清理后:"
df -h / | tail -1
echo ""

# 计算节省的空间
echo "✅ 清理完成！"
echo ""
echo "📝 安全说明:"
echo "   - 只删除临时文件、缓存和旧日志"
echo "   - 不删除系统文件、配置文件或用户数据"
echo "   - 保留最近的文件（tmp 7 天，cache 30 天）"
