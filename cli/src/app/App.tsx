import { Box, Text, useApp, useInput } from 'ink';
import React, { useState, useCallback, useEffect } from 'react';

import { OutputHistory } from './OutputHistory.js';
import { InputArea } from './InputArea.js';
import { StatusBar } from './StatusBar.js';
import { routeCommand } from './CommandRouter.js';
import { createMessage, initialAppState } from './types.js';
import type { AppState, OutputMessage } from './types.js';
import { initMCPClient, closeMCPClient } from '../lib/mcp-client.js';

interface AppProps {
  mcpUrl?: string;
}

export function App({ mcpUrl }: AppProps) {
  const { exit } = useApp();

  const [state, setState] = useState<AppState>(() => ({
    ...initialAppState,
    mcpUrl: mcpUrl || initialAppState.mcpUrl,
  }));

  // Initialize MCP connection
  useEffect(() => {
    const connect = async () => {
      try {
        await initMCPClient(state.mcpUrl);
        setState((prev) => ({
          ...prev,
          mcpConnected: true,
          mcpConnecting: false,
          mcpError: null,
        }));
        addMessage('system', 'Connected to MCP server');
      } catch (err) {
        const error = err instanceof Error ? err.message : 'Connection failed';
        setState((prev) => ({
          ...prev,
          mcpConnected: false,
          mcpConnecting: false,
          mcpError: error,
        }));
        addMessage('error', `Failed to connect: ${error}`);
      }
    };

    connect();

    return () => {
      closeMCPClient();
    };
  }, [state.mcpUrl]);

  // Add welcome message on mount
  useEffect(() => {
    addMessage('info', 'Welcome to Tomo CLI');
    addMessage('system', 'Type /help for available commands, /quit to exit');
  }, []);

  const addMessage = useCallback(
    (type: OutputMessage['type'], content: string) => {
      setState((prev) => ({
        ...prev,
        history: [...prev.history, createMessage(type, content)],
      }));
    },
    []
  );

  const handleInputChange = useCallback((value: string) => {
    setState((prev) => ({ ...prev, inputValue: value }));
  }, []);

  const handleHistoryNavigate = useCallback((index: number) => {
    setState((prev) => ({ ...prev, historyIndex: index }));
  }, []);

  const handleSubmit = useCallback(
    async (input: string) => {
      // Add command to history
      addMessage('command', input);

      // Add to command history (avoid duplicates)
      setState((prev) => {
        const newHistory =
          prev.commandHistory[prev.commandHistory.length - 1] === input
            ? prev.commandHistory
            : [...prev.commandHistory, input];

        return {
          ...prev,
          inputValue: '',
          commandHistory: newHistory.slice(-100), // Keep last 100 commands
          historyIndex: -1,
          isRunningCommand: true,
        };
      });

      try {
        const results = await routeCommand(input, state);

        for (const result of results) {
          // Handle special commands
          if (result.content === '__CLEAR__') {
            setState((prev) => ({ ...prev, history: [] }));
            continue;
          }

          if (result.content === '__LOGOUT__') {
            setState((prev) => ({
              ...prev,
              authenticated: false,
              username: null,
            }));
            continue;
          }

          addMessage(result.type, result.content);

          if (result.exit) {
            setTimeout(() => exit(), 100);
            return;
          }
        }
      } catch (err) {
        addMessage(
          'error',
          err instanceof Error ? err.message : 'Command failed'
        );
      } finally {
        setState((prev) => ({ ...prev, isRunningCommand: false }));
      }
    },
    [state, addMessage, exit]
  );

  // Handle global keyboard shortcuts
  useInput((input, key) => {
    if (key.ctrl && input === 'l') {
      // Ctrl+L - Clear screen
      setState((prev) => ({ ...prev, history: [] }));
    }
  });

  return (
    <Box flexDirection="column" height={24}>
      {/* Header */}
      <Box
        borderStyle="double"
        borderColor="cyan"
        paddingX={1}
        justifyContent="center"
      >
        <Text bold color="cyan">
          Tomo - Admin CLI
        </Text>
      </Box>

      {/* Output history area */}
      <Box flexDirection="column" flexGrow={1} paddingX={1}>
        <OutputHistory messages={state.history} height={15} />
      </Box>

      {/* Status bar */}
      <StatusBar
        mcpConnected={state.mcpConnected}
        mcpConnecting={state.mcpConnecting}
        mcpError={state.mcpError}
        authenticated={state.authenticated}
        username={state.username}
        isRunningCommand={state.isRunningCommand}
      />

      {/* Input area */}
      <Box paddingX={1} marginTop={1}>
        <InputArea
          value={state.inputValue}
          onChange={handleInputChange}
          onSubmit={handleSubmit}
          commandHistory={state.commandHistory}
          historyIndex={state.historyIndex}
          onHistoryNavigate={handleHistoryNavigate}
          disabled={state.isRunningCommand}
        />
      </Box>
    </Box>
  );
}
