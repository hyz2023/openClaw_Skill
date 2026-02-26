#!/bin/bash
# ODPS 采集完成监控脚本

LOG_FILE="/home/ubuntu/.openclaw/workspace/odps_metadata_v2.log"
CHECK_INTERVAL=60  # 每 60 秒检查一次
MAX_WAIT=1800      # 最多等待 30 分钟

echo "🔍 开始监控 ODPS 元数据采集进度..."
echo "日志文件：$LOG_FILE"
echo "检查间隔：${CHECK_INTERVAL}秒"
echo ""

start_time=$(date +%s)

while true; do
    current_time=$(date +%s)
    elapsed=$((current_time - start_time))
    
    # 检查是否超时
    if [ $elapsed -gt $MAX_WAIT ]; then
        echo "⏰ 监控超时 (${MAX_WAIT}秒)"
        exit 1
    fi
    
    # 检查日志文件是否存在
    if [ ! -f "$LOG_FILE" ]; then
        echo "⏳ 等待日志文件生成..."
        sleep $CHECK_INTERVAL
        continue
    fi
    
    # 获取最新进度
    latest_progress=$(grep "⏰" "$LOG_FILE" | tail -1)
    
    if [ -z "$latest_progress" ]; then
        echo "⏳ 等待进度更新..."
        sleep $CHECK_INTERVAL
        continue
    fi
    
    # 提取进度百分比
    percentage=$(echo "$latest_progress" | grep -oP '\d+\.\d+%' | head -1)
    current_table=$(echo "$latest_progress" | grep "当前：" | cut -d'：' -f2 | cut -d' ' -f1)
    
    echo "📊 $(date '+%H:%M:%S') - 进度：$percentage 当前表：$current_table"
    
    # 检查是否完成 (95% 以上或找到完成标志)
    if grep -q "✅ 元数据采集完成" "$LOG_FILE" || \
       grep -q "采集完成" "$LOG_FILE" || \
       echo "$percentage" | grep -q "100.0%"; then
        echo ""
        echo "✅✅✅ 采集完成！✅✅✅"
        echo ""
        
        # 显示最终统计
        echo "📋 最终统计:"
        tail -50 "$LOG_FILE" | grep -E "总表数 | 总字段数 | 分区表数 | 输出文件"
        
        # 发送通知
        echo ""
        echo "📤 发送通知..."
        
        # 这里可以调用通知 API
        # 例如：curl -X POST "通知接口" -d "ODPS 元数据采集完成！"
        
        exit 0
    fi
    
    # 检查是否卡住 (连续两次检查进度不变)
    prev_percentage="$percentage"
    sleep $CHECK_INTERVAL
    
    latest_progress2=$(grep "⏰" "$LOG_FILE" | tail -1)
    percentage2=$(echo "$latest_progress2" | grep -oP '\d+\.\d+%' | head -1)
    
    if [ "$prev_percentage" = "$percentage2" ] && [ -n "$percentage2" ]; then
        echo "⚠️  警告：进度停滞在 $percentage2，可能卡住了"
        # 继续等待，不退出
    fi
done
