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
import { t } from '../i18n/index.js';

/**
 * Guard for commands that require authentication.
 * Returns error results if not connected or not authenticated, null otherwise.
 */
function requireAuth(state: AppState): CommandResult[] | null {
  if (!state.mcpConnected) {
    return [{ type: 'error', content: t('auth.notConnected') }];
  }
  if (!state.authenticated) {
    return [{ type: 'error', content: t('auth.authRequired') }];
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
    description: t('commands.help.description'),
    handler: async () => getHelpText(),
  },
  {
    name: 'clear',
    aliases: ['cls'],
    description: t('commands.clear.description'),
    handler: async () => [{ type: 'system', content: SIGNALS.CLEAR }],
  },
  {
    name: 'quit',
    aliases: ['exit', 'q'],
    description: t('commands.quit.description'),
    handler: async () => [{ type: 'system', content: t('common.goodbye'), exit: true }],
  },
  {
    name: 'status',
    aliases: [],
    description: t('commands.status.description'),
    handler: async (_args, state) => [
      { type: 'info', content: t('commands.status.title') },
      {
        type: state.mcpConnected ? 'success' : 'error',
        content: state.mcpConnected ? t('commands.status.mcpConnected') : t('commands.status.mcpDisconnected'),
      },
      { type: 'info', content: t('commands.status.urlPrefix', { url: state.mcpUrl }) },
      {
        type: state.authenticated ? 'success' : 'info',
        content: state.authenticated
          ? t('commands.status.authenticated', { username: state.username })
          : t('commands.status.notAuthenticated'),
      },
    ],
  },
  {
    name: 'servers',
    aliases: [],
    description: t('commands.servers.description'),
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
    description: t('commands.agents.description'),
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
    description: t('commands.login.description'),
    handler: async () => [{ type: 'system', content: SIGNALS.LOGIN }],
  },
  {
    name: 'logout',
    aliases: [],
    description: t('commands.logout.description'),
    handler: async () => [
      { type: 'system', content: SIGNALS.LOGOUT },
      { type: 'success', content: t('commands.logout.success') },
    ],
  },
  {
    name: 'view',
    aliases: [],
    description: t('commands.view.description'),
    handler: async (args) => {
      const target = args[0]?.toLowerCase();

      if (!target || !VALID_VIEWS.includes(target as never)) {
        return [
          { type: 'error', content: t('commands.view.usage', { views: VALID_VIEWS.join('|') }) },
        ];
      }

      return [{ type: 'system', content: `${SIGNALS.VIEW}${target}` }];
    },
  },
  {
    name: 'refresh',
    aliases: [],
    description: t('commands.refresh.description'),
    handler: async () => [{ type: 'system', content: SIGNALS.REFRESH }],
  },
  {
    name: 'agent',
    aliases: [],
    description: t('commands.agent.description'),
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
    description: t('commands.server.description'),
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
    description: t('commands.update.description'),
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
    description: t('commands.security.description'),
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
    description: t('commands.backup.description'),
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
    description: t('commands.user.description'),
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
    description: t('commands.admin.description'),
    handler: async (args) => {
      const subcommand = args[0]?.toLowerCase() ?? '';

      if (subcommand === 'create') {
        return [{ type: 'system', content: SIGNALS.SETUP }];
      }

      return [
        {
          type: 'error',
          content: subcommand
            ? t('commands.admin.unknownSubcommand', { subcommand: sanitizeForDisplay(subcommand) })
            : t('commands.admin.usage'),
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
      { type: 'error', content: t('commands.unknownCommand', { command: sanitizeForDisplay(cmdName) }) },
      { type: 'info', content: t('common.typeHelpForCommands') },
    ];
  }

  // No regular commands — all commands must use / prefix
  return [
    { type: 'error', content: t('commands.unknownInput', { input: sanitizeForDisplay(trimmed) }) },
    { type: 'info', content: t('common.typeHelpForCommands') },
  ];
}
