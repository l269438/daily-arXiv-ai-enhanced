#!/bin/bash

today=`date -u "+%Y-%m-%d"`
output_file="data/aigclink_${today}.json"

echo "执行AIGCLINK爬虫，输出到: ${output_file}"

# 设置数据库环境变量（如果未设置）
if [ -z "$DB_USER" ]; then
  echo "请设置数据库环境变量："
  echo "export DB_USER=\"用户名\""
  echo "export DB_PASSWORD=\"密码\""
  echo "export DB_HOST=\"主机地址\""
  echo "export DB_PORT=\"端口\""
  echo "export DB_NAME=\"数据库名\""
  echo "export SAVE_TO_DB=\"true\""
fi

# 直接执行脚本而不是作为模块导入
cd daily_arxiv/daily_arxiv/aigclink

# 执行爬虫，添加--save-to-db参数
python api_scraper.py --output "../../../${output_file}" --save-to-db

echo "完成！" 