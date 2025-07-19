import { useState, useCallback, useRef } from 'react'
import type { ReasoningStep, SourceURL, WebCrawlerToolCall, WebCrawlerStreamData } from '../types/streaming'

class ContentDeduplicator {
  private lastContent = ''
  
  getUniqueContent(newContent: string): string {
    if (!newContent || typeof newContent !== 'string') return ''
    
    // If new content is completely different, return it all
    if (!this.lastContent || !newContent.includes(this.lastContent)) {
      this.lastContent = newContent
      return newContent
    }
    
    // Extract only the new part
    const uniqueContent = newContent.slice(this.lastContent.length)
    this.lastContent = newContent
    return uniqueContent
  }
  
  reset(): void {
    this.lastContent = ''
  }
}

const extractSourcesFromUrl = (url: string): SourceURL => {
  try {
    const urlObj = new URL(url)
    return {
      url,
      domain: urlObj.hostname,
      title: url.split('/').pop()?.replace(/\.[^/.]+$/, '') || urlObj.pathname
    }
  } catch {
    return {
      url,
      domain: 'Unknown',
      title: url
    }
  }
}

export const useWebCrawlerStream = () => {
  const [streamData, setStreamData] = useState<WebCrawlerStreamData>({
    reasoningSteps: [],
    content: '',
    sources: [],
    toolCalls: [],
    isStreaming: false
  })
  
  const contentDeduplicator = useRef(new ContentDeduplicator())
  
  const resetStream = useCallback(() => {
    contentDeduplicator.current.reset()
    setStreamData({
      reasoningSteps: [],
      content: '',
      sources: [],
      toolCalls: [],
      isStreaming: false
    })
  }, [])
  
  const updateToolCalls = useCallback((existingCalls: WebCrawlerToolCall[], newTool: WebCrawlerToolCall): WebCrawlerToolCall[] => {
    const existingIndex = existingCalls.findIndex(
      call => call.tool_call_id === newTool.tool_call_id
    )
    
    if (existingIndex >= 0) {
      const updated = [...existingCalls]
      updated[existingIndex] = { ...updated[existingIndex], ...newTool }
      return updated
    } else {
      return [...existingCalls, newTool]
    }
  }, [])
  
  const processStreamChunk = useCallback((chunk: any) => {
    console.log('Processing chunk:', chunk.event, chunk)
    
    setStreamData((prev: WebCrawlerStreamData) => {
      const newData = { ...prev }
      
      switch (chunk.event) {
        case 'RunStarted':
          newData.isStreaming = true
          break
          
        case 'RunResponseContent':
          if (typeof chunk.content === 'string') {
            const uniqueContent = contentDeduplicator.current.getUniqueContent(chunk.content)
            if (uniqueContent) {
              newData.content = prev.content + uniqueContent
            }
          }
          break
          
        case 'ToolCallStarted':
        case 'ToolCallCompleted':
          if (chunk.tool) {
            newData.toolCalls = updateToolCalls(prev.toolCalls, chunk.tool)
            
            // Extract sources from crawl_selected_urls tool
            if (chunk.tool.tool_name === 'crawl_selected_urls' && chunk.tool.tool_args?.urls) {
              const sources = chunk.tool.tool_args.urls.map(extractSourcesFromUrl)
              newData.sources = sources
            }
          }
          break
          
        case 'RunCompleted':
          newData.isStreaming = false
          
          // Set final content if provided
          if (typeof chunk.content === 'string') {
            newData.content = chunk.content
          }
          
          // Extract reasoning steps
          if (chunk.extra_data?.reasoning_steps) {
            newData.reasoningSteps = chunk.extra_data.reasoning_steps
          }
          
          // Update final tool calls
          if (chunk.tool) {
            newData.toolCalls = updateToolCalls(prev.toolCalls, chunk.tool)
          }
          break
          
        case 'RunError':
          newData.isStreaming = false
          break
      }
      
      return newData
    })
  }, [updateToolCalls])
  
  return {
    streamData,
    processStreamChunk,
    resetStream
  }
}
