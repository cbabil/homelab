/**
 * Command Router for the interactive CLI
 *
 * Parses user input and routes to appropriate command handlers.
 * All commands are slash commands (e.g., /help, /agent list).
 */

import type { AppState, CommandResult } from './types.js';
import { VALID_VIEWS } from './dashboard-types.js';
import { SIGNALS } from './signals.js';
import { getMCPClient } from '../lib/mcp-client.js';
import { handleAgentCommand } from './handlers/agent-handlers.js';
import { handleServerCommand } from './handlers/server-handlers.js';
import { handleUpdateCommand } from './handlers/update-handlers.js';
import { handleSecurityCommand } from './handlers/security-handlers.js';
import { handleBackupCommand } from './handlers/backup-handlers.js';
import { handleUserCommand } from './handlers/user-handlers.js';
import { getHelpText } from './handlers/help-handler.js';
import { sanitizeForDisplay } from '../lib/validation.js';

/**
 * Guard for commands that require authentication.
 * Returns error results if not connected or not authenticated, null otherwise.
 */
function requireAuth(state: AppState): CommandResult[] | null {
  if (!state.mcpConnected) {
    return [{ type: 'error', content: 'Not connected to MCP server' }];
  }
  if (!state.authenticated) {
    return [{ type: 'error', content: 'Authentication required. Use /login first.' }];
  }
  return null;
}

interface SlashCommand {
  name: string;
  aliases: string[];
  description: string;
  handler: (args: string[], state: AppState) => Promise<CommandResult[]>;
}

