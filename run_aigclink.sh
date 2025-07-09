#!/bin/bash

today=`date -u "+%Y-%m-%d"`
output_file="data/aigclink_${today}.json"

echo "执行AIGCLINK爬虫，输出到: ${output_file}"

# 直接执行脚本而不是作为模块导入
cd daily_arxiv/daily_arxiv/aigclink
python api_scraper.py --output "../../../${output_file}"

echo "完成！" 