#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
初始化数据库脚本
用于创建数据库和表结构
"""

import os
import sys
import argparse
from db import init_db

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="初始化数据库和表结构")
    parser.add_argument("--user", help="数据库用户名", default=os.environ.get("DB_USER"))
    parser.add_argument("--password", help="数据库密码", default=os.environ.get("DB_PASSWORD"))
    parser.add_argument("--host", help="数据库主机地址", default=os.environ.get("DB_HOST", "localhost"))
    parser.add_argument("--port", help="数据库端口", default=os.environ.get("DB_PORT", "3306"))
    parser.add_argument("--name", help="数据库名称", default=os.environ.get("DB_NAME", "daily_arxiv"))
    return parser.parse_args()

def main():
    """主函数"""
    print("开始初始化数据库...")
    
    # 解析命令行参数
    args = parse_args()
    
    # 设置环境变量
    if args.user:
        os.environ["DB_USER"] = args.user
    if args.password:
        os.environ["DB_PASSWORD"] = args.password
    if args.host:
        os.environ["DB_HOST"] = args.host
    if args.port:
        os.environ["DB_PORT"] = args.port
    if args.name:
        os.environ["DB_NAME"] = args.name
    
    # 检查环境变量
    required_vars = ["DB_USER", "DB_PASSWORD", "DB_HOST"]
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    
    if missing_vars:
        print(f"错误: 缺少必要的环境变量或参数: {', '.join(missing_vars)}", file=sys.stderr)
        print("请设置以下环境变量或提供命令行参数:")
        print("  DB_USER/--user - 数据库用户名")
        print("  DB_PASSWORD/--password - 数据库密码")
        print("  DB_HOST/--host - 数据库主机地址")
        print("可选环境变量或参数:")
        print("  DB_PORT/--port - 数据库端口 (默认: 3306)")
        print("  DB_NAME/--name - 数据库名称 (默认: daily_arxiv)")
        print("\n示例:")
        print("  python init_database.py --user root --password yourpassword --host localhost")
        return 1
    
    # 初始化数据库
    if init_db():
        print("数据库初始化成功!")
        return 0
    else:
        print("数据库初始化失败!", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main()) 