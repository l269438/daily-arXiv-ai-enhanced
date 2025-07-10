#!/bin/bash

# AIGCLINK完整流程：爬取数据 -> AI增强 -> 存储MySQL
# 类似于arXiv的完整流程

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
today=`date -u "+%Y-%m-%d"`
echo "开始处理日期: ${today}"

# 设置文件路径
RAW_FILE="data/aigclink_${today}.json"
ENHANCED_FILE="data/aigclink_${today}_enhanced.json"

echo "========================================="
echo "步骤1: 爬取AIGCLINK数据"
echo "========================================="

# 进入AIGCLINK爬虫目录
cd daily_arxiv/daily_arxiv/aigclink

# 执行爬虫，保存原始数据
python api_scraper.py --output "../../../${RAW_FILE}"

# 检查爬取是否成功
if [ ! -f "../../../${RAW_FILE}" ]; then
  echo "错误: 数据爬取失败，文件 ${RAW_FILE} 不存在"
  exit 1
fi

echo "数据爬取完成，保存在: ${RAW_FILE}"

echo "========================================="
echo "步骤2: AI内容增强"
echo "========================================="

# 设置PYTHONPATH
export PYTHONPATH=$PYTHONPATH:$(pwd)/../../..

# 执行AI增强，根据SAVE_TO_DB环境变量决定是否保存到数据库
if [ "${SAVE_TO_DB}" = "true" ]; then
  echo "启用数据库存储模式"
  python ai_enhance.py --input "../../../${RAW_FILE}" --output "../../../${ENHANCED_FILE}" --save-to-db
else
  echo "仅文件存储模式"
  python ai_enhance.py --input "../../../${RAW_FILE}" --output "../../../${ENHANCED_FILE}"
fi

# 返回到根目录
cd ../../../

# 检查AI增强是否成功
if [ ! -f "${ENHANCED_FILE}" ]; then
  echo "错误: AI增强失败，文件 ${ENHANCED_FILE} 不存在"
  exit 1
fi

echo "AI增强完成，保存在: ${ENHANCED_FILE}"

echo "========================================="
echo "步骤3: 更新文件列表"
echo "========================================="

# 更新文件列表（包含所有数据文件）
ls data/*.json data/*.jsonl | sed 's|data/||' > assets/file-list.txt

echo "文件列表已更新"

echo "========================================="
echo "AIGCLINK完整流程执行完成！"
echo "========================================="
echo "原始数据: ${RAW_FILE}"
echo "增强数据: ${ENHANCED_FILE}"
if [ "${SAVE_TO_DB}" = "true" ]; then
  echo "数据已保存到MySQL数据库"
fi
echo "========================================="
