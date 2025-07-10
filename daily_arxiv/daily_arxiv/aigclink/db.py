#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
AIGCLINK数据库模块 - 用于将AIGCLINK数据保存到MySQL数据库
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

# 尝试导入pymysql
try:
    import pymysql
    HAS_PYMYSQL = True
except ImportError:
    logger.warning("未安装pymysql，数据库功能将不可用。安装命令: pip install pymysql")
    HAS_PYMYSQL = False

# 从环境变量获取数据库连接信息
DB_USER = os.environ.get("DB_USER", "")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
DB_HOST = os.environ.get("DB_HOST", "")
DB_PORT = int(os.environ.get("DB_PORT", "3306"))
DB_NAME = os.environ.get("DB_NAME", "")
SAVE_TO_DB = os.environ.get("SAVE_TO_DB", "false").lower() == "true"

# 自定义JSON编码函数，确保中文正常显示
def json_dumps_chinese(obj):
    return json.dumps(obj, ensure_ascii=False)

def get_connection():
    """获取数据库连接"""
    if not HAS_PYMYSQL:
        logger.error("未安装pymysql，无法连接数据库")
        return None
    
    try:
        logger.info(f"正在连接数据库: {DB_HOST}:{DB_PORT}/{DB_NAME}")
        connection = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT,
            database=DB_NAME,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor,
            connect_timeout=10
        )
        logger.info("数据库连接成功")
        return connection
    except Exception as e:
        logger.error(f"数据库连接错误: {e}")
        return None

def init_aigclink_table():
    """初始化AIGCLINK数据表"""
    if not SAVE_TO_DB:
        logger.info("未启用数据库存储，跳过表初始化")
        return False
    
    logger.info("开始初始化AIGCLINK数据表")
    
    # 首先创建数据库（如果不存在）
    try:
        # 连接到MySQL服务器（不指定数据库）
        connection = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT
        )
        
        with connection.cursor() as cursor:
            # 创建数据库（如果不存在）
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci")
            logger.info(f"数据库 '{DB_NAME}' 已创建或已存在")
            
            # 切换到新创建的数据库
            cursor.execute(f"USE `{DB_NAME}`")
            
            # 创建aigclink_products表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS `aigclink_products` (
                  `id` varchar(50) COLLATE utf8mb4_general_ci NOT NULL,
                  `product_name` varchar(255) COLLATE utf8mb4_general_ci NOT NULL,
                  `short_description` text COLLATE utf8mb4_general_ci,
                  `summary` text COLLATE utf8mb4_general_ci,
                  `url` varchar(500) COLLATE utf8mb4_general_ci,
                  `category` varchar(100) COLLATE utf8mb4_general_ci,
                  `tags` text COLLATE utf8mb4_general_ci,
                  `industry` varchar(100) COLLATE utf8mb4_general_ci,
                  `job_assistance` varchar(100) COLLATE utf8mb4_general_ci,
                  `created_time` bigint,
                  `last_edited_time` bigint,
                  `collection_date` datetime NOT NULL,
                  PRIMARY KEY (`id`)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
            """)
            logger.info("aigclink_products表已创建或已存在")
            
            # 创建aigclink_analysis表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS `aigclink_analysis` (
                  `id` int NOT NULL AUTO_INCREMENT,
                  `product_id` varchar(50) COLLATE utf8mb4_general_ci NOT NULL,
                  `summary` text COLLATE utf8mb4_general_ci,
                  `key_features` text COLLATE utf8mb4_general_ci,
                  `innovation_points` text COLLATE utf8mb4_general_ci,
                  `patent_ideas` text COLLATE utf8mb4_general_ci,
                  `use_cases` text COLLATE utf8mb4_general_ci,
                  `tech_stack` text COLLATE utf8mb4_general_ci,
                  `market_potential` text COLLATE utf8mb4_general_ci,
                  `improvement_suggestions` text COLLATE utf8mb4_general_ci,
                  `created_at` datetime NOT NULL,
                  PRIMARY KEY (`id`),
                  KEY `product_id` (`product_id`),
                  CONSTRAINT `aigclink_analysis_ibfk_1` FOREIGN KEY (`product_id`) REFERENCES `aigclink_products` (`id`)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
            """)
            logger.info("aigclink_analysis表已创建或已存在")
        
        connection.commit()
        connection.close()
        logger.info("表初始化成功")
        return True
    except Exception as e:
        logger.error(f"初始化AIGCLINK表错误: {e}")
        return False

