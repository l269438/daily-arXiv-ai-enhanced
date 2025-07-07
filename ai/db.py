import os
import json
import sys
import pymysql
from datetime import datetime

# 从环境变量获取数据库连接信息
DB_USER = os.environ.get("DB_USER", "")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
DB_HOST = os.environ.get("DB_HOST", "")
DB_PORT = int(os.environ.get("DB_PORT", ""))
DB_NAME = os.environ.get("DB_NAME", "")

def get_connection():
    """获取数据库连接"""
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
        print(f"数据库连接错误: {e}", file=sys.stderr)
        return None

def init_db():
    """初始化数据库和表"""
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
            print(f"数据库 '{DB_NAME}' 已创建或已存在")
            
            # 切换到新创建的数据库
            cursor.execute(f"USE `{DB_NAME}`")
            
            # 创建papers表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS `papers` (
                  `id` varchar(50) COLLATE utf8mb4_general_ci NOT NULL,
                  `title` varchar(500) COLLATE utf8mb4_general_ci NOT NULL,
                  `authors` text COLLATE utf8mb4_general_ci NOT NULL,
                  `summary` text COLLATE utf8mb4_general_ci NOT NULL,
                  `abs` varchar(255) COLLATE utf8mb4_general_ci NOT NULL,
                  `pdf` varchar(255) COLLATE utf8mb4_general_ci DEFAULT NULL,
                  `categories` text COLLATE utf8mb4_general_ci NOT NULL,
                  `comment` text COLLATE utf8mb4_general_ci,
                  `crawl_date` datetime NOT NULL,
                  PRIMARY KEY (`id`)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
            """)
            print("papers表已创建或已存在")
            
            # 创建ai_analysis表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS `ai_analysis` (
                  `id` int NOT NULL AUTO_INCREMENT,
                  `paper_id` varchar(50) COLLATE utf8mb4_general_ci NOT NULL,
                  `tldr` text COLLATE utf8mb4_general_ci NOT NULL,
                  `motivation` text COLLATE utf8mb4_general_ci NOT NULL,
                  `method` text COLLATE utf8mb4_general_ci NOT NULL,
                  `result` text COLLATE utf8mb4_general_ci NOT NULL,
                  `conclusion` text COLLATE utf8mb4_general_ci NOT NULL,
                  `idea_en` text COLLATE utf8mb4_general_ci NOT NULL,
                  `idea_ch` text COLLATE utf8mb4_general_ci NOT NULL,
                  `language` varchar(50) COLLATE utf8mb4_general_ci NOT NULL,
                  `created_at` datetime NOT NULL,
                  PRIMARY KEY (`id`),
                  KEY `paper_id` (`paper_id`),
                  CONSTRAINT `ai_analysis_ibfk_1` FOREIGN KEY (`paper_id`) REFERENCES `papers` (`id`)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
            """)
            print("ai_analysis表已创建或已存在")
        
        connection.close()
        return True
    except Exception as e:
        print(f"初始化数据库错误: {e}", file=sys.stderr)
        return False

def save_paper(paper_data):
    """保存论文数据到数据库"""
    connection = get_connection()
    if not connection:
        return False
    
    try:
        with connection.cursor() as cursor:
            # 检查论文是否已存在
            cursor.execute("SELECT id FROM papers WHERE id = %s", (paper_data['id'],))
            existing_paper = cursor.fetchone()
            
            if not existing_paper:
                # 插入新论文
                sql = """
                    INSERT INTO papers (id, title, authors, summary, abs, pdf, categories, comment, crawl_date)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(sql, (
                    paper_data['id'],
                    paper_data['title'],
                    json.dumps(paper_data['authors']),
                    paper_data['summary'],
                    paper_data['abs'],
                    paper_data.get('pdf', None),
                    json.dumps(paper_data['categories']),
                    paper_data.get('comment', None),
                    datetime.now()
                ))
                print(f"论文 {paper_data['id']} 已保存到数据库")
        
        connection.commit()
        return True
    except Exception as e:
        connection.rollback()
        print(f"保存论文错误: {e}", file=sys.stderr)
        return False
    finally:
        connection.close()

def save_ai_analysis(paper_id, ai_data, language):
    """保存AI分析数据到数据库"""
    connection = get_connection()
    if not connection:
        return False
    
    try:
        with connection.cursor() as cursor:
            # 检查是否已存在AI分析
            cursor.execute("SELECT id FROM ai_analysis WHERE paper_id = %s", (paper_id,))
            existing_analysis = cursor.fetchone()
            
            if not existing_analysis:
                # 插入新分析
                sql = """
                    INSERT INTO ai_analysis (paper_id, tldr, motivation, method, result, conclusion, idea_en, idea_ch, language, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(sql, (
                    paper_id,
                    ai_data['tldr'],
                    ai_data['motivation'],
                    ai_data['method'],
                    ai_data['result'],
                    ai_data['conclusion'],
                    json.dumps(ai_data['idea_en']),
                    json.dumps(ai_data['idea_ch']),
                    language,
                    datetime.now()
                ))
                print(f"论文 {paper_id} 的AI分析已保存到数据库")
            else:
                # 更新现有分析
                sql = """
                    UPDATE ai_analysis
                    SET tldr = %s, motivation = %s, method = %s, result = %s, conclusion = %s, idea_en = %s, idea_ch = %s, language = %s
                    WHERE paper_id = %s
                """
                cursor.execute(sql, (
                    ai_data['tldr'],
                    ai_data['motivation'],
                    ai_data['method'],
                    ai_data['result'],
                    ai_data['conclusion'],
                    json.dumps(ai_data['idea_en']),
                    json.dumps(ai_data['idea_ch']),
                    language,
                    paper_id
                ))
                print(f"论文 {paper_id} 的AI分析已更新")
        
        connection.commit()
        return True
    except Exception as e:
        connection.rollback()
        print(f"保存AI分析错误: {e}", file=sys.stderr)
        return False
    finally:
        connection.close()

def save_paper_with_analysis(paper_data):
    """保存论文和AI分析数据到数据库"""
    # 先保存论文数据
    if save_paper(paper_data):
        # 如果有AI分析数据，再保存分析
        if 'AI' in paper_data:
            language = os.environ.get("LANGUAGE", "Chinese")
            return save_ai_analysis(paper_data['id'], paper_data['AI'], language)
        return True
    return False 