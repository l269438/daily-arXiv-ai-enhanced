#!/bin/bash

# 加载环境变量
if [ -f .env ]; then
  source .env
fi

# 确保有OpenAI API密钥
if [ -z "$OPENAI_API_KEY" ]; then
  echo "错误: 未设置OPENAI_API_KEY环境变量"
  exit 1
fi

# 设置日期
PROCESS_DATE=$(date +%Y-%m-%d)
INPUT_FILE="data/aigclink_${PROCESS_DATE}.json"
OUTPUT_FILE="data/aigclink_${PROCESS_DATE}_enhanced.json"

# 检查输入文件是否存在
if [ ! -f "$INPUT_FILE" ]; then
  echo "错误: 输入文件 ${INPUT_FILE} 不存在"
  echo "请先运行 ./run_aigclink.sh 爬取数据"
  exit 1
fi

# 设置PYTHONPATH
export PYTHONPATH=$PYTHONPATH:$(pwd)

# 执行AI增强
cd daily_arxiv/daily_arxiv/aigclink
python ai_enhance.py --input "../../../${INPUT_FILE}" --output "../../../${OUTPUT_FILE}" --save-to-db

# 返回到原目录
cd ../../../
echo "增强完成，结果保存在 ${OUTPUT_FILE}" 