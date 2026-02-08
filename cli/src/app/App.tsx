import { Box, useApp, useInput, useStdout } from 'ink';
import React, { useState, useCallback, useEffect, useRef } from 'react';

import { routeCommand } from './CommandRouter.js';
import { createMessage, initialAppState } from './types.js';
import type { AppState, OutputMessage } from './types.js';
import type { ActivityEntry, ViewMode } from './dashboard-types.js';
import { createActivityEntry, NAV_ITEMS } from './dashboard-types.js';
import { SIGNALS, parseSignal } from './signals.js';
import { initMCPClient, closeMCPClient, getMCPClient } from '../lib/mcp-client.js';
import { checkSystemSetup, clearAuth, getAuthToken, revokeToken, refreshAuthToken } from '../lib/auth.js';
import { useDashboardData } from '../hooks/useDashboardData.js';
import { useLoginFlow } from '../hooks/useLoginFlow.js';
import { useSetupFlow } from '../hooks/useSetupFlow.js';
import { useResetPasswordFlow } from '../hooks/useResetPasswordFlow.js';
import { useBackupFlow } from '../hooks/useBackupFlow.js';

import { AsciiHeader } from '../components/dashboard/AsciiHeader.js';
import { NavBar } from '../components/dashboard/NavBar.js';
import { CommandPrompt } from '../components/dashboard/CommandPrompt.js';
import { Footer } from '../components/dashboard/Footer.js';
import { ErrorBoundary } from '../components/dashboard/ErrorBoundary.js';

import { DashboardView } from './views/DashboardView.js';
import { AgentsView } from './views/AgentsView.js';
import { LogsView } from './views/LogsView.js';
import { SettingsView } from './views/SettingsView.js';
import { SetupView } from './views/SetupView.js';
import { DEFAULT_MCP_URL, CLI_VERSION } from '../lib/constants.js';
const REFRESH_INTERVAL = 30000;
const SESSION_TIMEOUT = 15 * 60 * 1000; // 15 minutes

interface AppProps {
  mcpUrl?: string;
}

