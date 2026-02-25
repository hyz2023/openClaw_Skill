#!/bin/bash
# 磁盘监控脚本 - 检查磁盘使用率并发送警报

THRESHOLD=80
WORKSPACE="/home/ubuntu/.openclaw/workspace"

# 获取根分区使用率
USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')

echo "=== 磁盘使用监控 ==="
echo "时间: $(date)"
echo "根分区使用率: ${USAGE}%"
echo "阈值: ${THRESHOLD}%"
echo ""

# 显示详细使用情况
df -h / | tail -1

if [ "$USAGE" -ge "$THRESHOLD" ]; then
    echo ""
    echo "⚠️  警告：磁盘使用率超过 ${THRESHOLD}%！"
    echo ""
    
    # 显示最大的目录
    echo "📁 占用空间最大的前 10 个目录:"
    du -ah /home/ubuntu 2>/dev/null | sort -rh | head -10
    
    # 发送警报消息
    if [ -f "$WORKSPACE/.openclaw_channel" ]; then
        echo ""
        echo "📢 将发送警报通知..."
        # 这里可以通过 OpenClaw message 工具发送
    fi
    
    exit 1
else
    echo "✅ 磁盘使用正常"
    exit 0
fi
