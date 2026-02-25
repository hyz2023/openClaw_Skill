#!/bin/bash
# 菲律宾每周热门话题报告脚本
# 每周一 UTC 01:00 (菲律宾时间 09:00) 执行

cd /home/ubuntu/.openclaw/workspace

# 运行采集脚本
python3 scripts/ph_trending_topics.py > /tmp/ph_trending_report.txt 2>&1

# 显示报告
cat /tmp/ph_trending_report.txt

# 保存报告到 reports 目录
mkdir -p reports
cp /tmp/ph_trending_report.txt "reports/ph-trending-$(date +%Y-%m-%d).txt"

echo ""
echo "✅ 报告已保存到：reports/ph-trending-$(date +%Y-%m-%d).txt"
