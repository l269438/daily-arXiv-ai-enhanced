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

def get_connection():
    """获取数据库连接"""
    if not HAS_PYMYSQL:
        logger.error("未安装pymysql，无法连接数据库")
        return None
    
    try:
        connection = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT,
            database=DB_NAME,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        return connection
    except Exception as e:
        logger.error(f"数据库连接错误: {e}")
        return None

def init_aigclink_table():
    """初始化AIGCLINK数据表"""
    if not SAVE_TO_DB:
        logger.info("未启用数据库存储，跳过表初始化")
        return False
    
    connection = get_connection()
    if not connection:
        return False
    
    try:
        with connection.cursor() as cursor:
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
        
        connection.commit()
        return True
    except Exception as e:
        connection.rollback()
        logger.error(f"初始化AIGCLINK表错误: {e}")
        return False
    finally:
        connection.close()

def save_aigclink_data(items):
    """保存AIGCLINK数据到数据库"""
    if not SAVE_TO_DB:
        logger.info("未启用数据库存储，跳过数据保存")
        return False
    
    connection = get_connection()
    if not connection:
        return False
    
    try:
        with connection.cursor() as cursor:
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
                        item.get('tags', ''),
                        item.get('industry', ''),
                        item.get('job_assistance', ''),
                        item.get('created_time', 0),
                        item.get('last_edited_time', 0),
                        datetime.now()
                    ))
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
                        item.get('tags', ''),
                        item.get('industry', ''),
                        item.get('job_assistance', ''),
                        item.get('last_edited_time', 0),
                        item['id']
                    ))
        
        connection.commit()
        logger.info(f"成功保存 {len(items)} 条AIGCLINK数据到数据库")
        return True
    except Exception as e:
        connection.rollback()
        logger.error(f"保存AIGCLINK数据错误: {e}")
        return False
    finally:
        connection.close() 