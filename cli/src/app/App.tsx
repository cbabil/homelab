import { Box, useApp, useInput, useStdout } from 'ink';
import React, { useState, useCallback, useEffect, useRef } from 'react';

import { routeCommand } from './CommandRouter.js';
import { createMessage, initialAppState } from './types.js';
import type { AppState, OutputMessage } from './types.js';
import type { ActivityEntry, ViewMode } from './dashboard-types.js';
import { createActivityEntry, NAV_ITEMS } from './dashboard-types.js';
import { classifySignal } from './signal-processor.js';
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

  const exitRef = useRef(exit);
  exitRef.current = exit;

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

  // Refs for flow objects so useCallback/useEffect have stable references
  const loginFlowRef = useRef(loginFlow);
  loginFlowRef.current = loginFlow;

  const setupFlowRef = useRef(setupFlow);
  setupFlowRef.current = setupFlow;

  const resetPasswordFlowRef = useRef(resetPasswordFlow);
  resetPasswordFlowRef.current = resetPasswordFlow;

  const backupFlowRef = useRef(backupFlow);
  backupFlowRef.current = backupFlow;

  const dashboardDataRef = useRef(dashboardData);
  dashboardDataRef.current = dashboardData;

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
          loginFlowRef.current.startLogin();
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
            setupFlowRef.current.startSetup();
            addActivity('SYS', 'System requires initial setup');
          } else {
            loginFlowRef.current.startLogin();
          }
        } catch {
          loginFlowRef.current.startLogin();
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
  }, [addActivity]);

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
        loginFlowRef.current.startLogin();
        addActivity('SYS', 'Session expired due to inactivity');
      }
    }, 30_000);
    return () => clearInterval(interval);
  }, [addActivity]);

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
          const action = classifySignal(result);

          switch (action.kind) {
            case 'clear':
              setState((prev) => ({ ...prev, history: [] }));
              addActivity('OK', 'Screen cleared');
              break;
            case 'logout':
              await revokeToken();
              setState((prev) => ({ ...prev, authenticated: false, username: null }));
              loginFlowRef.current.startLogin();
              addActivity('SYS', 'Logged out');
              break;
            case 'login':
              loginFlowRef.current.startLogin();
              addActivity('SYS', 'Enter credentials to authenticate');
              break;
            case 'refresh':
              dashboardDataRef.current.refresh();
              addActivity('OK', 'Data refreshed');
              break;
            case 'setup':
              setupFlowRef.current.startSetup();
              addActivity('SYS', 'Starting admin setup');
              break;
            case 'reset_password':
              resetPasswordFlowRef.current.startReset(action.username);
              addActivity('SYS', `Resetting password for ${action.username}`);
              break;
            case 'backup_export':
              backupFlowRef.current.startExport(action.path);
              addActivity('SYS', `Exporting backup to ${action.path}`);
              break;
            case 'backup_import':
              backupFlowRef.current.startImport(action.path, action.overwrite);
              addActivity('SYS', `Importing backup from ${action.path}${action.overwrite ? ' (overwrite)' : ''}`);
              break;
            case 'view':
              setActiveView(action.target);
              addActivity('OK', `Switched to ${action.target} view`);
              break;
            case 'message': {
              addMessage(action.result.type, action.result.content);
              const activityType: ActivityEntry['type'] =
                action.result.type === 'error' ? 'ERR'
                : action.result.type === 'success' ? 'OK'
                : 'SYS';
              if (action.result.content) {
                addActivity(activityType, action.result.content);
              }
              if (action.result.exit) {
                setTimeout(() => exitRef.current(), 100);
                return;
              }
              break;
            }
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
    [addMessage, addActivity]
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
            activityLog={activityLog}
            mcpConnected={state.mcpConnected}
          />
        );
      case 'agents':
        return <AgentsView agents={dashboardData.agents} />;
      case 'logs':
        return <LogsView entries={activityLog} />;
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
          items={NAV_ITEMS}
          activeTab={activeView}
        />
      ) : null}
    </Box>
  );
}
