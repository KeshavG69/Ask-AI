import React from 'react'
import type { SourceURL } from '../types/streaming'

interface SourcesDisplayProps {
  sources: SourceURL[]
  className?: string
}

const SourcesDisplay: React.FC<SourcesDisplayProps> = ({ 
  sources, 
  className = '' 
}) => {
  if (sources.length === 0) return null
  
  return (
    <div className={`sources-section ${className}`}>
      <div className="sources-header">
        <span className="sources-icon">📚</span>
        <h3 className="sources-title">Sources</h3>
      </div>
      
      <div className="sources-list">
        {sources.map((source, index) => (
          <div key={index} className="source-item">
            <div className="source-content">
              <span className="source-link-icon">🔗</span>
              <div className="source-details">
                <div className="source-title">
                  {source.title || source.url.split('/').pop() || source.domain}
                </div>
                <div className="source-domain">
                  {source.domain}
                </div>
                <div className="source-url">
                  {source.url}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
      
      <div className="sources-count">
        {sources.length} source{sources.length !== 1 ? 's' : ''} crawled
      </div>
    </div>
  )
}

export default SourcesDisplay
