#!/usr/bin/env python3
"""
Test script for WebCrawlerTool - Tests the tool directly without agent
"""

from web_crawler_tool import WebCrawlerTool
import time

test=WebCrawlerTool().discover_site_structure(urls=['https://docs.agno.com/introduction'])
print(test)