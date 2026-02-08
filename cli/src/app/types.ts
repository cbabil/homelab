/**
 * Shared types for the interactive CLI
 */

import { DEFAULT_MCP_URL } from '../lib/constants.js';

export type MessageType = 'info' | 'success' | 'error' | 'system';

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

export const initialAppState: AppState = {
  mcpConnected: false,
  mcpUrl: DEFAULT_MCP_URL,
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

let messageCounter = 0;

export function resetMessageCounter(): void {
  messageCounter = 0;
}

export function createMessage(
  type: MessageType,
  content: string
): OutputMessage {
  return {
    id: `msg-${Date.now()}-${++messageCounter}`,
    timestamp: new Date(),
    type,
    content,
  };
}
