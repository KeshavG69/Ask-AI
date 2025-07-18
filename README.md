# Ask-AI

An intelligent web crawling AI agent built with the Agno framework that answers questions based exclusively on scraped website content. Ask-AI combines advanced web crawling capabilities with GPT-powered reasoning to provide accurate, source-based answers.

## 🎯 Key Features

- **Source-Only Answers**: ALL responses are based EXCLUSIVELY on scraped website content—never external knowledge or training data
- **Intelligent Web Crawling**: Uses crawl4ai and Playwright to extract clean content from multiple URLs simultaneously
- **Smart Reasoning**: Integrates reasoning tools to analyze questions and plan crawling strategies
- **Auto Domain Detection**: Automatically extracts and restricts crawling to relevant domains for security
- **Link Discovery**: Discovers and explores related pages intelligently based on question relevance
- **Anti-Hallucination**: Strict rules prevent invention or assumption of information not found in scraped content
- **Interactive & Demo Modes**: Choose between guided demo or specify your own URLs and domains
- **Comprehensive Error Handling**: Gracefully handles failed crawls, timeouts, and invalid URLs

## 🏗️ Architecture

### Core Components

1. **Main Agent** (`main.py`)
   - Orchestrates the entire question-answering process
   - Uses GPT-4 for intelligent decision making and reasoning
   - Manages crawling strategy and response generation
   - Enforces strict source-only information rules

2. **Web Crawler Tool** (`web_crawler_tool.py`)
   - Handles async crawling of multiple URLs
   - Extracts clean, readable content using crawl4ai
   - Discovers and filters relevant links
   - Manages domain restrictions and security

3. **Test Suite**
   - `test_tool.py`: Basic tool functionality tests
   - `test_enhanced_crawler.py`: Advanced crawling scenario tests

### Workflow

```
User Question → Agent Reasoning → URL Selection → Content Crawling → Analysis → Source-Based Answer
     ↑                                                                           ↓
     └─────────────── Additional Crawling (if needed) ←─── Completeness Check ←─┘
```

## 🚀 Installation

### Prerequisites
- Python 3.13+ (specified in pyproject.toml)
- OpenAI API key

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/KeshavG69/Ask-AI.git
   cd Ask-AI
   ```

2. **Install dependencies using UV (recommended)**
   ```bash
   # Install UV if you haven't already
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # Install project dependencies
   uv sync
   ```

   **Or using pip**
   ```bash
   pip install agno>=1.7.4 crawl4ai>=0.7.1 playwright>=1.53.0 python-dotenv
   ```

3. **Install Playwright browsers** (required for crawl4ai)
   ```bash
   playwright install
   ```

4. **Set up environment variables**
   ```bash
   # Create .env file
   echo "OPENAI_API_KEY=your_api_key_here" > .env
   ```

## 💻 Usage

### Quick Start

```bash
python main.py
```

Choose between:
1. **Demo Mode**: Uses cricbuzz.com for testing cricket-related queries
2. **Interactive Mode**: Specify your own URLs and ask custom questions

### Demo Mode Example

```
❓ Question: Tell me about the India vs England 2nd test match

🤖 Agent Response:
Based on the latest information from Cricbuzz:

**Match Status**: India vs England, 2nd Test
**Venue**: Lord's Cricket Ground, London
**Current Status**: England 218/4 (Day 2, 2nd Session)
...

*All information sourced directly from cricbuzz.com*
```

### Interactive Mode Example

```python
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from web_crawler_tool import WebCrawlerTool
import os

# Create crawler for your specific domain
starting_urls = ["https://docs.yourcompany.com"]
agent = create_web_support_agent(starting_urls)

# Ask questions
agent.print_response("What are your API rate limits?")
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your_openai_api_key_here
```

### Agent Instructions

The agent follows strict guidelines to ensure accuracy:

- **Source Exclusivity**: Only information from scraped content is used
- **Anti-Hallucination**: No invention, assumption, or gap-filling with external knowledge
- **Reasoning Integration**: Uses reasoning tools to plan and verify responses
- **URL Selection**: Intelligently matches URLs to question topics

### Customization

You can customize the agent for specific use cases:

```python
# E-commerce support
starting_urls = ["https://shop.com", "https://shop.com/help"]

# Documentation bot  
starting_urls = ["https://docs.api.com", "https://docs.api.com/reference"]

# Company information
starting_urls = ["https://company.com/about", "https://company.com/contact"]
```

## 🧪 Testing

Run the test suite to verify functionality:

```bash
# Basic tool tests
python test_tool.py

# Enhanced crawler tests
python test_enhanced_crawler.py
```

## 🔧 Technical Details

### Dependencies

- **agno**: AI agent framework for orchestration
- **crawl4ai**: Advanced web crawling and content extraction
- **playwright**: Browser automation for JavaScript-heavy sites
- **openai**: GPT-4 integration for reasoning and responses

### Security Features

- **Domain Restriction**: Automatically limits crawling to specified domains
- **Rate Limiting**: Respects robots.txt and implements crawling delays
- **Content Filtering**: Only processes publicly accessible content
- **Error Isolation**: Failed crawls don't compromise other operations

### Performance Considerations

- **Async Crawling**: Multiple URLs processed simultaneously
- **Intelligent Caching**: Avoids redundant crawls of same content
- **Selective Crawling**: Only crawls URLs relevant to the question
- **Content Optimization**: Extracts clean, readable text from HTML

## 🛠️ Development

### Project Structure

```
Ask-AI/
├── main.py                    # Main application entry point
├── web_crawler_tool.py        # Core crawling functionality
├── test_tool.py              # Basic functionality tests
├── test_enhanced_crawler.py   # Advanced crawling tests
├── pyproject.toml            # Project configuration
├── .env                      # Environment variables (create this)
├── .gitignore               # Git ignore rules
└── README.md                # This file
```

### Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## 🚫 Limitations

- **Content Scope**: Limited to publicly accessible web pages
- **JavaScript**: May have issues with heavily JavaScript-dependent SPAs
- **API Dependency**: Requires OpenAI API access (GPT-4)
- **Rate Limits**: Subject to website rate limiting and robots.txt
- **Real-time Data**: Information is only as current as the last crawl

## 📝 Use Cases

### Customer Support Bot
```python
starting_urls = ["https://support.company.com", "https://help.company.com/faq"]
# Answers customer questions based on official support documentation
```

### Technical Documentation Assistant
```python
starting_urls = ["https://docs.api.com", "https://api.reference.com"]
# Helps developers with API questions using official documentation
```

### Product Information Agent
```python
starting_urls = ["https://products.company.com", "https://specs.company.com"]
# Provides product details based on official specifications
```

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Support

- **Issues**: Report bugs via GitHub Issues
- **Documentation**: Check this README and inline code comments
- **API Keys**: Ensure your OpenAI API key has sufficient credits

## 🔗 Related Projects

- [Agno Framework](https://github.com/agno-ai/agno) - AI agent orchestration
- [Crawl4AI](https://github.com/unclecode/crawl4ai) - Advanced web crawling
- [Playwright](https://playwright.dev/) - Browser automation

---

**Ask-AI**: Bringing accuracy and transparency to AI-powered question answering through source-based responses.
