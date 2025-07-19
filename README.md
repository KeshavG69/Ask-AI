# Ask-AI

A streaming AI Chat Widget API that answers questions based exclusively on content crawled from specified websites. Built with FastAPI and powered by GPT-4, Ask-AI provides real-time streaming responses with intelligent web crawling capabilities.

## 🎯 Key Features

- **Streaming API**: Real-time Server-Sent Events (SSE) streaming for immediate response delivery
- **Source-Only Answers**: ALL responses based EXCLUSIVELY on crawled website content—never external knowledge
- **Smart Web Crawling**: Uses crawl4ai and Playwright for JavaScript-heavy sites and dynamic content
- **llms.txt Discovery**: Automatically discovers AI-optimized content from llms.txt files
- **Multi-URL Support**: Crawl and analyze content from multiple websites simultaneously
- **Domain Security**: Automatic domain restriction for secure crawling
- **Widget-Ready**: CORS-enabled API perfect for website integration
- **Anti-Hallucination**: Strict rules prevent invention of information not found in crawled content
- **Real-time Processing**: Stream reasoning steps, crawling progress, and final responses

## 🏗️ Architecture

### Core Components

1. **FastAPI Server** (`server.py`)
   - Main web server with CORS middleware for widget embedding
   - Health endpoints and API documentation

2. **Chat API** (`app.py`)
   - Streaming chat endpoint (`/chat`) with Server-Sent Events
   - Request validation and session management
   - Real-time response processing

3. **AI Agent** (`agent.py`)
   - Creates web support agents using OpenAI GPT-4
   - Integrates reasoning tools for intelligent decision making
   - Enforces strict source-only information rules

4. **Web Crawler Tool** (`tool.py`)
   - Sophisticated web crawling with crawl4ai and Playwright
   - Automatic llms.txt discovery for AI-optimized content
   - Domain-restricted crawling for security
   - Link discovery and intelligent URL selection

5. **Stream Processor** (`simple_processor.py`)
   - Processes agent responses into clean streaming chunks
   - Extracts reasoning steps, crawling progress, and content
   - Prevents duplicate content in streams

6. **Chat Widget** (`chat-widget.js`, `chat-widget.html`)
   - Frontend components for easy website integration
   - Real-time streaming interface

### API Workflow

```
POST /chat → Agent Creation → Site Discovery → URL Selection → Content Crawling → AI Analysis → Streaming Response
     ↑                                                                                    ↓
     └─── Session Management ←──── Real-time Updates ←──── Stream Processing ←────┘
```

## 🚀 Installation

### Prerequisites
- Python 3.13+
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
   pip install agno>=1.7.5 crawl4ai>=0.7.1 fastapi>=0.116.1 playwright>=1.53.0 uvicorn>=0.32.1
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

### Start the Server

```bash
python server.py
```

The API will be available at `http://localhost:8000`

- **API Documentation**: `http://localhost:8000/docs`
- **Health Check**: `http://localhost:8000/health`

### API Endpoints

#### POST /chat - Streaming Chat

Send questions about website content and receive streaming responses.

**Request Body:**
```json
{
  "urls": ["https://docs.example.com", "https://help.example.com"],
  "query": "What are your API rate limits?",
  "session_id": "unique-session-id",
  "company_name": "YourCompany"
}
```

**Response:** Server-Sent Events stream with:
- **Reasoning steps**: AI decision-making process
- **Crawling progress**: Real-time crawling updates
- **Content chunks**: Streaming response content
- **Completion**: Final response with sources

#### GET /health - Health Check

```json
{
  "status": "healthy",
  "service": "AI Chat Widget API"
}
```

### Chat Widget Integration

Include the chat widget in your website:

```html
<!DOCTYPE html>
<html>
<head>
    <title>AI Chat Widget Demo</title>
</head>
<body>
    <!-- Your website content -->
    
    <!-- Include the chat widget -->
    <script src="chat-widget.js"></script>
    <link rel="stylesheet" href="chat-widget.html">
</body>
</html>
```

### API Usage Examples

#### Python Example

```python
import requests
import json

# Streaming chat request
def stream_chat(urls, query, session_id, company_name):
    response = requests.post(
        "http://localhost:8000/chat",
        json={
            "urls": urls,
            "query": query,
            "session_id": session_id,
            "company_name": company_name
        },
        stream=True,
        headers={'Accept': 'text/event-stream'}
    )
    
    for line in response.iter_lines():
        if line:
            if line.startswith(b'data: '):
                try:
                    data = json.loads(line[6:])
                    print(f"Type: {data['type']}")
                    if data['type'] == 'content':
                        print(f"Content: {data['text']}")
                except json.JSONDecodeError:
                    pass

# Example usage
stream_chat(
    urls=["https://docs.company.com", "https://help.company.com"],
    query="What are your pricing plans?",
    session_id="user-123",
    company_name="CompanyBot"
)
```

#### JavaScript Example

```javascript
const eventSource = new EventSource('/chat', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({
        urls: ['https://docs.example.com'],
        query: 'How do I get started?',
        session_id: 'session-456',
        company_name: 'ExampleBot'
    })
});

eventSource.onmessage = function(event) {
    const data = JSON.parse(event.data);
    
    switch(data.type) {
        case 'reasoning':
            console.log('AI Reasoning:', data.step.title);
            break;
        case 'crawling':
            console.log('Crawling:', data.urls);
            break;
        case 'content':
            console.log('Response:', data.text);
            break;
        case 'completion':
            console.log('Final Answer:', data.final_content);
            console.log('Sources:', data.sources);
            break;
    }
};
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your_openai_api_key_here
```

