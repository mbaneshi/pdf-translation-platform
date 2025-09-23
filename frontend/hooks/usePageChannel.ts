import { useEffect, useRef, useState, useCallback } from 'react'

interface WebSocketMessage {
  type: string
  data: any
  timestamp: string
  page_id?: number
}

interface UsePageChannelOptions {
  documentId: number
  pageNumber: number
  onMessage?: (message: WebSocketMessage) => void
  onStatusUpdate?: (status: string) => void
  onPresenceUpdate?: (presence: any) => void
}

export function usePageChannel({
  documentId,
  pageNumber,
  onMessage,
  onStatusUpdate,
  onPresenceUpdate
}: UsePageChannelOptions) {
  const [isConnected, setIsConnected] = useState(false)
  const [connectionError, setConnectionError] = useState<string | null>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const reconnectAttempts = useRef(0)
  const maxReconnectAttempts = 5

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return
    }

    try {
      // Create WebSocket connection to collaboration endpoint
      const wsUrl = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/api/collab/${pageNumber}`
      const ws = new WebSocket(wsUrl)
      
      ws.onopen = () => {
        console.log('WebSocket connected for page', pageNumber)
        setIsConnected(true)
        setConnectionError(null)
        reconnectAttempts.current = 0

        // Send initial presence message
        sendMessage({
          type: 'presence',
          data: {
            user_id: 'user_' + Math.random().toString(36).substr(2, 9),
            username: 'User',
            role: 'editor',
            page_id: pageNumber
          }
        })
      }

      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data)
          
          // Handle different message types
          switch (message.type) {
            case 'pong':
              // Heartbeat response
              break
            case 'presence_update':
              onPresenceUpdate?.(message.data)
              break
            case 'operation':
              // CRDT operation
              break
            case 'comment':
              // Comment update
              break
            case 'suggestion':
              // Suggestion update
              break
            case 'room_state':
              // Room state update
              break
            case 'error':
              console.error('WebSocket error:', message.data)
              break
            default:
              onMessage?.(message)
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error)
        }
      }

      ws.onclose = (event) => {
        console.log('WebSocket disconnected:', event.code, event.reason)
        setIsConnected(false)
        
        // Attempt to reconnect if not a normal closure
        if (event.code !== 1000 && reconnectAttempts.current < maxReconnectAttempts) {
          const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000)
          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectAttempts.current++
            connect()
          }, delay)
        }
      }

      ws.onerror = (error) => {
        console.error('WebSocket error:', error)
        setConnectionError('Connection failed')
        setIsConnected(false)
      }

      wsRef.current = ws
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error)
      setConnectionError('Failed to connect')
    }
  }, [pageNumber, onMessage, onPresenceUpdate])

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }

    if (wsRef.current) {
      wsRef.current.close(1000, 'Component unmounting')
      wsRef.current = null
    }
    
    setIsConnected(false)
  }, [])

  const sendMessage = useCallback((message: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message))
    } else {
      console.warn('WebSocket not connected, cannot send message:', message)
    }
  }, [])

  const sendPing = useCallback(() => {
    sendMessage({ type: 'ping' })
  }, [sendMessage])

  // Connect on mount and when page changes
  useEffect(() => {
    connect()
    return () => disconnect()
  }, [connect, disconnect])

  // Send periodic pings to keep connection alive
  useEffect(() => {
    if (!isConnected) return

    const pingInterval = setInterval(sendPing, 30000) // Ping every 30 seconds
    return () => clearInterval(pingInterval)
  }, [isConnected, sendPing])

  return {
    isConnected,
    connectionError,
    sendMessage,
    reconnect: connect
  }
}
