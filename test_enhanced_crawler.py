#!/usr/bin/env python3
"""
Quick test for the enhanced web crawler
"""

import asyncio
from web_crawler_tool import WebCrawlerTool


async def test_enhanced_crawler():
    """Test the enhanced crawler with a simple site first."""
    print("🧪 Testing Enhanced Web Crawler")
    print("=" * 50)
    
    # Test with a simple site first
    starting_urls = ["https://httpbin.org/html"]
    tool = WebCrawlerTool(starting_urls=starting_urls)
    
    print("📝 Testing with httpbin.org/html (simple test)...")
    result = tool.crawl_websites("https://httpbin.org/html")
    print("\n🔍 Result:")
    print("=" * 50)
    print(result)
    print("=" * 50)
    
    # Test content length
    if "Content Length:" in result:
        print("✅ Enhanced content extraction working!")
    else:
        print("❌ Enhanced content extraction may have issues")


if __name__ == "__main__":
    asyncio.run(test_enhanced_crawler())
