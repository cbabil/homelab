/**
 * Help command handler for the interactive CLI
 */

import type { CommandResult } from '../types.js';

export function getHelpText(): CommandResult[] {
  return [
    {
      type: 'info',
      content: 'Available Commands:',
    },
    {
      type: 'system',
      content: '  /help, /h, /?          - Show this help message',
    },
    {
      type: 'system',
      content: '  /clear, /cls           - Clear output history',
    },
    {
      type: 'system',
      content: '  /quit, /exit, /q       - Exit the CLI',
    },
    {
      type: 'system',
      content: '  /status                - Show connection status',
    },
    {
      type: 'system',
      content: '  /servers               - List all servers',
    },
    {
      type: 'system',
      content: '  /agents                - List all agents',
    },
    {
      type: 'system',
      content: '  /login                 - Authenticate as admin',
    },
    {
      type: 'system',
      content: '  /logout                - Clear authentication',
    },
    {
      type: 'system',
      content: '  /view <tab>            - Switch view (dashboard|agents|logs|settings)',
    },
    {
      type: 'system',
      content: '  /refresh               - Force data refresh',
    },
    {
      type: 'info',
      content: '',
    },
    {
      type: 'info',
      content: 'Management Commands:',
    },
    {
      type: 'system',
      content: '  /agent <sub> [args]    - Agent management (list|status|ping|rotate|install)',
    },
    {
      type: 'system',
      content: '  /server <sub>          - Server management (list)',
    },
    {
      type: 'system',
      content: '  /update                - Check for updates',
    },
    {
      type: 'system',
      content: '  /security <sub> [args] - Security (list-locked|unlock)',
    },
    {
      type: 'system',
      content: '  /backup <sub> [args]   - Backup (export|import)',
    },
    {
      type: 'system',
      content: '  /user <sub> <args>     - User management (reset-password)',
    },
    {
      type: 'system',
      content: '  /admin create          - Initial admin setup',
    },
  ];
}