const slashCommands: SlashCommand[] = [
  {
    name: 'help',
    aliases: ['h', '?'],
    description: 'Show available commands',
    handler: async () => getHelpText(),
  },
  {
    name: 'clear',
    aliases: ['cls'],
    description: 'Clear output history',
    handler: async () => [{ type: 'system', content: SIGNALS.CLEAR }],
  },
  {
    name: 'quit',
    aliases: ['exit', 'q'],
    description: 'Exit the CLI',
    handler: async () => [{ type: 'system', content: 'Goodbye!', exit: true }],
  },
  {
    name: 'status',
    aliases: [],
    description: 'Show connection status',
    handler: async (_args, state) => [
      { type: 'info', content: 'Connection Status:' },
      {
        type: state.mcpConnected ? 'success' : 'error',
        content: `  MCP: ${state.mcpConnected ? 'Connected' : 'Disconnected'}`,
      },
      { type: 'info', content: `  URL: ${state.mcpUrl}` },
      {
        type: state.authenticated ? 'success' : 'info',
        content: `  Auth: ${state.authenticated ? `Authenticated as ${state.username}` : 'Not authenticated'}`,
      },
    ],
  },
  {
    name: 'servers',
    aliases: [],
    description: 'List all servers',
    handler: async (_args, state) => {
      const authError = requireAuth(state);
      if (authError) return authError;
      const client = getMCPClient();
      return handleServerCommand(client, 'list', []);
    },
  },
  {
    name: 'agents',
    aliases: [],
    description: 'List all agents',
    handler: async (_args, state) => {
      const authError = requireAuth(state);
      if (authError) return authError;
      const client = getMCPClient();
      return handleAgentCommand(client, 'list', []);
    },
  },
  {
    name: 'login',
    aliases: [],
    description: 'Authenticate as admin',
    handler: async () => [{ type: 'system', content: SIGNALS.LOGIN }],
  },
  {
    name: 'logout',
    aliases: [],
    description: 'Clear authentication',
    handler: async () => [
      { type: 'system', content: SIGNALS.LOGOUT },
      { type: 'success', content: 'Logged out successfully' },
    ],
  },
  {
    name: 'view',
    aliases: [],
    description: 'Switch dashboard view',
    handler: async (args) => {
      const target = args[0]?.toLowerCase();

      if (!target || !VALID_VIEWS.includes(target as never)) {
        return [
          { type: 'error', content: `Usage: /view <${VALID_VIEWS.join('|')}>` },
        ];
      }

      return [{ type: 'system', content: `${SIGNALS.VIEW}${target}` }];
    },
  },
  {
    name: 'refresh',
    aliases: [],
    description: 'Force data refresh',
    handler: async () => [{ type: 'system', content: SIGNALS.REFRESH }],
  },
  {
    name: 'agent',
    aliases: [],
    description: 'Agent management',
    handler: async (args, state) => {
      const authError = requireAuth(state);
      if (authError) return authError;
      const client = getMCPClient();
      const subcommand = args[0]?.toLowerCase() ?? '';
      const subArgs = args.slice(1);
      return handleAgentCommand(client, subcommand, subArgs);
    },
  },
  {
    name: 'server',
    aliases: [],
    description: 'Server management',
    handler: async (args, state) => {
      const authError = requireAuth(state);
      if (authError) return authError;
      const client = getMCPClient();
      const subcommand = args[0]?.toLowerCase() ?? '';
      const subArgs = args.slice(1);
      return handleServerCommand(client, subcommand, subArgs);
    },
  },
  {
    name: 'update',
    aliases: [],
    description: 'Check for updates',
    handler: async (_args, state) => {
      const authError = requireAuth(state);
      if (authError) return authError;
      const client = getMCPClient();
      return handleUpdateCommand(client);
    },
  },
  {
    name: 'security',
    aliases: [],
    description: 'Security management',
    handler: async (args, state) => {
      const authError = requireAuth(state);
      if (authError) return authError;
      const subcommand = args[0]?.toLowerCase() ?? '';
      const subArgs = args.slice(1);
      return handleSecurityCommand(subcommand, subArgs, state);
    },
  },
  {
    name: 'backup',
    aliases: [],
    description: 'Backup and restore',
    handler: async (args, state) => {
      const authError = requireAuth(state);
      if (authError) return authError;
      const subcommand = args[0]?.toLowerCase() ?? '';
      const subArgs = args.slice(1);
      return handleBackupCommand(subcommand, subArgs);
    },
  },
  {
    name: 'user',
    aliases: [],
    description: 'User management',
    handler: async (args, state) => {
      const authError = requireAuth(state);
      if (authError) return authError;
      const subcommand = args[0]?.toLowerCase() ?? '';
      const subArgs = args.slice(1);
      return handleUserCommand(subcommand, subArgs);
    },
  },
  {
    name: 'admin',
    aliases: [],
    description: 'Admin management',
    handler: async (args) => {
      const subcommand = args[0]?.toLowerCase() ?? '';

      if (subcommand === 'create') {
        return [{ type: 'system', content: SIGNALS.SETUP }];
      }

      return [
        {
          type: 'error',
          content: subcommand
            ? `Unknown admin subcommand: ${sanitizeForDisplay(subcommand)}`
            : 'Usage: /admin <create>',
        },
      ];
    },
  },
];

export async function routeCommand(
  input: string,
  state: AppState
): Promise<CommandResult[]> {
  const trimmed = input.trim();

  if (!trimmed) {
    return [];
  }

  // Check for slash commands
  if (trimmed.startsWith('/')) {
    const parts = trimmed.slice(1).split(/\s+/);
    const cmdName = parts[0]?.toLowerCase() ?? '';
    const args = parts.slice(1);

    for (const cmd of slashCommands) {
      if (cmd.name === cmdName || cmd.aliases.includes(cmdName)) {
        return cmd.handler(args, state);
      }
    }

    return [
      { type: 'error', content: `Unknown command: /${sanitizeForDisplay(cmdName)}` },
      { type: 'info', content: 'Type /help for available commands' },
    ];
  }

  // No regular commands — all commands must use / prefix
  return [
    { type: 'error', content: `Unknown input: ${sanitizeForDisplay(trimmed)}` },
    { type: 'info', content: 'Type /help for available commands' },
  ];
}
