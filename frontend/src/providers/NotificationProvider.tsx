/**
 * Notification Provider Component
 *
 * Manages application-wide notifications including connection status,
 * alerts, and system messages. Syncs with backend via MCP.
 */

import React, { createContext, useContext, useState, useCallback, useEffect, useRef, ReactNode } from 'react'
import { useMCP } from '@/providers/MCPProvider'
import { NotificationMcpClient, BackendNotification } from '@/services/notificationMcpClient'
import { mcpLogger } from '@/services/systemLogger'

export interface Notification {
  id: string
  type: 'info' | 'success' | 'warning' | 'error'
  title: string
  message: string
  timestamp: Date
  read: boolean
}

interface NotificationContextType {
  notifications: Notification[]
  unreadCount: number
  isLoading: boolean
  addNotification: (notification: Omit<Notification, 'id' | 'timestamp' | 'read'>) => void
  markAsRead: (id: string) => void
  markAllAsRead: () => void
  removeNotification: (id: string) => void
  clearAll: () => void
  refresh: () => Promise<void>
}

const NotificationContext = createContext<NotificationContextType | undefined>(undefined)

// Poll interval for checking new notifications (30 seconds)
const POLL_INTERVAL = 30000

/**
 * Convert backend notification to frontend format
 */
function mapBackendToFrontend(backend: BackendNotification): Notification {
  return {
    id: backend.id,
    type: backend.type,
    title: backend.title,
    message: backend.message,
    timestamp: new Date(backend.created_at),
    read: backend.read
  }
}

/**
 * Custom hook for notification state management
 */
function useNotificationState() {
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [unreadCount, setUnreadCount] = useState(0)
  const [isLoading, setIsLoading] = useState(true)

  const { client, isConnected } = useMCP()
  const mcpClientRef = useRef<NotificationMcpClient | null>(null)

  useEffect(() => {
    if (client && isConnected) {
      mcpClientRef.current = new NotificationMcpClient(client, () => isConnected)
    } else {
      mcpClientRef.current = null
    }
  }, [client, isConnected])

  return {
    notifications, setNotifications,
    unreadCount, setUnreadCount,
    isLoading, setIsLoading,
    isConnected, mcpClientRef
  }
}

/**
 * Custom hook for notification fetching logic
 */
function useNotificationFetcher(
  mcpClientRef: React.RefObject<NotificationMcpClient | null>,
  setNotifications: React.Dispatch<React.SetStateAction<Notification[]>>,
  setUnreadCount: React.Dispatch<React.SetStateAction<number>>,
  setIsLoading: React.Dispatch<React.SetStateAction<boolean>>,
  isConnected: boolean
) {
  const fetchNotifications = useCallback(async () => {
    if (!mcpClientRef.current?.isConnected()) {
      mcpLogger.info('MCP not connected, skipping notification fetch')
      return
    }

    try {
      const result = await mcpClientRef.current.getNotifications({ limit: 100 })
      const mappedNotifications = result.notifications.map(mapBackendToFrontend)
      setNotifications(mappedNotifications)
      setUnreadCount(result.unread_count)
      setIsLoading(false)
    } catch (error) {
      mcpLogger.error('Failed to fetch notifications', { error })
      setIsLoading(false)
    }
  }, [mcpClientRef, setNotifications, setUnreadCount, setIsLoading])

  useEffect(() => {
    if (isConnected && mcpClientRef.current) {
      fetchNotifications()
    }
  }, [isConnected, mcpClientRef, fetchNotifications])

  useEffect(() => {
    if (!isConnected) return
    const intervalId = setInterval(() => fetchNotifications(), POLL_INTERVAL)
    return () => clearInterval(intervalId)
  }, [isConnected, fetchNotifications])

  return fetchNotifications
}

/**
 * Custom hook for notification actions
 */
