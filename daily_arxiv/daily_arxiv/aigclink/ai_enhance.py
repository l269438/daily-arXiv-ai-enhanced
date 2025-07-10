#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
AIGCLINK AI增强模块 - 使用LLM提取产品的专利点和创新点
"""

import os
import sys
import json
import logging
from datetime import datetime

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

try:
    from langchain_openai import ChatOpenAI
    from langchain.prompts import ChatPromptTemplate
    # 使用绝对导入
    try:
        from daily_arxiv.daily_arxiv.aigclink.ai_structure import AIGCLINKAnalysis
    except ImportError:
        # 如果绝对导入失败，尝试相对导入
        try:
            from .ai_structure import AIGCLINKAnalysis
        except ImportError:
            # 最后尝试直接导入(在同一目录下)
            from ai_structure import AIGCLINKAnalysis
    HAS_LANGCHAIN = True
except ImportError:
    logger.warning("未安装langchain或langchain_openai，AI增强功能将不可用")
    logger.warning("安装命令: pip install langchain langchain_openai")
    HAS_LANGCHAIN = False

# 尝试导入数据库模块
try:
    # 使用绝对导入
    try:
        from daily_arxiv.daily_arxiv.aigclink.db import save_aigclink_analysis
    except ImportError:
        # 如果绝对导入失败，尝试相对导入
        try:
            from .db import save_aigclink_analysis
        except ImportError:
            # 最后尝试直接导入(在同一目录下)
            from db import save_aigclink_analysis
    HAS_DB_MODULE = True
except ImportError:
    logger.warning("无法导入数据库模块，数据库功能将不可用")
    HAS_DB_MODULE = False

# 系统提示词
SYSTEM_PROMPT = """
你是一位专业的AI产品分析师，擅长分析AI产品的创新点和潜在专利点。
你的任务是分析一个AI产品的描述，并提取以下信息：
1. 产品摘要：简要概述产品的主要功能和用途
2. 关键特性：列出产品的主要特性和功能
3. 创新点：分析产品的创新之处
4. 专利点：提取可能的专利点或专利申请方向
5. 应用场景：列出产品的主要应用场景
6. 技术栈：推测产品可能使用的技术栈
7. 市场潜力：分析产品的市场潜力
8. 改进建议：提出可能的改进方向

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

def analyze_product(product_data, model_name=None):
    """使用LLM分析产品数据"""
    if not HAS_LANGCHAIN:
        logger.error("未安装langchain，无法进行AI分析")
        return None
    
    # 获取OpenAI API密钥
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        logger.error("未设置OPENAI_API_KEY环境变量")
        return None
    
    # 设置模型名称
    if not model_name:
        model_name = os.environ.get("MODEL_NAME", "gpt-4o")
    
    # 获取API基础URL（如果有）
    api_base = os.environ.get("OPENAI_BASE_URL", None)
    
    logger.info(f"使用模型 {model_name} 分析产品")
    
    try:
        # 创建LLM
        llm_kwargs = {
            "model": model_name,
            "temperature": 0.2,
            "api_key": api_key
        }
        
        # 如果设置了API基础URL，则添加到参数中
        if api_base:
            llm_kwargs["base_url"] = api_base
            
        llm = ChatOpenAI(**llm_kwargs).with_structured_output(AIGCLINKAnalysis)
        
        # 创建提示词模板
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            ("human", HUMAN_PROMPT)
        ])
        
        # 创建链
        chain = prompt_template | llm
        
        # 准备输入数据
        input_data = {
            "product_name": product_data.get("product_name", ""),
            "short_description": product_data.get("short_description", ""),
            "summary": product_data.get("summary", ""),
            "category": product_data.get("category", ""),
            "tags": ", ".join(product_data.get("tags", [])) if isinstance(product_data.get("tags"), list) else product_data.get("tags", ""),
            "industry": product_data.get("industry", "")
        }
        
        # 调用LLM
        logger.info(f"开始分析产品: {input_data['product_name']}")
        result = chain.invoke(input_data)
        logger.info(f"产品分析完成: {input_data['product_name']}")
        
        return result
    
    except Exception as e:
        logger.error(f"AI分析出错: {e}")
        import traceback
        traceback.print_exc()
        return None

def enhance_products(products, save_to_db=False):
    """增强产品数据"""
    enhanced_products = []
    
    for product in products:
        # 跳过没有产品名的项
        if not product.get("product_name"):
            continue
        
        # 分析产品
        analysis = analyze_product(product)
        
        if analysis:
            # 将分析结果添加到产品数据
            product["AI"] = analysis.model_dump()
            
            # 保存到数据库
            if save_to_db and HAS_DB_MODULE:
                try:
                    save_aigclink_analysis(product["id"], product["AI"])
                    logger.info(f"产品 {product['product_name']} 的AI分析已保存到数据库")
                except Exception as e:
                    logger.error(f"保存AI分析到数据库失败: {e}")
        
        enhanced_products.append(product)
    
    return enhanced_products

def enhance_aigclink_data(input_file, output_file=None, save_to_db=False):
    """增强AIGCLINK数据"""
    # 读取输入文件
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        logger.error(f"读取输入文件失败: {e}")
        return False
    
    # 检查数据格式
    if not isinstance(data, dict) or "items" not in data:
        logger.error("输入数据格式不正确")
        return False
    
    # 增强产品数据
    enhanced_items = enhance_products(data["items"], save_to_db)
    
    # 更新数据
    data["items"] = enhanced_items
    data["enhanced"] = True
    data["enhanced_timestamp"] = datetime.now().isoformat()
    
    # 保存结果
    if not output_file:
        output_file = input_file.replace('.json', '_enhanced.json')
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"增强结果已保存到: {output_file}")
        return True
    except Exception as e:
        logger.error(f"保存结果失败: {e}")
        return False

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='AIGCLINK AI增强工具')
    parser.add_argument('--input', type=str, required=True, help='输入文件路径')
    parser.add_argument('--output', type=str, help='输出文件路径')
    parser.add_argument('--model', type=str, help='使用的模型名称，默认使用环境变量MODEL_NAME或gpt-4o')
    parser.add_argument('--save-to-db', action='store_true', help='将分析结果保存到数据库')
    
    args = parser.parse_args()
    
    # 设置模型名称
    if args.model:
        os.environ["MODEL_NAME"] = args.model
    
    # 增强数据
    success = enhance_aigclink_data(args.input, args.output, args.save_to_db)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 