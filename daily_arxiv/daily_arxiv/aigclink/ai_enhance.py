#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
AIGCLINK AI增强模块 - 使用LLM提取产品的专利点和创新点
"""

import os
import json
import sys
from datetime import datetime

import dotenv
import argparse

import langchain_core.exceptions
from langchain_openai import ChatOpenAI
from langchain.prompts import (
  ChatPromptTemplate,
  SystemMessagePromptTemplate,
  HumanMessagePromptTemplate,
)

# 尝试导入所需模块
try:
    # 尝试从当前目录导入
    try:
        from ai_structure import AIGCLINKAnalysis
    except ImportError:
        # 尝试相对导入
        try:
            from .ai_structure import AIGCLINKAnalysis
        except ImportError:
            # 尝试绝对导入
            from daily_arxiv.daily_arxiv.aigclink.ai_structure import AIGCLINKAnalysis

    try:
        from db import save_aigclink_analysis, init_aigclink_table
    except ImportError:
        try:
            from .db import save_aigclink_analysis, init_aigclink_table
        except ImportError:
            from daily_arxiv.daily_arxiv.aigclink.db import save_aigclink_analysis, init_aigclink_table
except Exception as e:
    print(f"导入模块错误: {e}", file=sys.stderr)
    sys.exit(1)

if os.path.exists('.env'):
    dotenv.load_dotenv()

# 系统提示词
SYSTEM_PROMPT = """
你是一位专业的AI产品分析师，擅长分析AI产品的创新点和潜在专利点。
你的任务是分析一个AI产品的描述，并提取以下信息：
1. summary: 产品的简短摘要，概述其主要功能和用途
2. key_features: 产品的关键特性，用逗号分隔
3. innovation_points: 产品的创新点分析
4. patent_ideas: 从产品描述中提取的可能的专利点
5. use_cases: 产品的主要应用场景
6. tech_stack: 推测的产品技术栈
7. market_potential: 产品的市场潜力分析
8. improvement_suggestions: 对产品的改进建议

请确保你的分析客观、专业，并基于提供的产品描述。
"""

# 人类提示词模板
HUMAN_PROMPT = """
以下是一个AI产品的信息：

产品名称: {product_name}
简介: {short_description}
详细描述: {summary}
分类: {category}
标签: {tags}
行业: {industry}

