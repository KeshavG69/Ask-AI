# Web Support Bot

An intelligent web crawling agent built with the Agno framework that can answer questions about websites by crawling and analyzing their content.

## Features

- **Scraped Data Only**: **CRITICALLY IMPORTANT** - ALL answers are based EXCLUSIVELY on scraped website content, never external knowledge
- **Intelligent Web Crawling**: Uses crawl4ai to extract clean content from multiple URLs simultaneously
- **Smart Decision Making**: Agent decides when to explore more pages vs when it has enough information to answer
- **Domain Filtering**: Stays within specified allowed domains for security
- **Link Discovery**: Automatically discovers and can explore related pages
- **Source Attribution**: Always cites specific URLs where information was found with direct quotes
- **Data Integrity**: Never supplements with external knowledge, training data, or assumptions
- **Relevance Filtering**: Refuses to answer questions unrelated to the crawled website content
- **Conversation Memory**: Remembers previous interactions and crawled content

## Architecture

The system consists of two main components:

### 1. WebCrawlerTool (`web_crawler_tool.py`)
- **Purpose**: Pure crawling functionality - takes URLs, returns content and links
- **Key Features**:
  - Async crawling of multiple URLs simultaneously
  - Clean content extraction using crawl4ai
  - Link discovery and domain filtering
  - Error handling for failed crawls
  - Formatted output for easy agent parsing

### 2. Web Support Agent (`main.py`)
- **Purpose**: Intelligence layer that makes decisions about what to crawl and how to answer
- **Key Features**:
  - Uses GPT-4 for reasoning and decision making
  - Analyzes crawled content to determine sufficiency
  - Selects relevant links for further exploration
  - Generates comprehensive answers with sources
  - Refuses irrelevant questions

## How It Works

```
1. User asks question → 2. Agent crawls starting URLs → 3. Agent analyzes content
                                    ↓
6. Agent provides answer ← 5. Enough info? → 4. Agent selects & crawls more URLs
   with sources                YES      NO           (back to step 3)
```

## Installation

1. Make sure you have the required dependencies:
```bash
pip install agno crawl4ai playwright
```

2. Install Playwright browsers (required for crawl4ai):
```bash
playwright install
```

3. Set up your OpenAI API key in `.env`:
```
OPENAI_API_KEY=your_api_key_here
```

## Usage

### Basic Usage

```python
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from web_crawler_tool import WebCrawlerTool

# Create the tool with domain restrictions
crawler_tool = WebCrawlerTool(allowed_domains=["example.com"])

# Create agent
agent = Agent(
    model=OpenAIChat(id="gpt-4o"),
    tools=[crawler_tool],
    instructions=[
        "Crawl the starting URLs to gather information",
        "Only answer questions related to the website content",
        "Always cite your sources"
    ]
)

# Ask questions
agent.print_response("What services do you offer?")
```

### Running the Demo

```bash
python main.py
```

Choose between:
1. **Demo mode**: Uses example.com for testing
2. **Interactive mode**: Specify your own URLs and domains

### Example Conversation

```
User: "What is your return policy?"

Agent: I'll help you find information about the return policy. Let me start by 
       crawling the main website pages.
       
[Agent calls crawl_websites tool with starting URLs]

Agent: I found a dedicated returns page. Let me get the specific policy details.

[Agent calls crawl_websites tool with the returns page URL]

Agent: Based on the return policy page at https://store.com/returns, here's what I found:
       
       **Return Policy Summary:**
       - 30-day return window from purchase date
       - Items must be in original condition
       - Free return shipping for defective items
       
       Source: https://store.com/returns
```

## Configuration Options

### WebCrawlerTool Parameters

- `allowed_domains`: List of domains the crawler can access (e.g., `["example.com", "help.example.com"]`)
- `max_links_per_page`: Maximum number of links to extract from each page (default: 50)

### Agent Instructions

You can customize the agent's behavior by modifying the instructions:

```python
agent = Agent(
    model=OpenAIChat(id="gpt-4o"),
    tools=[crawler_tool],
    instructions=[
        "CRITICAL: ALWAYS base answers EXCLUSIVELY on scraped website data",
        "NEVER use external knowledge or general information",
        "Focus on finding official policies and procedures",
        "Prioritize FAQ and help pages", 
        "If information is incomplete, explore related links",
        "Always provide direct quotes from scraped content as evidence",
        "If no relevant data found in scraped content, explicitly state this"
    ]
)
```

## Error Handling

The system gracefully handles:
- Failed webpage crawls
- Domain restriction violations
- Network timeouts
- Invalid URLs
- Questions unrelated to website content

## Limitations

- Requires OpenAI API key (uses GPT-4)
- Limited to publicly accessible web pages
- Respects robots.txt and rate limiting
- Cannot crawl JavaScript-heavy SPAs effectively
- Performance depends on website response times

## Examples

### E-commerce Support Bot
```python
starting_urls = ["https://shop.com", "https://shop.com/help", "https://shop.com/faq"]
allowed_domains = ["shop.com"]
# Agent can answer questions about products, policies, shipping, etc.
```

### Documentation Bot
```python
starting_urls = ["https://docs.example.com"]
allowed_domains = ["docs.example.com", "api.example.com"]  
# Agent can answer technical questions from documentation
```

### Company Information Bot
```python
starting_urls = ["https://company.com/about", "https://company.com/contact"]
allowed_domains = ["company.com"]
# Agent can answer questions about company info, contact details, etc.
```

## Contributing

This implementation follows the design principles of keeping tools simple (just crawl and return data) while putting all intelligence in the agent (decision making, relevance filtering, answer generation).

The architecture makes it easy to:
- Extend the crawler with new features
- Modify agent instructions for different use cases  
- Add new tools for different data sources
- Scale to handle multiple domains or languages
