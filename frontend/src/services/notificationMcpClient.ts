/**
 * Notification MCP Client
 *
 * MCP client for notification operations (list, mark read, dismiss, etc.).
 * Provides type-safe interface for managing user notifications from the backend.
 */

import { useMCP } from '@/providers/MCPProvider'
import { mcpLogger } from '@/services/systemLogger'

// Backend notification type (matches NotificationListResponse from backend)
export interface BackendNotification {
  id: string
  user_id: string
  type: 'info' | 'success' | 'warning' | 'error'
  title: string
  message: string
  read: boolean
  created_at: string  // ISO string
  read_at: string | null
  source: string | null
  metadata: Record<string, unknown> | null
}

// Response type for list_notifications
interface ListNotificationsResponse {
  success: boolean
  data?: {
    notifications: BackendNotification[]
    total: number
    unread_count: number
  }
  message?: string
  error?: string
}

// Response type for get_unread_count
interface UnreadCountResponse {
  success: boolean
  data?: {
    unread_count: number
    total: number
  }
  message?: string
  error?: string
}

// Response type for mark read / dismiss operations
interface NotificationActionResponse {
  success: boolean
  data?: { updated?: boolean; dismissed?: boolean; count?: number }
  message?: string
  error?: string
}

// Response type for create_notification
interface CreateNotificationResponse {
  success: boolean
  data?: BackendNotification
  message?: string
  error?: string
}

/**
 * MCP-based Notification Client
 *
 * Handles all notification operations through the backend MCP tools
 * with proper error handling and type safety.
 */
export class NotificationMcpClient {
  private mcpClient: ReturnType<typeof useMCP>['client']
  private isConnectedFn: () => boolean

  constructor(mcpClient: ReturnType<typeof useMCP>['client'], isConnected: () => boolean) {
    this.mcpClient = mcpClient
    this.isConnectedFn = isConnected
    mcpLogger.info('Notification MCP Client initialized')
  }

  /**
   * Get notifications list
   *
   * @param options - Filter options
   */
  async getNotifications(options?: {
    read?: boolean
    type?: 'info' | 'success' | 'warning' | 'error'
    limit?: number
    offset?: number
  }): Promise<{
    notifications: BackendNotification[]
    total: number
    unread_count: number
  }> {
    try {
      mcpLogger.info('Getting notifications list', options)

      // Build inner params object
      const innerParams: Record<string, unknown> = {}
      if (options?.read !== undefined) innerParams.read = options.read
      if (options?.type) innerParams.type = options.type
      if (options?.limit) innerParams.limit = options.limit
      if (options?.offset) innerParams.offset = options.offset

      // Backend NotificationTools expects { params: {...} } structure
      const response = await this.mcpClient.callTool<ListNotificationsResponse>(
        'list_notifications',
        { params: innerParams }
      )

      if (!response.success) {
        mcpLogger.error('Failed to get notifications', { error: response.error })
        return { notifications: [], total: 0, unread_count: 0 }
      }

      // Handle the response data structure
      const responseData = response.data as ListNotificationsResponse
      const data = responseData?.data || { notifications: [], total: 0, unread_count: 0 }
      mcpLogger.info('Notifications retrieved successfully', { count: data.notifications.length })
      return data
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error'
      mcpLogger.error('Notifications retrieval failed', { error: errorMessage })
      return { notifications: [], total: 0, unread_count: 0 }
    }
  }

  /**
   * Get unread notification count
   */
  async getUnreadCount(): Promise<{ unread_count: number; total: number }> {
    try {
      mcpLogger.info('Getting unread notification count')

      const response = await this.mcpClient.callTool<UnreadCountResponse>(
        'get_unread_count',
        { params: {} }
      )

      if (!response.success) {
        mcpLogger.error('Failed to get unread count', { error: response.error })
        return { unread_count: 0, total: 0 }
      }

      const responseData = response.data as UnreadCountResponse
      const data = responseData?.data || { unread_count: 0, total: 0 }
      mcpLogger.info('Unread count retrieved', data)
      return data
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error'
      mcpLogger.error('Get unread count failed', { error: errorMessage })
      return { unread_count: 0, total: 0 }
    }
  }