请分析这个产品并提取关键信息。
"""

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='AIGCLINK AI增强工具')
    parser.add_argument('--input', type=str, required=True, help='输入文件路径')
    parser.add_argument('--output', type=str, help='输出文件路径')
    parser.add_argument('--save-to-db', action='store_true', help='将分析结果保存到数据库')
    return parser.parse_args()

def main():
    args = parse_args()
    model_name = os.environ.get("MODEL_NAME", 'gpt-4o')
    language = os.environ.get("LANGUAGE", 'Chinese')
    save_to_db = args.save_to_db or os.environ.get("SAVE_TO_DB", "false").lower() == "true"
    
    # 如果需要保存到数据库，初始化数据库
    if save_to_db:
        try:
            init_aigclink_table()
            print("数据库初始化成功", file=sys.stderr)
        except Exception as e:
            print(f"数据库初始化错误: {e}", file=sys.stderr)
            save_to_db = False
    
    # 读取输入文件
    try:
        with open(args.input, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"读取输入文件失败: {e}", file=sys.stderr)
        return 1
    
    # 检查数据格式
    if not isinstance(data, dict) or "items" not in data:
        print("输入数据格式不正确", file=sys.stderr)
        return 1
    
    products = data["items"]
    
    # 去重
    seen_ids = set()
    unique_products = []
    for item in products:
        if item['id'] not in seen_ids:
            seen_ids.add(item['id'])
            unique_products.append(item)
    
    products = unique_products
    
    print('Open:', args.input, file=sys.stderr)
    
    # 创建LLM
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        print("未设置OPENAI_API_KEY环境变量", file=sys.stderr)
        return 1
    
    api_base = os.environ.get("OPENAI_BASE_URL", None)
    llm_kwargs = {
        "model": model_name,
        "temperature": 0.2,
        "api_key": api_key
    }
    
    if api_base:
        llm_kwargs["base_url"] = api_base
    
    llm = ChatOpenAI(**llm_kwargs).with_structured_output(AIGCLINKAnalysis, method="function_calling")
    print('Connect to:', model_name, file=sys.stderr)
    
    # 创建提示词模板
    prompt_template = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(SYSTEM_PROMPT),
        HumanMessagePromptTemplate.from_template(template=HUMAN_PROMPT)
    ])
    
    chain = prompt_template | llm
    
    # 确定输出文件
    if not args.output:
        output_file = args.input.replace('.json', '_enhanced.json')
    else:
        output_file = args.output
    
    # 处理每个产品
    for idx, product in enumerate(products):
        try:
            # 准备输入数据
            input_data = {
                "product_name": product.get("product_name", ""),
                "short_description": product.get("short_description", ""),
                "summary": product.get("summary", ""),
                "category": product.get("category", ""),
                "tags": ", ".join(product.get("tags", [])) if isinstance(product.get("tags"), list) else product.get("tags", ""),
                "industry": product.get("industry", "")
            }
            
            # 调用LLM
            print(f"开始分析产品 {idx+1}/{len(products)}: {input_data['product_name']}", file=sys.stderr)
            response = chain.invoke(input_data)

            # 处理响应
            if use_structured:
                # Structured output模式
                product['AI'] = response.model_dump()
            else:
                # 普通模式，需要解析JSON
                try:
                    import json
                    if hasattr(response, 'content'):
                        response_text = response.content
                    else:
                        response_text = str(response)

                    # 尝试提取JSON部分
                    start_idx = response_text.find('{')
                    end_idx = response_text.rfind('}') + 1
                    if start_idx != -1 and end_idx > start_idx:
                        json_str = response_text[start_idx:end_idx]
                        parsed_result = json.loads(json_str)
                        product['AI'] = parsed_result
                    else:
                        raise ValueError("No JSON found in response")

                except (json.JSONDecodeError, ValueError) as e:
                    print(f"解析JSON失败: {e}", file=sys.stderr)
                    print(f"原始响应: {response_text[:200]}...", file=sys.stderr)
                    # 创建默认结构
                    product['AI'] = {
                        "summary": f"解析失败: {str(e)}",
                        "key_features": [],
                        "innovation_points": [],
                        "patent_ideas": [],
                        "use_cases": [],
                        "tech_stack": [],
                        "market_potential": f"解析失败: {str(e)}",
                        "improvement_suggestions": []
                    }
            
            # 保存到数据库
            if save_to_db:
                try:
                    success = save_aigclink_analysis(product["id"], product["AI"])
                    if success:
                        print(f"产品 {product['id']} 已保存到数据库", file=sys.stderr)
                    else:
                        print(f"保存产品 {product['id']} 到数据库失败", file=sys.stderr)
                except Exception as e:
                    print(f"保存到数据库时出错: {e}", file=sys.stderr)
                    
        except langchain_core.exceptions.OutputParserException as e:
            print(f"{product.get('id', 'unknown')} 发生错误: {e}", file=sys.stderr)
            product['AI'] = {
                "summary": "Error",
                "key_features": [],
                "innovation_points": [],
                "patent_ideas": [],
                "use_cases": [],
                "tech_stack": [],
                "market_potential": "Error",
                "improvement_suggestions": []
            }
        
        print(f"完成 {idx+1}/{len(products)}", file=sys.stderr)
    
    # 更新数据
    data["items"] = products
    data["enhanced"] = True
    data["enhanced_timestamp"] = datetime.now().isoformat()
    
    # 保存结果
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"增强结果已保存到: {output_file}", file=sys.stderr)
        return 0
    except Exception as e:
        print(f"保存结果失败: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main()) 