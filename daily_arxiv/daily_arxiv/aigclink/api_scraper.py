#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
AIGCLINK数据爬取工具 - 简化版
直接调用Notion API获取数据，清洗数据并生成英文键名的JSON格式
"""

import os
import sys
import json
import logging
import requests
import argparse
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

# 尝试导入数据库模块
try:
    from db import init_aigclink_table, save_aigclink_data
    HAS_DB_MODULE = True
except ImportError:
    logger.warning("无法导入数据库模块，数据库功能将不可用")
    HAS_DB_MODULE = False

def call_notion_api(url=None):
    """调用Notion API获取数据"""
    if not url:
        url = "https://d.aigclink.ai/?v=8f252a54730e49f4b8caf897b7ae49f6"
    
    logger.info(f"处理URL: {url}")
    
    # API端点
    api_endpoint = "https://d.aigclink.ai/api/v3/queryCollection?src=initial_load"
    
    # 请求头
    headers = {
        "accept": "*/*",
        "accept-language": "zh-CN,zh;q=0.9,en;q=0.8",
        "content-type": "application/json",
        "notion-audit-log-platform": "web",
        "notion-client-version": "23.13.0.4131",
        "origin": "https://d.aigclink.ai",
        "referer": url,
        "sec-ch-ua": '"Chromium";v="128", "Not;A=Brand";v="24", "Google Chrome";v="128"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "x-notion-space-id": "4ce4d650-ed04-405e-a492-bd790ae10569"
    }
    
    # 从URL中提取视图ID
    view_id = url.split("?v=")[1].split("&")[0] if "?v=" in url else None
    if not view_id:
        logger.error("无法从URL中提取视图ID")
        return None
    
    logger.info(f"提取的视图ID: {view_id}")
    
    # 构造请求体
    data = {
        "source": {
            "type": "collection",
            "id": "bf0ecb26-74f9-4cb9-8d02-95b0ea44beab",
            "spaceId": "4ce4d650-ed04-405e-a492-bd790ae10569"
        },
        "collectionView": {
            "id": view_id,
            "spaceId": "4ce4d650-ed04-405e-a492-bd790ae10569"
        },
        "loader": {
            "reducers": {
                "collection_group_results": {
                    "type": "results",
                    "limit": 50,
                    "loadContentCover": True
                }
            },
            "filter": {
                "operator": "and",
                "filters": [
                    {
                        "filter": {
                            "value": [
                                {"type": "exact", "value": "线下活动"},
                                {"type": "exact", "value": "会议"},
                                {"type": "exact", "value": "about"}
                            ],
                            "operator": "enum_does_not_contain"
                        },
                        "property": ">Dc>"
                    }
                ]
            },
            "sort": [
                {"property": "vuJC", "direction": "descending"}
            ],
            "searchQuery": "",
            "userTimeZone": "Asia/Shanghai"
        }
    }
    
    try:
        logger.info("调用Notion API...")
        logger.debug(f"请求URL: {api_endpoint}")
        logger.debug(f"请求头: {headers}")
        logger.debug(f"请求体: {json.dumps(data, ensure_ascii=False)}")
        
        response = requests.post(api_endpoint, headers=headers, json=data, timeout=30)
        
        if response.status_code == 200:
            logger.info("API调用成功")
            return response.json()
        else:
            logger.error(f"API调用失败，状态码: {response.status_code}")
            logger.error(f"响应内容: {response.text[:500]}")
            return None
    except Exception as e:
        logger.error(f"API调用出错: {e}")
        import traceback
        traceback.print_exc()
        return None

def process_notion_data(data):
    """处理Notion API返回的数据"""
    if not data:
        logger.error("没有数据可处理")
        return None
    
    # 检查是否有recordMap数据
    if "recordMap" not in data:
        logger.error("数据中没有recordMap字段")
        return None
    
    logger.info("发现recordMap数据，开始处理...")
    
    record_map = data["recordMap"]
    
    # 提取集合信息
    collection_id = None
    collection_data = None
    property_map = {}
    
    if "collection" in record_map:
        for coll_id, coll_data in record_map["collection"].items():
            try:
                # 处理嵌套的value结构 - 修正处理方式
                coll_value = None
                if "value" in coll_data:
                    if isinstance(coll_data["value"], dict) and "value" in coll_data["value"]:
                        coll_value = coll_data["value"]["value"]
                    else:
                        coll_value = coll_data["value"]
                
                if coll_value and isinstance(coll_value, dict):
                    collection_id = coll_id
                    collection_data = coll_value
                    
                    # 提取属性映射
                    schema = coll_value.get("schema", {})
                    for prop_id, prop_data in schema.items():
                        property_map[prop_id] = {
                            "name": prop_data.get("name", ""),
                            "type": prop_data.get("type", "")
                        }
                    
                    logger.info(f"提取到集合信息，ID: {collection_id}")
                    break
            except Exception as e:
                logger.error(f"处理集合信息时出错: {e}")
                import traceback
                traceback.print_exc()
    
    # 提取块数据
    blocks = record_map.get("block", {})
    logger.info(f"发现 {len(blocks)} 个块数据")
    
    # 找到所有页面块
    pages = []
    for block_id, block_data in blocks.items():
        try:
            # 处理嵌套的value结构 - 修正处理方式
            block_value = None
            if "value" in block_data:
                if isinstance(block_data["value"], dict) and "value" in block_data["value"]:
                    block_value = block_data["value"]["value"]
                else:
                    block_value = block_data["value"]
            
            if block_value and isinstance(block_value, dict) and block_value.get("type") == "page":
                pages.append(block_value)
        except Exception as e:
            logger.error(f"处理块 {block_id} 时出错: {e}")
            import traceback
            traceback.print_exc()
    
    logger.info(f"找到 {len(pages)} 个页面块")
    
    # 创建结果
    result = {
        "pages": pages,
        "property_map": property_map
    }
    
    logger.info(f"成功处理 {len(pages)} 个页面")
    return result

def convert_to_friendly_format(data):
    """将原始数据转换为友好格式"""
    if not data or "pages" not in data:
        logger.error("没有页面数据可转换")
        return None
    
    pages = data["pages"]
    property_map = data.get("property_map", {})
    
    friendly_items = []
    
    for page in pages:
        item = {
            "id": page.get("id", ""),
            "created_time": page.get("created_time", 0),
            "last_edited_time": page.get("last_edited_time", 0)
        }
        
        # 提取属性
        properties = page.get("properties", {})
        for prop_id, prop_value in properties.items():
            # 获取属性名称
            prop_name = property_map.get(prop_id, {}).get("name", prop_id) if prop_id in property_map else prop_id
            
            # 提取文本内容
            text_content = extract_text_from_property(prop_value)
            if text_content is not None:
                item[prop_name] = text_content
        
        friendly_items.append(item)
    
    # 创建结果
    result = {
        "timestamp": datetime.now().isoformat(),
        "total_count": len(friendly_items),
        "items": friendly_items
    }
    
    return result

def extract_text_from_property(prop_value):
    """从Notion属性中提取纯文本内容"""
    if not prop_value:
        return None
    
    # 如果是字符串，直接返回
    if isinstance(prop_value, str):
        return prop_value
    
    # 如果是列表，尝试提取文本
    if isinstance(prop_value, list):
        if len(prop_value) == 0:
            return None
        
        # 处理标题、文本等属性
        if isinstance(prop_value[0], list):
            text_parts = []
            for part in prop_value:
                if isinstance(part, list) and len(part) > 0:
                    # 确保正确处理中文字符
                    if isinstance(part[0], str):
                        text_parts.append(part[0])
            return "".join(text_parts)
        
        # 处理多选属性
        if all(isinstance(item, str) for item in prop_value):
            return prop_value
        
        # 处理复杂结构
        try:
            return json.dumps(prop_value, ensure_ascii=False)
        except:
            return str(prop_value)
    
    # 如果是字典，转为JSON字符串
    if isinstance(prop_value, dict):
        try:
            return json.dumps(prop_value, ensure_ascii=False)
        except:
            return str(prop_value)
    
    # 其他类型，转为字符串
    return str(prop_value)

def convert_to_english_keys(data):
    """将数据转换为使用英文键名的格式"""
    if not data or "items" not in data:
        logger.error("没有数据项可转换")
        return None
    
    items = data["items"]
    
    # 中文属性名到英文属性名的映射
    cn_to_en_map = {
        "标签": "tags",
        "摘要": "summary",
        "网址": "url",
        "分类": "category",
        "岗位辅助": "job_assistance",
        "产品名": "product_name",
        "行业": "industry",
        "收录时间": "collection_date",
        "一句话简介": "short_description",
        "title": "title"
    }
    
    english_items = []
    
    for item in items:
        english_item = {
            "id": item.get("id", ""),
            "created_time": item.get("created_time", 0),
            "last_edited_time": item.get("last_edited_time", 0)
        }
        
        # 转换键名
        for key, value in item.items():
            # 跳过已处理的基本字段
            if key in ["id", "created_time", "last_edited_time"]:
                continue
            
            # 使用英文键名
            en_key = cn_to_en_map.get(key, key)
            english_item[en_key] = value
        
        english_items.append(english_item)
    
    # 创建结果
    result = {
        "timestamp": datetime.now().isoformat(),
        "total_count": len(english_items),
        "items": english_items
    }
    
    return result

def save_json(data, output_file, pretty=True):
    """将数据保存为JSON文件"""
    try:
        # 确保输出目录存在
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            if pretty:
                json.dump(data, f, ensure_ascii=False, indent=2)
            else:
                json.dump(data, f, ensure_ascii=False)
        
        logger.info(f"结果已保存到: {output_file}")
        return True
    
    except Exception as e:
        logger.error(f"保存结果时出错: {e}")
        return False

def scrape_aigclink(url=None, output_file=None, english_keys=True, save_to_db=False):
    """爬取AIGCLINK数据并保存为JSON"""
    # 1. 调用API获取数据
    raw_data = call_notion_api(url)
    if not raw_data:
        return False
    
    # 2. 处理数据
    processed_data = process_notion_data(raw_data)
    if not processed_data:
        return False
    
    # 3. 转换为友好格式
    friendly_data = convert_to_friendly_format(processed_data)
    if not friendly_data:
        return False
    
    # 4. 如果需要，转换为英文键名
    final_data = convert_to_english_keys(friendly_data) if english_keys else friendly_data
    
    # 5. 如果需要，保存到数据库
    save_to_db_env = os.environ.get("SAVE_TO_DB", "").lower() == "true"
    if (save_to_db or save_to_db_env) and HAS_DB_MODULE:
        try:
            init_aigclink_table()
            save_aigclink_data(final_data["items"])
            logger.info(f"已将 {len(final_data['items'])} 条数据保存到数据库")
        except Exception as e:
            logger.error(f"保存到数据库失败: {e}")
            import traceback
            traceback.print_exc()
    
    # 6. 保存结果
    if not output_file:
        timestamp = datetime.now().strftime("%Y-%m-%d")
        prefix = "aigclink_en" if english_keys else "aigclink"
        # 使用绝对路径
        # 获取当前脚本的绝对路径
        current_script_path = os.path.abspath(__file__)
        # 获取项目根目录路径
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_script_path))))
        # 构建输出文件路径
        output_file = os.path.join(project_root, f"data/{prefix}_{timestamp}.json")
        logger.info(f"项目根目录: {project_root}")
    
    return save_json(final_data, output_file)

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='AIGCLINK数据爬取工具 - 简化版')
    parser.add_argument('--url', type=str, help='AIGCLINK网址，默认为首页')
    parser.add_argument('--output', type=str, help='输出文件路径')
    parser.add_argument('--chinese-keys', action='store_true', help='使用中文键名（默认使用英文键名）')
    parser.add_argument('--compact', action='store_true', help='输出紧凑的JSON格式（无缩进）')
    parser.add_argument('--verbose', action='store_true', help='显示详细日志')
    parser.add_argument('--save-to-db', action='store_true', help='将数据保存到数据库')
    
    args = parser.parse_args()
    
    # 设置日志级别
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    # 爬取数据
    success = scrape_aigclink(args.url, args.output, not args.chinese_keys, args.save_to_db)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 