export interface ReasoningStep {
  title: string
  action?: string
  result: string
  reasoning: string
  confidence?: number
  next_action?: string
}

export interface WebCrawlerToolCall {
  tool_call_id: string
  tool_name: string
  tool_args: {
    urls?: string[]
    [key: string]: any
  }
  result?: string
  metrics?: {
    time: number
  }
  created_at: number
}

export interface SourceURL {
  url: string
  domain: string
  title?: string
}

export interface WebCrawlerStreamData {
  reasoningSteps: ReasoningStep[]
  content: string
  sources: SourceURL[]
  toolCalls: WebCrawlerToolCall[]
  isStreaming: boolean
}

export interface StreamChunk {
  event: 'RunStarted' | 'RunResponseContent' | 'ToolCallStarted' | 'ToolCallCompleted' | 'RunCompleted' | 'RunError'
  content?: string | object
  created_at: number
  agent_id?: string
  session_id?: string
  tool?: WebCrawlerToolCall
  extra_data?: {
    reasoning_steps?: ReasoningStep[]
    [key: string]: any
  }
}

export interface ChatMessage {
  role: 'user' | 'agent'
  content: string
  created_at: number
  tool_calls?: WebCrawlerToolCall[]
  extra_data?: {
    reasoning_steps?: ReasoningStep[]
    [key: string]: any
  }
}
