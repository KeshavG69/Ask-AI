# Web Crawler Streaming UI Components

A complete React component library for displaying streaming AI web crawler responses with animated reasoning steps, content streaming, and source attribution.

## Features

- 🧠 **Animated Reasoning Steps** - Shows AI thinking process step-by-step
- 💬 **Word-by-word Content Streaming** - Real-time response display
- 📚 **Source Attribution** - Clear display of crawled URLs
- 🎨 **Beautiful Animations** - Smooth transitions and loading states
- 📱 **Responsive Design** - Works on all screen sizes
- 🎯 **TypeScript Support** - Full type safety

## Quick Start

### 1. Import Components and Styles

```jsx
import WebCrawlerChat from './web-crawler-ui/components/WebCrawlerChat'
import './web-crawler-ui/styles/webCrawlerStyles.css'
```

### 2. Basic Usage

```jsx
import React from 'react'
import WebCrawlerChat from './web-crawler-ui/components/WebCrawlerChat'

const App = () => {
  const message = {
    role: 'agent',
    content: 'Based on the crawled documentation, here is the information...',
    created_at: Date.now(),
    tool_calls: [{
      tool_call_id: 'call_123',
      tool_name: 'crawl_selected_urls',
      tool_args: {
        urls: [
          'https://docs.example.com/api',
          'https://docs.example.com/guide'
        ]
      },
      created_at: Date.now()
    }],
    extra_data: {
      reasoning_steps: [
        {
          title: 'Analyzing the question',
          reasoning: 'Understanding what information the user is looking for',
          result: 'Identified need for API documentation'
        },
        {
          title: 'Selecting relevant URLs',
          reasoning: 'Choosing the most relevant documentation pages',
          result: 'Selected 2 high-quality documentation sources'
        }
      ]
    }
  }

  return (
    <div className="chat-container">
      <WebCrawlerChat message={message} />
    </div>
  )
}
```

## Component Architecture

### Main Components

1. **WebCrawlerChat** - Main orchestrating component
2. **ReasoningStepsDisplay** - Animated reasoning process
3. **SourcesDisplay** - Source URLs with metadata
4. **StreamingContent** - Content with typing cursor

### Hook

- **useWebCrawlerStream** - Handles stream parsing and state management

## Data Flow

```
Stream Data → useWebCrawlerStream → Process Chunk → Update UI Components
     ↓                ↓                    ↓              ↓
JSON Events    Parse Events      Extract Data    Animate Display
```

## Stream Event Processing

The components handle these stream events from your backend:

- `RunStarted` - Initialize streaming state
- `RunResponseContent` - Word-by-word content updates
- `ToolCallStarted/Completed` - Tool execution tracking
- `RunCompleted` - Final response with reasoning steps
- `RunError` - Error handling

## Customization

### Styling

The components use CSS classes that you can override:

```css
.reasoning-steps-container {
  background: #your-color;
  border-radius: 8px;
}

.source-item:hover {
  transform: scale(1.02);
}
```

### Component Props

All components accept `className` prop for custom styling:

```jsx
<ReasoningStepsDisplay 
  steps={steps} 
  className="my-custom-reasoning"
/>
```

## Advanced Usage

### Real-time Streaming

```jsx
import { useWebCrawlerStream } from './web-crawler-ui/hooks/useWebCrawlerStream'

const LiveChat = () => {
  const { streamData, processStreamChunk } = useWebCrawlerStream()
  
  // Connect to your streaming endpoint
  useEffect(() => {
    const eventSource = new EventSource('/api/chat-stream')
    
    eventSource.onmessage = (event) => {
      const chunk = JSON.parse(event.data)
      processStreamChunk(chunk)
    }
    
    return () => eventSource.close()
  }, [])
  
  return (
    <div>
      <ReasoningStepsDisplay steps={streamData.reasoningSteps} />
      <StreamingContent 
        content={streamData.content} 
        isStreaming={streamData.isStreaming} 
      />
      <SourcesDisplay sources={streamData.sources} />
    </div>
  )
}
```

### Custom Message Processing

```jsx
const CustomMessage = ({ message }) => {
  const { streamData, processStreamChunk } = useWebCrawlerStream()
  
  // Process your specific message format
  useEffect(() => {
    if (message.reasoning) {
      processStreamChunk({
        event: 'RunCompleted',
        extra_data: { reasoning_steps: message.reasoning }
      })
    }
  }, [message])
  
  return (
    <div className="custom-message">
      {/* Your custom layout */}
    </div>
  )
}
```

## TypeScript Types

```typescript
interface ChatMessage {
  role: 'user' | 'agent'
  content: string
  created_at: number
  tool_calls?: WebCrawlerToolCall[]
  extra_data?: {
    reasoning_steps?: ReasoningStep[]
  }
}

interface ReasoningStep {
  title: string
  reasoning: string
  result: string
  confidence?: number
}
```

## Backend Integration

Your FastAPI backend should stream events in this format:

```python
# Your streaming response
yield {
  "event": "RunResponseContent",
  "content": "word by word content",
  "created_at": timestamp
}

yield {
  "event": "ToolCallStarted", 
  "tool": {
    "tool_name": "crawl_selected_urls",
    "tool_args": {"urls": ["https://..."]}
  }
}

yield {
  "event": "RunCompleted",
  "content": "final complete response",
  "extra_data": {
    "reasoning_steps": [...]
  }
}
```

## Performance Tips

1. **Debounce Updates** - For high-frequency streaming
2. **Lazy Loading** - For large source lists
3. **Animation Controls** - Disable for slower devices

```jsx
// Disable animations on slower devices
const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
```

## Browser Support

- Chrome 60+
- Firefox 55+
- Safari 12+
- Edge 79+

## License

MIT License - Use freely in your projects.