function useNotificationActions(
  mcpClientRef: React.RefObject<NotificationMcpClient | null>,
  notifications: Notification[],
  setNotifications: React.Dispatch<React.SetStateAction<Notification[]>>,
  setUnreadCount: React.Dispatch<React.SetStateAction<number>>,
  setIsLoading: React.Dispatch<React.SetStateAction<boolean>>,
  fetchNotifications: () => Promise<void>
) {
  const addNotification = useCallback(async (
    notification: Omit<Notification, 'id' | 'timestamp' | 'read'>
  ) => {
    const tempNotification: Notification = {
      ...notification, id: `temp_${Date.now()}`, timestamp: new Date(), read: false
    }
    setNotifications(prev => [tempNotification, ...prev])
    setUnreadCount(prev => prev + 1)

    if (mcpClientRef.current?.isConnected()) {
      try {
        const created = await mcpClientRef.current.createNotification({
          type: notification.type, title: notification.title,
          message: notification.message, source: 'frontend'
        })
        if (created) {
          setNotifications(prev => prev.map(n =>
            n.id === tempNotification.id ? mapBackendToFrontend(created) : n
          ))
        }
      } catch (error) {
        mcpLogger.error('Failed to create notification in backend', { error })
      }
    }
  }, [mcpClientRef, setNotifications, setUnreadCount])

  const markAsRead = useCallback(async (id: string) => {
    setNotifications(prev => prev.map(n => n.id === id ? { ...n, read: true } : n))
    setUnreadCount(prev => Math.max(0, prev - 1))
    if (mcpClientRef.current?.isConnected() && !id.startsWith('temp_')) {
      try { await mcpClientRef.current.markAsRead(id) }
      catch (error) { mcpLogger.error('Failed to mark notification as read', { error }) }
    }
  }, [mcpClientRef, setNotifications, setUnreadCount])

  const markAllAsRead = useCallback(async () => {
    setNotifications(prev => prev.map(n => ({ ...n, read: true })))
    setUnreadCount(0)
    if (mcpClientRef.current?.isConnected()) {
      try { await mcpClientRef.current.markAllAsRead() }
      catch (error) { mcpLogger.error('Failed to mark all as read', { error }) }
    }
  }, [mcpClientRef, setNotifications, setUnreadCount])

  const removeNotification = useCallback(async (id: string) => {
    const notification = notifications.find(n => n.id === id)
    setNotifications(prev => prev.filter(n => n.id !== id))
    if (notification && !notification.read) setUnreadCount(prev => Math.max(0, prev - 1))
    if (mcpClientRef.current?.isConnected() && !id.startsWith('temp_')) {
      try { await mcpClientRef.current.dismissNotification(id) }
      catch (error) { mcpLogger.error('Failed to dismiss notification', { error }) }
    }
  }, [mcpClientRef, notifications, setNotifications, setUnreadCount])

  const clearAll = useCallback(async () => {
    setNotifications([])
    setUnreadCount(0)
    if (mcpClientRef.current?.isConnected()) {
      try { await mcpClientRef.current.dismissAll() }
      catch (error) { mcpLogger.error('Failed to dismiss all notifications', { error }) }
    }
  }, [mcpClientRef, setNotifications, setUnreadCount])

  const refresh = useCallback(async () => {
    setIsLoading(true)
    await fetchNotifications()
  }, [setIsLoading, fetchNotifications])

  return { addNotification, markAsRead, markAllAsRead, removeNotification, clearAll, refresh }
}

export function NotificationProvider({ children }: { children: ReactNode }) {
  const state = useNotificationState()
  const fetchNotifications = useNotificationFetcher(
    state.mcpClientRef, state.setNotifications,
    state.setUnreadCount, state.setIsLoading, state.isConnected
  )
  const actions = useNotificationActions(
    state.mcpClientRef, state.notifications, state.setNotifications,
    state.setUnreadCount, state.setIsLoading, fetchNotifications
  )

  return (
    <NotificationContext.Provider
      value={{
        notifications: state.notifications,
        unreadCount: state.unreadCount,
        isLoading: state.isLoading,
        ...actions
      }}
    >
      {children}
    </NotificationContext.Provider>
  )
}

export function useNotifications() {
  const context = useContext(NotificationContext)
  if (context === undefined) {
    throw new Error('useNotifications must be used within a NotificationProvider')
  }
  return context
}
