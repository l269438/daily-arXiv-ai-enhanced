#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
AIGCLINK爬虫模块的命令行入口点
支持两种爬虫方法：
1. API方法 - 直接调用Notion API获取数据（默认，推荐）
2. Selenium方法 - 使用浏览器爬取网页内容
"""

import sys
import argparse

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='AIGCLINK爬虫 - 从AIGCLINK网站获取AI产品/工具数据')
    parser.add_argument('--method', type=str, choices=['api', 'selenium'], default='api',
                        help='爬取方法: api（直接调用API，默认）或 selenium（使用浏览器）')
    parser.add_argument('--url', type=str, 
                        help='AIGCLINK网址，默认为首页')
    parser.add_argument('--output', type=str, 
                        help='输出文件路径')
    parser.add_argument('--chinese-keys', action='store_true', 
                        help='使用中文键名（默认使用英文键名）')
    parser.add_argument('--compact', action='store_true', 
                        help='输出紧凑的JSON格式（无缩进）')
    parser.add_argument('--verbose', action='store_true', 
                        help='显示详细日志')
    parser.add_argument('--save-to-db', action='store_true', 
                        help='将数据保存到数据库')
    
    args = parser.parse_args()
    
    if args.method == 'api':
        # 使用API方法
        from .api_scraper import scrape_aigclink
        success = scrape_aigclink(args.url, args.output, not args.chinese_keys, args.save_to_db)
    else:
        # 使用Selenium方法
        from .scraper import setup_selenium, scrape_aigclink_notion, save_results
        
        # 设置Selenium
        selenium_tools = setup_selenium()
        if not selenium_tools:
            print("Selenium设置失败，退出")
            return 1
        
        try:
            # 爬取内容
            url = args.url or "https://d.aigclink.ai/?v=8f252a54730e49f4b8caf897b7ae49f6"
            print(f"开始爬取 {url}")
            results = scrape_aigclink_notion(selenium_tools, url)
            
            if not results:
                print("爬取失败，未返回结果")
                return 1
            
            # 保存结果
            success = save_results(results, args.output)
        finally:
            # 确保关闭WebDriver
            try:
                selenium_tools["driver"].quit()
                print("WebDriver已关闭")
            except:
                pass
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 