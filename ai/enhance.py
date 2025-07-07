import os
import json
import sys

import dotenv
import argparse

import langchain_core.exceptions
from langchain_openai import ChatOpenAI
from langchain.prompts import (
  ChatPromptTemplate,
  SystemMessagePromptTemplate,
  HumanMessagePromptTemplate,
)
from structure import Structure
from db import save_paper_with_analysis, init_db  # 导入数据库函数

if os.path.exists('.env'):
    dotenv.load_dotenv()
template = open("template.txt", "r").read()
system = open("system.txt", "r").read()

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=str, required=True, help="jsonline data file")
    parser.add_argument("--save-to-db", action="store_true", help="Save data to MySQL database")
    return parser.parse_args()

def main():
    args = parse_args()
    model_name = os.environ.get("MODEL_NAME", 'deepseek-chat')
    language = os.environ.get("LANGUAGE", 'Chinese')
    save_to_db = args.save_to_db or os.environ.get("SAVE_TO_DB", "false").lower() == "true"

    # 如果需要保存到数据库，初始化数据库
    if save_to_db:
        try:
            init_db()
            print("数据库初始化成功", file=sys.stderr)
        except Exception as e:
            print(f"数据库初始化错误: {e}", file=sys.stderr)
            save_to_db = False

    data = []
    with open(args.data, "r") as f:
        for line in f:
            data.append(json.loads(line))

    seen_ids = set()
    unique_data = []
    for item in data:
        if item['id'] not in seen_ids:
            seen_ids.add(item['id'])
            unique_data.append(item)

    data = unique_data

    print('Open:', args.data, file=sys.stderr)

    llm = ChatOpenAI(model=model_name).with_structured_output(Structure, method="function_calling")
    print('Connect to:', model_name, file=sys.stderr)
    prompt_template = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(system),
        HumanMessagePromptTemplate.from_template(template=template)
    ])

    chain = prompt_template | llm

    # 创建输出文件
    output_file = args.data.replace('.jsonl', f'_AI_enhanced_{language}.jsonl')
    # 确保输出文件是空的
    with open(output_file, "w") as f:
        pass

    for idx, d in enumerate(data):
        try:
            response: Structure = chain.invoke({
                "language": language,
                "content": d['summary']
            })
            d['AI'] = response.model_dump()
            
            # 保存到数据库
            if save_to_db:
                success = save_paper_with_analysis(d)
                if success:
                    print(f"论文 {d['id']} 已保存到数据库", file=sys.stderr)
                else:
                    print(f"保存论文 {d['id']} 到数据库失败", file=sys.stderr)
                    
        except langchain_core.exceptions.OutputParserException as e:
            print(f"{d['id']} 发生错误: {e}", file=sys.stderr)
            d['AI'] = {
                 "tldr": "Error",
                 "motivation": "Error",
                 "method": "Error",
                 "result": "Error",
                 "conclusion": "Error"
            }
            
        # 追加到输出文件
        with open(output_file, "a") as f:
            f.write(json.dumps(d) + "\n")

        print(f"完成 {idx+1}/{len(data)}", file=sys.stderr)

if __name__ == "__main__":
    main()
