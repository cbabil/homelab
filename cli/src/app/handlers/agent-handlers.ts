/**
 * Agent command handlers for the interactive CLI
 */

import type { CommandResult } from '../types.js';
import type { MCPClient } from '../../lib/mcp-client.js';
import type { AgentInfo, RotateTokenData } from '../../lib/agent.js';
import { installAgent } from '../../lib/agent.js';
import { sanitizeForDisplay } from '../../lib/validation.js';

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
        return [{ type: 'error', content: 'Usage: agent status <server-id>' }];
      }
      return executeAgentStatus(client, args[0]);

    case 'ping':
      if (!args[0]) {
        return [{ type: 'error', content: 'Usage: agent ping <server-id>' }];
      }
      return executeAgentPing(client, args[0]);

    case 'rotate':
      if (!args[0]) {
        return [{ type: 'error', content: 'Usage: agent rotate <server-id>' }];
      }
      return executeAgentRotate(client, args[0]);

    case 'install':
      if (!args[0]) {
        return [{ type: 'error', content: 'Usage: agent install <server-id>' }];
      }
      return executeAgentInstall(args[0]);

    default:
      return [
        {
          type: 'error',
          content: subcommand
            ? `Unknown agent subcommand: ${sanitizeForDisplay(subcommand)}`
            : 'Usage: agent <list|status|ping|rotate|install> [args]',
        },
      ];
  }
}

async function executeAgentList(
  client: MCPClient
): Promise<CommandResult[]> {
  const response = await client.callTool<{ agents: AgentInfo[] }>('list_agents', {});

  if (!response.success) {
    return [{ type: 'error', content: response.error || 'Failed to list agents' }];
  }

  const agents = response.data?.agents || [];

  if (agents.length === 0) {
    return [{ type: 'info', content: 'No agents found.' }];
  }

  const results: CommandResult[] = [
    { type: 'info', content: `Found ${agents.length} agent(s):` },
  ];

  for (const agent of agents) {
    results.push({
      type: agent.status === 'connected' ? 'success' : 'info',
      content: `  [${agent.id}] Server: ${agent.server_id} - ${agent.status}`,
    });
  }

  return results;
}

async function executeAgentStatus(
  client: MCPClient,
  serverId: string
): Promise<CommandResult[]> {
  const response = await client.callTool<AgentInfo>('get_agent_status', {
    server_id: serverId,
  });

  if (!response.success) {
    return [{ type: 'error', content: response.error || 'Failed to get agent status' }];
  }

  const agent = response.data;
  if (!agent) {
    return [{ type: 'error', content: 'Agent not found' }];
  }

  return [
    { type: 'info', content: `Agent Status for server ${serverId}:` },
    {
      type: agent.status === 'connected' ? 'success' : 'info',
      content: `  Status: ${agent.status}`,
    },
    { type: 'info', content: `  Version: ${agent.version || 'unknown'}` },
    { type: 'info', content: `  Last seen: ${agent.last_seen || 'never'}` },
  ];
}

async function executeAgentPing(
  client: MCPClient,
  serverId: string
): Promise<CommandResult[]> {
  const startTime = Date.now();

  const response = await client.callTool<{ success: boolean; latency_ms?: number }>(
    'ping_agent',
    { server_id: serverId }
  );

  const elapsed = Date.now() - startTime;

  if (!response.success) {
    return [
      { type: 'error', content: `Ping failed: ${response.error || 'No response'}` },
    ];
  }

  const latency = response.data?.latency_ms || elapsed;

  return [
    {
      type: 'success',
      content: `Pong! Agent on server ${serverId} responded in ${latency}ms`,
    },
  ];
}

async function executeAgentRotate(
  client: MCPClient,
  serverId: string
): Promise<CommandResult[]> {
  const response = await client.callTool<RotateTokenData>(
    'rotate_agent_token',
    { server_id: serverId }
  );

  if (!response.success) {
    return [
      { type: 'error', content: response.error || 'Failed to rotate agent token' },
    ];
  }

  const data = response.data;
  if (!data) {
    return [{ type: 'error', content: 'No rotation data received' }];
  }

  return [
    { type: 'success', content: 'Token rotation initiated successfully!' },
    { type: 'info', content: `  Agent ID: ${data.agent_id}` },
    { type: 'info', content: `  Grace Period: ${data.grace_period_seconds} seconds` },
    { type: 'info', content: `  Token Expires: ${data.token_expires_at}` },
    { type: 'system', content: 'The agent will receive the new token via WebSocket.' },
  ];
}

async function executeAgentInstall(
  serverId: string
): Promise<CommandResult[]> {
  try {
    const result = await installAgent(serverId);

    if (!result.success) {
      return [{ type: 'error', content: result.error || 'Failed to install agent' }];
    }

    const agentId = result.data?.agent_id || 'unknown';
    const version = result.data?.version || 'unknown';

    return [
      { type: 'success', content: `Agent installed on server ${serverId}` },
      { type: 'info', content: `  Agent ID: ${agentId}` },
      { type: 'info', content: `  Version: ${version}` },
    ];
  } catch (err) {
    return [
      {
        type: 'error',
        content: err instanceof Error ? err.message : 'Failed to install agent',
      },
    ];
  }
}
