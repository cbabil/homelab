/**
 * Shared types for the interactive CLI
 */

export type MessageType = 'info' | 'success' | 'error' | 'command' | 'system';

export interface OutputMessage {
  id: string;
  timestamp: Date;
  type: MessageType;
  content: string;
}

export interface AppState {
  // Connection
  mcpConnected: boolean;
  mcpUrl: string;
  mcpConnecting: boolean;
  mcpError: string | null;

  // Auth
  authenticated: boolean;
  username: string | null;

  // UI
  history: OutputMessage[];
  inputValue: string;
  commandHistory: string[];
  historyIndex: number;

  // App state
  isRunningCommand: boolean;
}

export interface CommandResult {
  type: MessageType;
  content: string;
  exit?: boolean;
}

export interface CommandHandler {
  name: string;
  description: string;
  execute: (args: string[], state: AppState) => Promise<CommandResult[]>;
}

export const initialAppState: AppState = {
  mcpConnected: false,
  mcpUrl: process.env.MCP_SERVER_URL || 'http://localhost:8000/mcp',
  mcpConnecting: true,
  mcpError: null,
  authenticated: false,
  username: null,
  history: [],
  inputValue: '',
  commandHistory: [],
  historyIndex: -1,
  isRunningCommand: false,
};

export function createMessage(
  type: MessageType,
  content: string
): OutputMessage {
  return {
    id: `msg-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`,
    timestamp: new Date(),
    type,
    content,
  };
}