def save_aigclink_data(items):
    """保存AIGCLINK数据到数据库"""
    if not SAVE_TO_DB:
        logger.info("未启用数据库存储，跳过数据保存")
        return False
    
    if not items or len(items) == 0:
        logger.warning("没有数据需要保存")
        return False
    
    logger.info(f"开始保存 {len(items)} 条数据到数据库")
    
    connection = get_connection()
    if not connection:
        logger.error("无法获取数据库连接，数据保存失败")
        return False
    
    try:
        with connection.cursor() as cursor:
            inserted_count = 0
            updated_count = 0
            
            for item in items:
                # 检查产品是否已存在
                cursor.execute("SELECT id FROM aigclink_products WHERE id = %s", (item['id'],))
                existing_product = cursor.fetchone()
                
                if not existing_product:
                    # 插入新产品
                    sql = """
                        INSERT INTO aigclink_products 
                        (id, product_name, short_description, summary, url, category, 
                        tags, industry, job_assistance, created_time, last_edited_time, collection_date)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    cursor.execute(sql, (
                        item['id'],
                        item.get('product_name', ''),
                        item.get('short_description', ''),
                        item.get('summary', ''),
                        item.get('url', ''),
                        item.get('category', ''),
                        json_dumps_chinese(item.get('tags', [])),
                        item.get('industry', ''),
                        item.get('job_assistance', ''),
                        item.get('created_time', 0),
                        item.get('last_edited_time', 0),
                        datetime.now()
                    ))
                    inserted_count += 1
                else:
                    # 更新现有产品
                    sql = """
                        UPDATE aigclink_products
                        SET product_name = %s, short_description = %s, summary = %s, 
                        url = %s, category = %s, tags = %s, industry = %s, 
                        job_assistance = %s, last_edited_time = %s
                        WHERE id = %s
                    """
                    cursor.execute(sql, (
                        item.get('product_name', ''),
                        item.get('short_description', ''),
                        item.get('summary', ''),
                        item.get('url', ''),
                        item.get('category', ''),
                        json_dumps_chinese(item.get('tags', [])),
                        item.get('industry', ''),
                        item.get('job_assistance', ''),
                        item.get('last_edited_time', 0),
                        item['id']
                    ))
                    updated_count += 1
        
        connection.commit()
        logger.info(f"数据保存成功: 新增 {inserted_count} 条, 更新 {updated_count} 条")
        return True
    except Exception as e:
        connection.rollback()
        logger.error(f"保存AIGCLINK数据错误: {e}")
        return False
    finally:
        connection.close()
        logger.info("数据库连接已关闭")

def save_aigclink_analysis(product_id, analysis_data):
    """保存AIGCLINK产品的AI分析结果到数据库"""
    if not SAVE_TO_DB:
        logger.info("未启用数据库存储，跳过AI分析保存")
        return False
    
    logger.info(f"开始保存产品 {product_id} 的AI分析结果到数据库")
    
    connection = get_connection()
    if not connection:
        logger.error("无法获取数据库连接，AI分析保存失败")
        return False
    
    try:
        with connection.cursor() as cursor:
            # 检查是否已存在分析结果
            cursor.execute("SELECT id FROM aigclink_analysis WHERE product_id = %s", (product_id,))
            existing_analysis = cursor.fetchone()
            
            if not existing_analysis:
                # 插入新分析
                sql = """
                    INSERT INTO aigclink_analysis 
                    (product_id, summary, key_features, innovation_points, patent_ideas, 
                    use_cases, tech_stack, market_potential, improvement_suggestions, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(sql, (
                    product_id,
                    analysis_data.get('summary', ''),
                    json_dumps_chinese(analysis_data.get('key_features', [])),
                    json_dumps_chinese(analysis_data.get('innovation_points', [])),
                    json_dumps_chinese(analysis_data.get('patent_ideas', [])),
                    json_dumps_chinese(analysis_data.get('use_cases', [])),
                    json_dumps_chinese(analysis_data.get('tech_stack', [])),
                    analysis_data.get('market_potential', ''),
                    json_dumps_chinese(analysis_data.get('improvement_suggestions', [])),
                    datetime.now()
                ))
                logger.info(f"产品 {product_id} 的AI分析已保存到数据库")
            else:
                # 更新现有分析
                sql = """
                    UPDATE aigclink_analysis
                    SET summary = %s, key_features = %s, innovation_points = %s, 
                    patent_ideas = %s, use_cases = %s, tech_stack = %s, 
                    market_potential = %s, improvement_suggestions = %s
                    WHERE product_id = %s
                """
                cursor.execute(sql, (
                    analysis_data.get('summary', ''),
                    json_dumps_chinese(analysis_data.get('key_features', [])),
                    json_dumps_chinese(analysis_data.get('innovation_points', [])),
                    json_dumps_chinese(analysis_data.get('patent_ideas', [])),
                    json_dumps_chinese(analysis_data.get('use_cases', [])),
                    json_dumps_chinese(analysis_data.get('tech_stack', [])),
                    analysis_data.get('market_potential', ''),
                    json_dumps_chinese(analysis_data.get('improvement_suggestions', [])),
                    product_id
                ))
                logger.info(f"产品 {product_id} 的AI分析已更新")
        
        connection.commit()
        return True
    except Exception as e:
        connection.rollback()
        logger.error(f"保存AI分析错误: {e}")
        return False
    finally:
        connection.close()
        logger.info("数据库连接已关闭")

if __name__ == "__main__":
    # 测试数据库连接
    logger.info("测试数据库连接...")
    if DB_USER and DB_PASSWORD and DB_HOST and DB_PORT and DB_NAME:
        conn = get_connection()
        if conn:
            logger.info("数据库连接测试成功")
            conn.close()
            
            # 初始化表
            if SAVE_TO_DB:
                init_aigclink_table()
        else:
            logger.error("数据库连接测试失败")
    else:
        logger.error("数据库配置不完整，请设置所有必要的环境变量") 