import React from 'react'

interface StreamingContentProps {
  content: string
  isStreaming?: boolean
  className?: string
}

const StreamingContent: React.FC<StreamingContentProps> = ({ 
  content, 
  isStreaming = false, 
  className = '' 
}) => {
  return (
    <div className={`streaming-content ${className}`}>
      <div className="content-text">
        {content}
        {isStreaming && (
          <span className="streaming-cursor">|</span>
        )}
      </div>
    </div>
  )
}

export default StreamingContent