  /**
   * Mark a notification as read
   *
   * @param notificationId - Notification ID to mark as read
   */
  async markAsRead(notificationId: string): Promise<boolean> {
    try {
      mcpLogger.info('Marking notification as read', { notificationId })

      const response = await this.mcpClient.callTool<NotificationActionResponse>(
        'mark_notification_read',
        { params: { notification_id: notificationId } }
      )

      if (!response.success) {
        mcpLogger.error('Failed to mark notification as read', { error: response.error })
        return false
      }

      const responseData = response.data as NotificationActionResponse
      const updated = responseData?.data?.updated || false
      mcpLogger.info('Notification marked as read', { notificationId, updated })
      return updated
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error'
      mcpLogger.error('Mark as read failed', { error: errorMessage })
      return false
    }
  }

  /**
   * Mark all notifications as read
   */
  async markAllAsRead(): Promise<number> {
    try {
      mcpLogger.info('Marking all notifications as read')

      const response = await this.mcpClient.callTool<NotificationActionResponse>(
        'mark_all_notifications_read',
        { params: {} }
      )

      if (!response.success) {
        mcpLogger.error('Failed to mark all as read', { error: response.error })
        return 0
      }

      const responseData = response.data as NotificationActionResponse
      const count = responseData?.data?.count || 0
      mcpLogger.info('All notifications marked as read', { count })
      return count
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error'
      mcpLogger.error('Mark all as read failed', { error: errorMessage })
      return 0
    }
  }

  /**
   * Dismiss a notification
   *
   * @param notificationId - Notification ID to dismiss
   */
  async dismissNotification(notificationId: string): Promise<boolean> {
    try {
      mcpLogger.info('Dismissing notification', { notificationId })

      const response = await this.mcpClient.callTool<NotificationActionResponse>(
        'dismiss_notification',
        { params: { notification_id: notificationId } }
      )

      if (!response.success) {
        mcpLogger.error('Failed to dismiss notification', { error: response.error })
        return false
      }

      const responseData = response.data as NotificationActionResponse
      const dismissed = responseData?.data?.dismissed || false
      mcpLogger.info('Notification dismissed', { notificationId, dismissed })
      return dismissed
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error'
      mcpLogger.error('Dismiss notification failed', { error: errorMessage })
      return false
    }
  }

  /**
   * Dismiss all notifications
   */
  async dismissAll(): Promise<number> {
    try {
      mcpLogger.info('Dismissing all notifications')

      const response = await this.mcpClient.callTool<NotificationActionResponse>(
        'dismiss_all_notifications',
        { params: {} }
      )

      if (!response.success) {
        mcpLogger.error('Failed to dismiss all notifications', { error: response.error })
        return 0
      }

      const responseData = response.data as NotificationActionResponse
      const count = responseData?.data?.count || 0
      mcpLogger.info('All notifications dismissed', { count })
      return count
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error'
      mcpLogger.error('Dismiss all failed', { error: errorMessage })
      return 0
    }
  }

  /**
   * Create a notification (admin/system use)
   */
  async createNotification(options: {
    userId?: string
    type: 'info' | 'success' | 'warning' | 'error'
    title: string
    message: string
    source?: string
    metadata?: Record<string, unknown>
  }): Promise<BackendNotification | null> {
    try {
      mcpLogger.info('Creating notification', options)

      const innerParams: Record<string, unknown> = {
        type: options.type,
        title: options.title,
        message: options.message
      }
      if (options.userId) innerParams.user_id = options.userId
      if (options.source) innerParams.source = options.source
      if (options.metadata) innerParams.metadata = options.metadata

      const response = await this.mcpClient.callTool<CreateNotificationResponse>(
        'create_notification',
        { params: innerParams }
      )

      if (!response.success) {
        mcpLogger.error('Failed to create notification', { error: response.error })
        return null
      }

      const responseData = response.data as CreateNotificationResponse
      mcpLogger.info('Notification created', { id: responseData?.data?.id })
      return responseData?.data || null
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error'
      mcpLogger.error('Create notification failed', { error: errorMessage })
      return null
    }
  }

  /**
   * Check if the MCP client is connected
   */
  isConnected(): boolean {
    return this.isConnectedFn()
  }
}

/**
 * Hook to get Notification MCP Client
 */
export function useNotificationMcpClient(): NotificationMcpClient | null {
  try {
    const { client, isConnected } = useMCP()
    return new NotificationMcpClient(client, () => isConnected)
  } catch (_error) {
    // useMCP will throw if not within MCPProvider
    mcpLogger.warn('Notification MCP Client not available - no MCP provider')
    return null
  }
}
