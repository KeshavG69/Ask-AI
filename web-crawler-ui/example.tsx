import React from 'react'
import { WebCrawlerChat } from './index'
import './styles/webCrawlerStyles.css'

// Example usage of the Web Crawler Streaming UI
const ExampleUsage: React.FC = () => {
  // Example message data that matches your backend format
  const exampleMessage = {
    role: 'agent' as const,
    content: `Based on the scraped content from the API documentation, here are the key points about rate limits:

## API Rate Limits

The API implements the following rate limiting policies:

### Free Tier
- **100 requests per hour** per API key
- **1,000 requests per day** maximum
- Rate limit resets at the top of each hour

### Premium Tier  
- **1,000 requests per hour** per API key
- **50,000 requests per day** maximum
- Burst capacity of up to 2,000 requests in a 5-minute window

### Rate Limit Headers
All API responses include these headers:
- \`X-RateLimit-Limit\`: Your rate limit ceiling for that request
- \`X-RateLimit-Remaining\`: Number of requests left for the time window
- \`X-RateLimit-Reset\`: UTC timestamp when the rate limit resets

### Best Practices
1. **Implement exponential backoff** when you receive 429 responses
2. **Cache responses** when possible to reduce API calls
3. **Use webhooks** instead of polling for real-time updates
4. **Batch requests** when the API supports it

If you exceed the rate limit, you'll receive a 429 status code with a retry-after header indicating when you can make your next request.`,
    created_at: Date.now(),
    tool_calls: [{
      tool_call_id: 'call_abc123',
      tool_name: 'crawl_selected_urls',
      tool_args: {
        urls: [
          'https://docs.api.com/rate-limits',
          'https://docs.api.com/authentication', 
          'https://docs.api.com/best-practices',
          'https://help.api.com/troubleshooting'
        ]
      },
      metrics: {
        time: 4.2
      },
      created_at: Date.now()
    }],
    extra_data: {
      reasoning_steps: [
        {
          title: 'Analyzing the user question',
          reasoning: 'The user is asking about API rate limits, which requires specific technical documentation',
          result: 'Identified need for rate limiting documentation',
          confidence: 0.95
        },
        {
          title: 'Selecting relevant documentation URLs',
          reasoning: 'Choosing pages that contain rate limiting policies, authentication details, and best practices',
          result: 'Selected 4 high-quality documentation sources',
          confidence: 0.89
        },
        {
          title: 'Crawling and extracting content',
          reasoning: 'Retrieving the most up-to-date information from official API documentation',
          result: 'Successfully crawled 4 pages in 4.2 seconds',
          confidence: 0.92
        },
        {
          title: 'Synthesizing comprehensive answer',
          reasoning: 'Combining information from multiple sources to provide complete rate limiting details',
          result: 'Created detailed response covering all rate limit aspects',
          confidence: 0.97
        }
      ]
    }
  }

  const userMessage = {
    role: 'user' as const,
    content: 'What are the API rate limits for your service?',
    created_at: Date.now() - 30000
  }

  return (
    <div style={{ 
      maxWidth: '800px', 
      margin: '0 auto', 
      padding: '20px',
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
    }}>
      <h1>Web Crawler Streaming UI Demo</h1>
      <p>This demo shows how the streaming UI components work with your web crawler backend.</p>
      
      <div style={{ 
        background: '#f8fafc', 
        border: '1px solid #e2e8f0', 
        borderRadius: '12px',
        padding: '20px',
        marginBottom: '20px'
      }}>
        <h2>Chat Conversation</h2>
        
        {/* User Message */}
        <WebCrawlerChat message={userMessage} />
        
        {/* Agent Response with Reasoning, Content, and Sources */}
        <WebCrawlerChat message={exampleMessage} />
      </div>

      <div style={{ 
        background: '#fff3cd', 
        border: '1px solid #ffeaa7',
        borderRadius: '8px',
        padding: '16px',
        marginTop: '20px'
      }}>
        <h3>🎯 What you're seeing:</h3>
        <ul>
          <li><strong>Reasoning Steps:</strong> Animated step-by-step AI thinking process</li>
          <li><strong>Main Content:</strong> Formatted response with markdown support</li>
          <li><strong>Sources:</strong> URLs that were crawled, extracted from tool calls</li>
          <li><strong>Responsive Design:</strong> Works on all screen sizes</li>
        </ul>
      </div>
    </div>
  )
}

export default ExampleUsage
