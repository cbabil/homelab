/**
 * Settings State Hook
 *
 * Custom hook to manage settings page state and handlers.
 */

import { useState, useEffect, useCallback } from 'react';
import { Session, SortKey } from './types';
import { settingsLogger } from '@/services/systemLogger';
import { useMCP } from '@/providers/MCPProvider';
import { useSettingsContext } from '@/providers/SettingsProvider';
import { useSettingsSaving } from './SettingsSavingContext';

export function useSettingsState() {
  // Get MCP provider status
  const { isConnected, error } = useMCP();

  // Get settings from context
  const { settings, updateSettings } = useSettingsContext();

  // Get saving state setter for indicator
  const { setIsSaving } = useSettingsSaving();

  const [activeTab, setActiveTab] = useState('general');
  const [activeServerTab, setActiveServerTab] = useState('ssh');

  // Notification settings from context with defaults
  const serverAlerts = settings?.notifications?.serverAlerts ?? true;
  const resourceAlerts = settings?.notifications?.resourceAlerts ?? true;
  const updateAlerts = settings?.notifications?.updateAlerts ?? false;

  // Server settings from context with defaults
  const connectionTimeout = String(settings?.servers?.connectionTimeout ?? 30);
  const retryCount = String(settings?.servers?.retryCount ?? 3);
  const autoRetry = settings?.servers?.autoRetry ?? true;

  // Agent settings from context with defaults
  const preferAgent = settings?.agent?.preferAgent ?? true;
  const agentAutoUpdate = settings?.agent?.autoUpdate ?? true;
  const heartbeatInterval = String(settings?.agent?.heartbeatInterval ?? 30);
  const heartbeatTimeout = String(settings?.agent?.heartbeatTimeout ?? 90);
  const commandTimeout = String(settings?.agent?.commandTimeout ?? 120);

  // Helper to wrap updateSettings with saving indicator
  const saveWithIndicator = useCallback(
    async (section: 'notifications' | 'servers' | 'agent', updates: Record<string, unknown>) => {
      setIsSaving(true);
      try {
        await updateSettings(section, updates);
      } finally {
        setIsSaving(false);
      }
    },
    [updateSettings, setIsSaving]
  );

  // Handlers that persist to settings
  const setServerAlerts = useCallback(
    (checked: boolean) => {
      saveWithIndicator('notifications', { serverAlerts: checked });
    },
    [saveWithIndicator]
  );

  const setResourceAlerts = useCallback(
    (checked: boolean) => {
      saveWithIndicator('notifications', { resourceAlerts: checked });
    },
    [saveWithIndicator]
  );

  const setUpdateAlerts = useCallback(
    (checked: boolean) => {
      saveWithIndicator('notifications', { updateAlerts: checked });
    },
    [saveWithIndicator]
  );

  const setConnectionTimeout = useCallback(
    (timeout: string) => {
      saveWithIndicator('servers', { connectionTimeout: parseInt(timeout, 10) });
    },
    [saveWithIndicator]
  );

  const setRetryCount = useCallback(
    (count: string) => {
      saveWithIndicator('servers', { retryCount: parseInt(count, 10) });
    },
    [saveWithIndicator]
  );

  const setAutoRetry = useCallback(
    (enabled: boolean) => {
      saveWithIndicator('servers', { autoRetry: enabled });
    },
    [saveWithIndicator]
  );

  // Agent settings handlers
  const setPreferAgent = useCallback(
    (checked: boolean) => {
      saveWithIndicator('agent', { preferAgent: checked });
    },
    [saveWithIndicator]
  );

  const setAgentAutoUpdate = useCallback(
    (checked: boolean) => {
      saveWithIndicator('agent', { autoUpdate: checked });
    },
    [saveWithIndicator]
  );

  const setHeartbeatInterval = useCallback(
    (interval: string) => {
      saveWithIndicator('agent', { heartbeatInterval: parseInt(interval, 10) });
    },
    [saveWithIndicator]
  );

  const setHeartbeatTimeout = useCallback(
    (timeout: string) => {
      saveWithIndicator('agent', { heartbeatTimeout: parseInt(timeout, 10) });
    },
    [saveWithIndicator]
  );

  const setCommandTimeout = useCallback(
    (timeout: string) => {
      saveWithIndicator('agent', { commandTimeout: parseInt(timeout, 10) });
    },
    [saveWithIndicator]
  );

  // Load MCP config from localStorage or use default
  const getInitialMcpConfig = () => {
    try {
      const saved = localStorage.getItem('tomo-mcp-config');
      if (saved) {
        const config = JSON.parse(saved);
        settingsLogger.info('Loaded MCP config from localStorage', {
          servers: Object.keys(config.mcpServers || {}),
        });
        return config;
      }
    } catch (error) {
      settingsLogger.warn('Failed to load MCP config from localStorage', error);
    }

    // Default configuration
    settingsLogger.info('Using default MCP configuration');
    return {
      mcpServers: {
        tomo: {
          type: 'http',
          url: import.meta.env.VITE_MCP_SERVER_URL || '/mcp',
          name: 'Tomo',
          description: 'Local tomo management MCP server',
        },
      },
    };
  };

  // MCP Configuration state
  const [mcpConfig, setMcpConfigState] = useState(getInitialMcpConfig);

  // Wrapper to persist to localStorage when MCP config changes
  const setMcpConfig = (newConfig: typeof mcpConfig) => {
    settingsLogger.info('Persisting MCP config to localStorage', {
      servers: Object.keys(newConfig.mcpServers || {}),
    });
    setMcpConfigState(newConfig);
    try {
      localStorage.setItem('tomo-mcp-config', JSON.stringify(newConfig));
      settingsLogger.info('MCP config successfully saved to localStorage');
    } catch (error) {
      settingsLogger.warn('Failed to save MCP config to localStorage', error);
    }
  };
  const [isEditingMcpConfig, setIsEditingMcpConfig] = useState(false);
  const [mcpConfigText, setMcpConfigText] = useState('');
  const [originalMcpConfig, setOriginalMcpConfig] = useState('');
  const [mcpConfigError, setMcpConfigError] = useState('');

  // MCP Connection state - sync with actual provider
  const [mcpConnectionStatus, setMcpConnectionStatus] = useState<
    'disconnected' | 'connecting' | 'connected' | 'error'
  >('disconnected');
  const [mcpConnectionError, setMcpConnectionError] = useState('');

  // Sync MCP connection status with actual provider
  useEffect(() => {
    if (isConnected) {
      setMcpConnectionStatus('connected');
      setMcpConnectionError('');
    } else if (error) {
      setMcpConnectionStatus('error');
      setMcpConnectionError(error);
    } else {
      setMcpConnectionStatus('disconnected');
      setMcpConnectionError('');
    }
  }, [isConnected, error]);

  // Session table state
  const [sortBy, setSortBy] = useState<SortKey>('lastActivity');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  // Mock session data
  const [sessions, setSessions] = useState<Session[]>([
    {
      id: 'sess_****7a2f',
      userId: 'user-123',
      username: 'admin',
      status: 'active',
      started: new Date('2024-01-15T09:15:00'),
      lastActivity: new Date(Date.now() - 2 * 60 * 1000), // 2 minutes ago
      expiresAt: new Date(Date.now() + 60 * 60 * 1000), // 1 hour from now
      location: '192.168.1.*** (Local network)',
      ip: '192.168.1.100',
      isCurrent: true,
    },
    {
      id: 'sess_****9b4c',
      userId: 'user-123',
      username: 'admin',
      status: 'idle',
      started: new Date('2024-01-15T08:30:00'),
      lastActivity: new Date(Date.now() - 45 * 60 * 1000), // 45 minutes ago
      expiresAt: new Date(Date.now() + 15 * 60 * 1000), // 15 minutes from now
      location: '10.0.1.*** (VPN)',
      ip: '10.0.1.50',
      isCurrent: false,
    },
    // Additional sessions truncated for brevity
  ]);

  return {
    // State
    activeTab,
    activeServerTab,
    serverAlerts,
    resourceAlerts,
    updateAlerts,
    autoRetry,
    connectionTimeout,
    retryCount,
    mcpConfig,
    isEditingMcpConfig,
    mcpConfigText,
    originalMcpConfig,
    mcpConfigError,
    mcpConnectionStatus,
    mcpConnectionError,
    sortBy,
    sortOrder,
    sessions,
    // Agent settings state
    preferAgent,
    agentAutoUpdate,
    heartbeatInterval,
    heartbeatTimeout,
    commandTimeout,

    // Setters
    setActiveTab,
    setActiveServerTab,
    setServerAlerts,
    setResourceAlerts,
    setUpdateAlerts,
    setAutoRetry,
    setConnectionTimeout,
    setRetryCount,
    setMcpConfig,
    setIsEditingMcpConfig,
    setMcpConfigText,
    setOriginalMcpConfig,
    setMcpConfigError,
    setMcpConnectionStatus,
    setMcpConnectionError,
    setSortBy,
    setSortOrder,
    setSessions,
    // Agent settings setters
    setPreferAgent,
    setAgentAutoUpdate,
    setHeartbeatInterval,
    setHeartbeatTimeout,
    setCommandTimeout,
  };
}
