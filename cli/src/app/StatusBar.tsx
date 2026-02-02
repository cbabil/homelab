import { Box, Text } from 'ink';
import React from 'react';

interface StatusBarProps {
  mcpConnected: boolean;
  mcpConnecting: boolean;
  mcpError: string | null;
  authenticated: boolean;
  username: string | null;
  isRunningCommand: boolean;
}

export function StatusBar({
  mcpConnected,
  mcpConnecting,
  mcpError,
  authenticated,
  username,
  isRunningCommand,
}: StatusBarProps) {
  // Connection status
  let connectionStatus: React.ReactNode;
  if (mcpError) {
    connectionStatus = (
      <Text color="red">Disconnected ({mcpError})</Text>
    );
  } else if (mcpConnecting) {
    connectionStatus = <Text color="yellow">Connecting...</Text>;
  } else if (mcpConnected) {
    connectionStatus = <Text color="green">Connected</Text>;
  } else {
    connectionStatus = <Text color="red">Disconnected</Text>;
  }

  // Auth status
  let authStatus: React.ReactNode;
  if (authenticated && username) {
    authStatus = (
      <Text>
        User: <Text color="cyan">{username}</Text>
      </Text>
    );
  } else {
    authStatus = <Text color="yellow">Not authenticated</Text>;
  }

  // Command status
  const commandStatus = isRunningCommand ? (
    <Text color="yellow"> [Running...]</Text>
  ) : null;

  return (
    <Box
      borderStyle="single"
      borderColor="gray"
      paddingX={1}
      justifyContent="space-between"
    >
      <Box gap={2}>
        <Text>
          MCP: {connectionStatus}
        </Text>
        <Text color="gray">|</Text>
        {authStatus}
        {commandStatus}
      </Box>
      <Text color="gray">/help | /quit | Ctrl+C cancel</Text>
    </Box>
  );
}
