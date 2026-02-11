/**
 * Help command handler for the interactive CLI
 */

import type { CommandResult } from '../types.js';
import { t } from '../../i18n/index.js';

export function getHelpText(): CommandResult[] {
  return [
    {
      type: 'info',
      content: t('commands.help.title'),
    },
    {
      type: 'system',
      content: t('commands.help.helpLine'),
    },
    {
      type: 'system',
      content: t('commands.help.clearLine'),
    },
    {
      type: 'system',
      content: t('commands.help.quitLine'),
    },
    {
      type: 'system',
      content: t('commands.help.statusLine'),
    },
    {
      type: 'system',
      content: t('commands.help.serversLine'),
    },
    {
      type: 'system',
      content: t('commands.help.agentsLine'),
    },
    {
      type: 'system',
      content: t('commands.help.loginLine'),
    },
    {
      type: 'system',
      content: t('commands.help.logoutLine'),
    },
    {
      type: 'system',
      content: t('commands.help.viewLine'),
    },
    {
      type: 'system',
      content: t('commands.help.refreshLine'),
    },
    {
      type: 'info',
      content: '',
    },
    {
      type: 'info',
      content: t('commands.help.managementTitle'),
    },
    {
      type: 'system',
      content: t('commands.help.agentMgmtLine'),
    },
    {
      type: 'system',
      content: t('commands.help.serverMgmtLine'),
    },
    {
      type: 'system',
      content: t('commands.help.updateLine'),
    },
    {
      type: 'system',
      content: t('commands.help.securityLine'),
    },
    {
      type: 'system',
      content: t('commands.help.backupLine'),
    },
    {
      type: 'system',
      content: t('commands.help.userLine'),
    },
    {
      type: 'system',
      content: t('commands.help.adminLine'),
    },
  ];
}
