import React, { useState, useEffect } from 'react'
import type { ReasoningStep } from '../types/streaming'

interface ReasoningStepsProps {
  steps: ReasoningStep[]
  className?: string
}

const ReasoningStepsDisplay: React.FC<ReasoningStepsProps> = ({ 
  steps, 
  className = '' 
}) => {
  const [visibleSteps, setVisibleSteps] = useState<number>(0)
  const [isAnimating, setIsAnimating] = useState(false)
  
  useEffect(() => {
    if (steps.length === 0) {
      setVisibleSteps(0)
      setIsAnimating(false)
      return
    }
    
    setIsAnimating(true)
    setVisibleSteps(0)
    
    // Animate steps one by one with delays
    const timer = setInterval(() => {
      setVisibleSteps((prev: number) => {
        if (prev >= steps.length) {
          clearInterval(timer)
          setIsAnimating(false)
          return prev
        }
        return prev + 1
      })
    }, 800) // 800ms delay between steps
    
    return () => {
      clearInterval(timer)
      setIsAnimating(false)
    }
  }, [steps.length])
  
  if (steps.length === 0) return null
  
  return (
    <div className={`reasoning-steps-container ${className}`}>
      <div className="reasoning-header">
        <span className="reasoning-icon">🧠</span>
        <h3 className="reasoning-title">AI Reasoning Process</h3>
      </div>
      
      <div className="reasoning-steps">
        {steps.slice(0, visibleSteps).map((step, index) => (
          <div 
            key={index} 
            className="reasoning-step animate-fadeInUp"
            style={{
              animationDelay: `${index * 0.1}s`,
              animationFillMode: 'both'
            }}
          >
            <div className="step-content">
              <div className="step-number">
                {index + 1}
              </div>
              <div className="step-details">
                <div className="step-title">
                  {step.title}
                </div>
                {step.reasoning && (
                  <div className="step-reasoning">
                    {step.reasoning}
                  </div>
                )}
                {step.result && (
                  <div className="step-result">
                    <span className="checkmark">✓</span>
                    <span>{step.result}</span>
                  </div>
                )}
                {step.confidence && (
                  <div className="step-confidence">
                    Confidence: {Math.round(step.confidence * 100)}%
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
        
        {isAnimating && visibleSteps < steps.length && (
          <div className="reasoning-loading">
            <div className="loading-spinner"></div>
            <span className="loading-text">Thinking...</span>
          </div>
        )}
      </div>
    </div>
  )
}

export default ReasoningStepsDisplay
