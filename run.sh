today=`date -u "+%Y-%m-%d"`
cd daily_arxiv
scrapy crawl arxiv -o ../data/${today}.jsonl

cd ../ai
# 检查是否设置了SAVE_TO_DB环境变量
if [ "${SAVE_TO_DB}" = "true" ]; then
  python enhance.py --data ../data/${today}.jsonl --save-to-db
else
  python enhance.py --data ../data/${today}.jsonl
fi

cd ../to_md
python convert.py --data ../data/${today}_AI_enhanced_${LANGUAGE}.jsonl

cd ..
# python update_readme.py

ls data/*.jsonl | sed 's|data/||' > assets/file-list.txt