export function App({ mcpUrl }: AppProps) {
  const { exit } = useApp();
  const { stdout } = useStdout();
  const terminalHeight = stdout?.rows || 24;

  const [state, setState] = useState<AppState>(() => ({
    ...initialAppState,
    mcpUrl: mcpUrl || initialAppState.mcpUrl,
  }));

  const [activeView, setActiveView] = useState<ViewMode>('dashboard');
  const [activityLog, setActivityLog] = useState<ActivityEntry[]>([]);

  const stateRef = useRef(state);
  stateRef.current = state;

  const lastActivityRef = useRef(Date.now());
  const forceLogoutFired = useRef(false);

  const addMessage = useCallback(
    (type: OutputMessage['type'], content: string) => {
      setState((prev) => ({
        ...prev,
        history: [...prev.history, createMessage(type, content)],
      }));
    },
    []
  );

  const addActivity = useCallback(
    (type: ActivityEntry['type'], message: string) => {
      setActivityLog((prev) => [...prev.slice(-99), createActivityEntry(type, message)]);
    },
    []
  );

  const setInputValue = useCallback((value: string) => {
    setState((prev) => ({ ...prev, inputValue: value }));
  }, []);

  const setRunning = useCallback((running: boolean) => {
    setState((prev) => ({ ...prev, isRunningCommand: running }));
  }, []);

  const onAuthenticated = useCallback((username: string) => {
    forceLogoutFired.current = false;
    setState((prev) => ({ ...prev, authenticated: true, username }));
  }, []);

  const loginFlow = useLoginFlow({
    addActivity,
    onAuthenticated,
    setInputValue,
    setRunning,
  });

  const setupFlow = useSetupFlow({
    addActivity,
    onAuthenticated,
    setInputValue,
    setRunning,
  });

  const resetPasswordFlow = useResetPasswordFlow({
    addActivity,
    setInputValue,
    setRunning,
  });

  const backupFlow = useBackupFlow({
    addActivity,
    setInputValue,
    setRunning,
  });

  const dashboardData = useDashboardData({
    refreshInterval: REFRESH_INTERVAL,
    enabled: state.mcpConnected,
  });

  // Auto-connect to MCP server on mount
  useEffect(() => {
    const url = mcpUrl || DEFAULT_MCP_URL;
    setState((prev) => ({ ...prev, mcpUrl: url, mcpConnecting: true }));

    (async () => {
      try {
        const client = await initMCPClient(url);
        client.setAuthTokenGetter(getAuthToken);
        client.setTokenRefresher(refreshAuthToken);
        client.setForceLogoutHandler(() => {
          if (forceLogoutFired.current) return;
          forceLogoutFired.current = true;
          clearAuth();
          setState((prev) => ({ ...prev, authenticated: false, username: null }));
          loginFlow.startLogin();
          addActivity('SYS', 'Session expired. Please log in again.');
        });
        setState((prev) => ({
          ...prev,
          mcpConnected: true,
          mcpConnecting: false,
          mcpError: null,
        }));
        addActivity('SYS', `Connected to ${url}`);

        try {
          const needsSetup = await checkSystemSetup();
          if (needsSetup) {
            setupFlow.startSetup();
            addActivity('SYS', 'System requires initial setup');
          } else {
            loginFlow.startLogin();
          }
        } catch {
          loginFlow.startLogin();
        }
      } catch (err) {
        const error = err instanceof Error ? err.message : 'Connection failed';
        setState((prev) => ({
          ...prev,
          mcpConnected: false,
          mcpConnecting: false,
          mcpError: error,
        }));
        addActivity('ERR', `Failed to connect: ${error}`);
      }
    })();

    return () => {
      closeMCPClient();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    addActivity('SYS', 'Welcome to Tomo CLI');
  }, [addActivity]);

  // Session inactivity timeout
  useEffect(() => {
    const interval = setInterval(() => {
      if (
        stateRef.current.authenticated &&
        !forceLogoutFired.current &&
        Date.now() - lastActivityRef.current > SESSION_TIMEOUT
      ) {
        forceLogoutFired.current = true;
        revokeToken().catch(() => {});
        setState((prev) => ({ ...prev, authenticated: false, username: null }));
        loginFlow.startLogin();
        addActivity('SYS', 'Session expired due to inactivity');
      }
    }, 30_000);
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleInputChange = useCallback((value: string) => {
    setState((prev) => ({ ...prev, inputValue: value }));
  }, []);

  const handleHistoryNavigate = useCallback((index: number) => {
    setState((prev) => ({ ...prev, historyIndex: index }));
  }, []);

  const handleSubmit = useCallback(
    async (input: string) => {
      lastActivityRef.current = Date.now();
      addActivity('CMD', input);

      setState((prev) => {
        const newHistory =
          prev.commandHistory[prev.commandHistory.length - 1] === input
            ? prev.commandHistory
            : [...prev.commandHistory, input];

        return {
          ...prev,
          inputValue: '',
          commandHistory: newHistory.slice(-100),
          historyIndex: -1,
          isRunningCommand: true,
        };
      });

      try {
        const results = await routeCommand(input, stateRef.current);

        for (const result of results) {
          if (result.content === SIGNALS.CLEAR) {
            setState((prev) => ({ ...prev, history: [] }));
            addActivity('OK', 'Screen cleared');
            continue;
          }

          if (result.content === SIGNALS.LOGOUT) {
            await revokeToken();
            setState((prev) => ({ ...prev, authenticated: false, username: null }));
            loginFlow.startLogin();
            addActivity('SYS', 'Logged out');
            continue;
          }

          if (result.content === SIGNALS.LOGIN) {
            loginFlow.startLogin();
            addActivity('SYS', 'Enter credentials to authenticate');
            continue;
          }

          if (result.content === SIGNALS.REFRESH) {
            dashboardData.refresh();
            addActivity('OK', 'Data refreshed');
            continue;
          }

          if (result.content === SIGNALS.SETUP) {
            setupFlow.startSetup();
            addActivity('SYS', 'Starting admin setup');
            continue;
          }

          const resetUsername = parseSignal(result.content, SIGNALS.RESET_PASSWORD);
          if (resetUsername !== null) {
            resetPasswordFlow.startReset(resetUsername);
            addActivity('SYS', `Resetting password for ${resetUsername}`);
            continue;
          }

          const exportPath = parseSignal(result.content, SIGNALS.BACKUP_EXPORT);
          if (exportPath !== null) {
            backupFlow.startExport(exportPath);
            addActivity('SYS', `Exporting backup to ${exportPath}`);
            continue;
          }

          const overwritePath = parseSignal(result.content, SIGNALS.BACKUP_IMPORT_OVERWRITE);
          if (overwritePath !== null) {
            backupFlow.startImport(overwritePath, true);
            addActivity('SYS', `Importing backup from ${overwritePath} (overwrite)`);
            continue;
          }

          const importPath = parseSignal(result.content, SIGNALS.BACKUP_IMPORT);
          if (importPath !== null) {
            backupFlow.startImport(importPath, false);
            addActivity('SYS', `Importing backup from ${importPath}`);
            continue;
          }

          const viewTarget = parseSignal(result.content, SIGNALS.VIEW);
          const validViews: ViewMode[] = ['dashboard', 'agents', 'logs', 'settings'];
          if (viewTarget !== null && validViews.includes(viewTarget as ViewMode)) {
            setActiveView(viewTarget as ViewMode);
            addActivity('OK', `Switched to ${viewTarget} view`);
            continue;
          }

          addMessage(result.type, result.content);

          const activityType: ActivityEntry['type'] =
            result.type === 'error' ? 'ERR'
            : result.type === 'success' ? 'OK'
            : result.type === 'system' ? 'SYS'
            : 'SYS';
          if (result.content) {
            addActivity(activityType, result.content);
          }

          if (result.exit) {
            setTimeout(() => exit(), 100);
            return;
          }
        }
      } catch (err) {
        const msg = err instanceof Error ? err.message : 'Command failed';
        addMessage('error', msg);
        addActivity('ERR', msg);
      } finally {
        setState((prev) => ({ ...prev, isRunningCommand: false }));
      }
    },
    [addMessage, addActivity, exit, dashboardData, loginFlow, setupFlow, resetPasswordFlow, backupFlow]
  );

  useInput((input, key) => {
    if (key.ctrl && input === 'l') {
      setState((prev) => ({ ...prev, history: [] }));
      return;
    }

    if (key.tab && !key.ctrl && !key.meta) {
      const views: ViewMode[] = ['dashboard', 'agents', 'logs', 'settings'];
      const currentIndex = views.indexOf(activeView);
      const next = key.shift
        ? (currentIndex - 1 + views.length) % views.length
        : (currentIndex + 1) % views.length;
      setActiveView(views[next]!);
    }
  });

  const activityLogEntries: ActivityEntry[] = activityLog;

  const connectionStatus = state.mcpConnected
    ? 'connected' as const
    : state.mcpConnecting
      ? 'connecting' as const
      : 'disconnected' as const;

  const renderView = () => {
    switch (activeView) {
      case 'dashboard':
        return (
          <DashboardView
            data={dashboardData}
            activityLog={activityLogEntries}
            mcpConnected={state.mcpConnected}
          />
        );
      case 'agents':
        return <AgentsView agents={dashboardData.agents} />;
      case 'logs':
        return <LogsView entries={activityLogEntries} />;
      case 'settings':
        return (
          <SettingsView
            mcpUrl={state.mcpUrl}
            refreshInterval={REFRESH_INTERVAL}
            autoRefresh={true}
            version={CLI_VERSION}
          />
        );
    }
  };

  const promptHandler = setupFlow.isActive
    ? setupFlow.handleSubmit
    : resetPasswordFlow.isActive
      ? resetPasswordFlow.handleSubmit
      : backupFlow.isActive
        ? backupFlow.handleSubmit
        : loginFlow.isActive
          ? loginFlow.handleSubmit
          : handleSubmit;

  const promptLabel = setupFlow.promptLabel
    || resetPasswordFlow.promptLabel
    || backupFlow.promptLabel
    || loginFlow.promptLabel;

  const promptMask = setupFlow.promptMask
    || resetPasswordFlow.promptMask
    || backupFlow.promptMask
    || loginFlow.promptMask;

  const isOffline = !state.mcpConnected && !state.mcpConnecting;

  return (
    <Box flexDirection="column" minHeight={terminalHeight}>
      <Footer
        version={CLI_VERSION}
        mcpUrl={state.mcpUrl}
        connectionStatus={connectionStatus}
      />

      <AsciiHeader />

      <ErrorBoundary fallbackMessage="View rendering failed">
        {setupFlow.isActive ? (
          <Box flexDirection="column" flexGrow={1}>
            <SetupView
              step={setupFlow.setupStep!}
              username={setupFlow.setupUsername}
              error={setupFlow.setupError}
            />
          </Box>
        ) : (
          <Box flexDirection="column" flexGrow={1}>
            {renderView()}
          </Box>
        )}
      </ErrorBoundary>

      <Box paddingX={1} marginTop={1}>
        <CommandPrompt
          username={state.username || 'admin'}
          value={state.inputValue}
          onChange={handleInputChange}
          onSubmit={promptHandler}
          commandHistory={state.commandHistory}
          historyIndex={state.historyIndex}
          onHistoryNavigate={handleHistoryNavigate}
          disabled={state.isRunningCommand || setupFlow.isDisabled}
          promptLabel={promptLabel}
          mask={promptMask}
          offline={isOffline}
        />
      </Box>

      {!setupFlow.isActive ? (
        <NavBar
          items={[...NAV_ITEMS]}
          activeTab={activeView}
        />
      ) : null}
    </Box>
  );
}
