import React, { useEffect } from 'react'
import { useWebCrawlerStream } from '../hooks/useWebCrawlerStream'
import ReasoningStepsDisplay from './ReasoningSteps'
import SourcesDisplay from './SourcesDisplay'
import StreamingContent from './StreamingContent'
import type { ChatMessage } from '../types/streaming'

interface WebCrawlerChatProps {
  message: ChatMessage
  className?: string
}

const WebCrawlerChat: React.FC<WebCrawlerChatProps> = ({ 
  message, 
  className = '' 
}) => {
  const { streamData, processStreamChunk, resetStream } = useWebCrawlerStream()
  
  // Process existing message data on mount
  useEffect(() => {
    if (message.tool_calls || message.extra_data?.reasoning_steps) {
      resetStream()
      
      // Simulate processing chunks from existing message data
      if (message.tool_calls) {
        message.tool_calls.forEach(toolCall => {
          processStreamChunk({
            event: 'ToolCallCompleted',
            tool: toolCall,
            created_at: message.created_at
          })
        })
      }
      
      if (message.extra_data?.reasoning_steps) {
        processStreamChunk({
          event: 'RunCompleted',
          content: message.content,
          extra_data: message.extra_data,
          created_at: message.created_at
        })
      }
    }
  }, [message, processStreamChunk, resetStream])
  
  if (message.role === 'user') {
    return (
      <div className={`user-message ${className}`}>
        <div className="user-avatar">👤</div>
        <div className="user-content">{message.content}</div>
      </div>
    )
  }
  
  return (
    <div className={`agent-message ${className}`}>
      <div className="agent-avatar">🤖</div>
      <div className="agent-response">
        {/* Reasoning Steps - Show first with animation */}
        {streamData.reasoningSteps.length > 0 && (
          <ReasoningStepsDisplay 
            steps={streamData.reasoningSteps} 
            className="mb-6"
          />
        )}
        
        {/* Main Content */}
        {message.content && (
          <div className="main-response mb-6">
            <div className="response-header">
              <span className="response-icon">💬</span>
              <h3 className="response-title">Response</h3>
            </div>
            <div className="response-content">
              <StreamingContent 
                content={message.content} 
                isStreaming={streamData.isStreaming}
              />
            </div>
          </div>
        )}
        
        {/* Sources - Show at the end */}
        {streamData.sources.length > 0 && (
          <SourcesDisplay 
            sources={streamData.sources} 
            className="mb-4"
          />
        )}
      </div>
    </div>
  )
}

export default WebCrawlerChat
