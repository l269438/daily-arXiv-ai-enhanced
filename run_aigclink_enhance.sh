#!/bin/bash

today=`date -u "+%Y-%m-%d"`
input_file="data/aigclink_${today}.json"
output_file="data/aigclink_${today}_enhanced.json"

echo "执行AIGCLINK AI增强，输入: ${input_file}, 输出: ${output_file}"

# 检查输入文件是否存在
if [ ! -f "$input_file" ]; then
  echo "错误: 输入文件 ${input_file} 不存在"
  echo "请先运行 ./run_aigclink.sh 爬取数据"
  exit 1
fi

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

# 设置OpenAI API密钥（如果未设置）
if [ -z "$OPENAI_API_KEY" ]; then
  echo "请设置OpenAI API密钥："
  echo "export OPENAI_API_KEY=\"你的API密钥\""
  exit 1
fi

# 执行AI增强
cd daily_arxiv/daily_arxiv/aigclink
python ai_enhance.py --input "../../../${input_file}" --output "../../../${output_file}" --save-to-db

echo "完成！" 