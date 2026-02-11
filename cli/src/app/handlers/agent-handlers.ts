/**
 * Agent command handlers for the interactive CLI
 */

import type { CommandResult } from '../types.js';
import type { MCPClient } from '../../lib/mcp-client.js';
import type { AgentInfo, RotateTokenData } from '../../lib/agent.js';
import { installAgent } from '../../lib/agent.js';
import { sanitizeForDisplay } from '../../lib/validation.js';
import { t } from '../../i18n/index.js';

export async function handleAgentCommand(
  client: MCPClient,
  subcommand: string,
  args: string[]
): Promise<CommandResult[]> {
  switch (subcommand) {
    case 'list':
      return executeAgentList(client);

    case 'status':
      if (!args[0]) {
        return [{ type: 'error', content: t('agents.usageStatus') }];
      }
      return executeAgentStatus(client, args[0]);

    case 'ping':
      if (!args[0]) {
        return [{ type: 'error', content: t('agents.usagePing') }];
      }
      return executeAgentPing(client, args[0]);

    case 'rotate':
      if (!args[0]) {
        return [{ type: 'error', content: t('agents.usageRotate') }];
      }
      return executeAgentRotate(client, args[0]);

    case 'install':
      if (!args[0]) {
        return [{ type: 'error', content: t('agents.usageInstall') }];
      }
      return executeAgentInstall(args[0]);

    default:
      return [
        {
          type: 'error',
          content: subcommand
            ? t('commands.agent.unknownSubcommand', { subcommand: sanitizeForDisplay(subcommand) })
            : t('commands.agent.usage'),
        },
      ];
  }
}

async function executeAgentList(
  client: MCPClient
): Promise<CommandResult[]> {
  try {
    const response = await client.callTool<{ agents: AgentInfo[] }>('list_agents', {});

    if (!response.success) {
      return [{ type: 'error', content: response.error || t('agents.failedToList') }];
    }

    const agents = response.data?.agents || [];

    if (agents.length === 0) {
      return [{ type: 'info', content: t('agents.noAgentsFound') }];
    }

    const results: CommandResult[] = [
      { type: 'info', content: t('agents.foundAgents', { count: agents.length }) },
    ];

    for (const agent of agents) {
      results.push({
        type: agent.status === 'connected' ? 'success' : 'info',
        content: t('agents.agentEntry', { id: agent.id, serverId: agent.server_id, status: agent.status.toUpperCase() }),
      });
      if (agent.version) {
        results.push({
          type: 'system',
          content: t('agents.versionLabel', { version: agent.version }),
        });
      }
    }

    return results;
  } catch (err) {
    return [
      {
        type: 'error',
        content: err instanceof Error ? err.message : t('agents.failedToList'),
      },
    ];
  }
}

async function executeAgentStatus(
  client: MCPClient,
  serverId: string
): Promise<CommandResult[]> {
  try {
    const response = await client.callTool<AgentInfo>('get_agent_status', {
      server_id: serverId,
    });

    if (!response.success) {
      return [{ type: 'error', content: response.error || t('agents.failedToGetStatus') }];
    }

    const agent = response.data;
    if (!agent) {
      return [{ type: 'error', content: t('agents.agentNotFound') }];
    }

    return [
      { type: 'info', content: t('agents.statusTitle', { serverId }) },
      {
        type: agent.status === 'connected' ? 'success' : 'info',
        content: t('agents.statusLabel', { status: agent.status }),
      },
      { type: 'info', content: t('agents.versionInfo', { version: agent.version || t('common.unknown') }) },
      { type: 'info', content: t('agents.lastSeen', { lastSeen: agent.last_seen || t('common.never') }) },
    ];
  } catch (err) {
    return [
      {
        type: 'error',
        content: err instanceof Error ? err.message : t('agents.failedToGetStatus'),
      },
    ];
  }
}

async function executeAgentPing(
  client: MCPClient,
  serverId: string
): Promise<CommandResult[]> {
  try {
    const startTime = Date.now();

    const response = await client.callTool<{ success: boolean; latency_ms?: number }>(
      'ping_agent',
      { server_id: serverId }
    );

    const elapsed = Date.now() - startTime;

    if (!response.success) {
      return [
        { type: 'error', content: t('agents.pingFailed', { error: response.error || 'No response' }) },
      ];
    }

    const latency = response.data?.latency_ms || elapsed;

    return [
      {
        type: 'success',
        content: t('agents.pingSuccess', { serverId, latency }),
      },
    ];
  } catch (err) {
    return [
      {
        type: 'error',
        content: err instanceof Error ? err.message : t('agents.failedToPing'),
      },
    ];
  }
}

async function executeAgentRotate(
  client: MCPClient,
  serverId: string
): Promise<CommandResult[]> {
  try {
    const response = await client.callTool<RotateTokenData>(
      'rotate_agent_token',
      { server_id: serverId }
    );

    if (!response.success) {
      return [
        { type: 'error', content: response.error || t('agents.failedToRotate') },
      ];
    }

    const data = response.data;
    if (!data) {
      return [{ type: 'error', content: t('agents.noRotationData') }];
    }

    return [
      { type: 'success', content: t('agents.rotateSuccess') },
      { type: 'info', content: t('agents.agentIdLabel', { agentId: data.agent_id }) },
      { type: 'info', content: t('agents.gracePeriodLabel', { seconds: data.grace_period_seconds }) },
      { type: 'info', content: t('agents.tokenExpiresLabel', { expiresAt: data.token_expires_at }) },
      { type: 'system', content: t('agents.rotateWebSocketNote') },
    ];
  } catch (err) {
    return [
      {
        type: 'error',
        content: err instanceof Error ? err.message : t('agents.failedToRotate'),
      },
    ];
  }
}

async function executeAgentInstall(
  serverId: string
): Promise<CommandResult[]> {
  try {
    const result = await installAgent(serverId);

    if (!result.success) {
      return [{ type: 'error', content: result.error || t('agents.failedToInstall') }];
    }

    const agentId = result.data?.agent_id || t('common.unknown');
    const version = result.data?.version || t('common.unknown');

    return [
      { type: 'success', content: t('agents.installSuccess', { serverId }) },
      { type: 'info', content: t('agents.agentIdLabel', { agentId }) },
      { type: 'info', content: t('agents.versionInfo', { version }) },
    ];
  } catch (err) {
    return [
      {
        type: 'error',
        content: err instanceof Error ? err.message : t('agents.failedToInstall'),
      },
    ];
  }
}
