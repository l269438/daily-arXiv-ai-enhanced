#!/bin/bash

today=`date -u "+%Y-%m-%d"`
output_file="data/aigclink_${today}.json"

echo "执行AIGCLINK爬虫，输出到: ${output_file}"
python -m daily_arxiv.aigclink --output "${output_file}"

echo "完成！" 