### Agent Customization

The AI agent follows strict guidelines for accuracy:

- **Source Exclusivity**: Only uses information from crawled content
- **Anti-Hallucination**: No invention or assumption of information
- **Reasoning Integration**: Uses reasoning tools to plan and verify responses
- **Markdown Formatting**: Structured, readable responses
- **Recency Priority**: Prioritizes most recent information

### Server Configuration

Modify `server.py` for custom configuration:

```python
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "server:app", 
        host="0.0.0.0",      # Change host
        port=8080,           # Change port
        reload=True,
        log_level="info"
    )
```

## 🧪 Testing

### Manual Testing

1. **Start the server**:
   ```bash
   python server.py
   ```

2. **Test with curl**:
   ```bash
   curl -X POST "http://localhost:8000/chat" \
        -H "Content-Type: application/json" \
        -d '{
          "urls": ["https://docs.python.org"],
          "query": "How do I install Python packages?",
          "session_id": "test-session",
          "company_name": "TestBot"
        }'
   ```

3. **Visit API docs**: `http://localhost:8000/docs`

### Load Testing

For production deployment, test with multiple concurrent requests:

```bash
# Install wrk for load testing
brew install wrk  # macOS
# or apt-get install wrk  # Linux

# Run load test
wrk -t12 -c400 -d30s -s post.lua http://localhost:8000/chat
```

## 🔧 Technical Details

### Dependencies

- **agno**: AI agent framework for orchestration and reasoning
- **crawl4ai**: Advanced web crawling with JavaScript support
- **playwright**: Browser automation for dynamic content
- **fastapi**: Modern async Python web framework
- **uvicorn**: ASGI server for FastAPI

### Smart Crawling Features

- **llms.txt Discovery**: Automatically finds AI-optimized content files
- **Domain Restriction**: Security through allowed domain filtering
- **Async Crawling**: Multiple URLs processed simultaneously
- **Content Optimization**: Extracts clean, readable text from HTML
- **Link Discovery**: Intelligent exploration of related pages

### Performance Considerations

- **Streaming Responses**: Immediate user feedback with Server-Sent Events
- **Async Processing**: Non-blocking request handling
- **Content Caching**: Avoids redundant crawling operations
- **Selective Crawling**: Only processes URLs relevant to the question
- **Error Isolation**: Failed crawls don't compromise other operations

## 🛠️ Development

### Project Structure

```
Ask-AI/
├── server.py                 # FastAPI server entry point
├── app.py                    # Chat API endpoints and streaming
├── agent.py                  # AI agent creation and configuration
├── tool.py                   # Web crawler tool implementation
├── simple_processor.py       # Stream processing logic
├── chat-widget.js           # Frontend chat widget JavaScript
├── chat-widget.html         # Frontend chat widget HTML/CSS
├── test.html                # Test page for widget integration
├── pyproject.toml           # Project dependencies and configuration
├── .env                     # Environment variables (create this)
├── .gitignore              # Git ignore rules
└── README.md               # This file
```

### Adding New Features

1. **New Tools**: Add to `agent.py` tools list
2. **API Endpoints**: Extend `app.py` router
3. **Stream Processing**: Modify `simple_processor.py`
4. **Frontend**: Update `chat-widget.js`

### Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Test with the API
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## 🚫 Limitations

- **Content Scope**: Limited to publicly accessible web pages
- **JavaScript Dependency**: Requires Playwright for dynamic content
- **API Dependency**: Requires OpenAI API access (GPT-4)
- **Rate Limits**: Subject to website rate limiting and robots.txt
- **Real-time Data**: Information is only as current as the last crawl
- **CORS**: Currently allows all origins (configure for production)

## 📝 Use Cases

### Customer Support Chatbot
```json
{
  "urls": ["https://support.company.com", "https://help.company.com/faq"],
  "query": "How do I reset my password?",
  "session_id": "support-session",
  "company_name": "SupportBot"
}
```

### Documentation Assistant
```json
{
  "urls": ["https://docs.api.com", "https://api.reference.com"],
  "query": "What are the authentication requirements?",
  "session_id": "dev-session",
  "company_name": "DocsBot"
}
```

### Product Information Agent
```json
{
  "urls": ["https://products.company.com", "https://specs.company.com"],
  "query": "What are the technical specifications?",
  "session_id": "product-session",
  "company_name": "ProductBot"
}
```

## 🚀 Deployment

### Docker Deployment

```dockerfile
FROM python:3.13-slim

WORKDIR /app
COPY . .

RUN pip install -r requirements.txt
RUN playwright install

EXPOSE 8000
CMD ["python", "server.py"]
```

### Production Considerations

- Configure CORS origins for your domain
- Use environment variables for API keys
- Set up proper logging and monitoring
- Consider rate limiting for API endpoints
- Use HTTPS in production

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Support

- **Issues**: Report bugs via GitHub Issues
- **API Documentation**: Available at `/docs` when server is running
- **Examples**: Check `test.html` for widget integration examples

## 🔗 Related Projects

- [Agno Framework](https://github.com/agno-ai/agno) - AI agent orchestration
- [Crawl4AI](https://github.com/unclecode/crawl4ai) - Advanced web crawling
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [Playwright](https://playwright.dev/) - Browser automation

---

**Ask-AI**: Real-time streaming AI chat widget powered by intelligent web crawling and source-based responses.
