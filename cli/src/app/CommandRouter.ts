/**
 * Command Router for the interactive CLI
 *
 * Parses user input and routes to appropriate command handlers.
 */

import type { AppState, CommandResult } from './types.js';
import { getMCPClient } from '../lib/mcp-client.js';

interface SlashCommand {
  name: string;
  aliases: string[];
  description: string;
  handler: (args: string[], state: AppState) => Promise<CommandResult[]>;
}

interface AgentInfo {
  id: string;
  server_id: string;
  status: string;
  version?: string;
  last_seen?: string;
}

interface ServerInfo {
  id: string;
  name: string;
  hostname: string;
  status: string;
}

const slashCommands: SlashCommand[] = [
  {
    name: 'help',
    aliases: ['h', '?'],
    description: 'Show available commands',
    handler: async () => [
      {
        type: 'info',
        content: 'Available Commands:',
      },
      {
        type: 'system',
        content: '  /help, /h, /?     - Show this help message',
      },
      {
        type: 'system',
        content: '  /clear, /cls      - Clear output history',
      },
      {
        type: 'system',
        content: '  /quit, /exit, /q  - Exit the CLI',
      },
      {
        type: 'system',
        content: '  /status           - Show connection status',
      },
      {
        type: 'system',
        content: '  /servers          - List all servers',
      },
      {
        type: 'system',
        content: '  /agents           - List all agents',
      },
      {
        type: 'system',
        content: '  /login            - Authenticate as admin',
      },
      {
        type: 'system',
        content: '  /logout           - Clear authentication',
      },
      {
        type: 'info',
        content: '',
      },
      {
        type: 'info',
        content: 'One-shot commands (also work in shell):',
      },
      {
        type: 'system',
        content: '  agent list        - List agents',
      },
      {
        type: 'system',
        content: '  agent status <id> - Get agent status',
      },
      {
        type: 'system',
        content: '  agent ping <id>   - Ping an agent',
      },
      {
        type: 'system',
        content: '  agent rotate <id> - Rotate agent token',
      },
      {
        type: 'system',
        content: '  update            - Check for updates',
      },
    ],
  },
  {
    name: 'clear',
    aliases: ['cls'],
    description: 'Clear output history',
    handler: async () => [{ type: 'system', content: '__CLEAR__' }],
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
    handler: async (_args, state) => {
      const results: CommandResult[] = [];

      results.push({
        type: 'info',
        content: 'Connection Status:',
      });

      results.push({
        type: state.mcpConnected ? 'success' : 'error',
        content: `  MCP: ${state.mcpConnected ? 'Connected' : 'Disconnected'}`,
      });

      results.push({
        type: 'info',
        content: `  URL: ${state.mcpUrl}`,
      });

      results.push({
        type: state.authenticated ? 'success' : 'info',
        content: `  Auth: ${state.authenticated ? `Authenticated as ${state.username}` : 'Not authenticated'}`,
      });

      return results;
    },
  },
  {
    name: 'servers',
    aliases: [],
    description: 'List all servers',
    handler: async (_args, state) => {
      if (!state.mcpConnected) {
        return [{ type: 'error', content: 'Not connected to MCP server' }];
      }

      try {
        const client = getMCPClient();
        const response = await client.callTool<{ servers: ServerInfo[] }>(
          'list_servers',
          {}
        );

        if (!response.success) {
          return [
            { type: 'error', content: response.error || 'Failed to list servers' },
          ];
        }

        const servers = response.data?.servers || [];

        if (servers.length === 0) {
          return [{ type: 'info', content: 'No servers found.' }];
        }

        const results: CommandResult[] = [
          { type: 'info', content: `Found ${servers.length} server(s):` },
        ];

        for (const server of servers) {
          const statusColor = server.status === 'online' ? 'success' : 'info';
          results.push({
            type: statusColor,
            content: `  [${server.id}] ${server.name} (${server.hostname}) - ${server.status}`,
          });
        }

        return results;
      } catch (err) {
        return [
          {
            type: 'error',
            content: err instanceof Error ? err.message : 'Failed to list servers',
          },
        ];
      }
    },
  },
  {
    name: 'agents',
    aliases: [],
    description: 'List all agents',
    handler: async (_args, state) => {
      if (!state.mcpConnected) {
        return [{ type: 'error', content: 'Not connected to MCP server' }];
      }

      try {
        const client = getMCPClient();
        const response = await client.callTool<{ agents: AgentInfo[] }>(
          'list_agents',
          {}
        );

        if (!response.success) {
          return [
            { type: 'error', content: response.error || 'Failed to list agents' },
          ];
        }

        const agents = response.data?.agents || [];

        if (agents.length === 0) {
          return [{ type: 'info', content: 'No agents found.' }];
        }

        const results: CommandResult[] = [
          { type: 'info', content: `Found ${agents.length} agent(s):` },
        ];

        for (const agent of agents) {
          const statusType =
            agent.status === 'connected' ? 'success' : 'info';
          results.push({
            type: statusType,
            content: `  [${agent.id}] Server: ${agent.server_id} - ${agent.status.toUpperCase()}`,
          });
          if (agent.version) {
            results.push({
              type: 'system',
              content: `       Version: ${agent.version}`,
            });
          }
        }

        return results;
      } catch (err) {
        return [
          {
            type: 'error',
            content: err instanceof Error ? err.message : 'Failed to list agents',
          },
        ];
      }
    },
  },
  {
    name: 'login',
    aliases: [],
    description: 'Authenticate as admin',
    handler: async () => {
      // This requires interactive prompting, which we'll handle separately
      return [
        {
          type: 'info',
          content: 'Login requires interactive prompts. Use: tomo admin create',
        },
      ];
    },
  },
  {
    name: 'logout',
    aliases: [],
    description: 'Clear authentication',
    handler: async () => [
      { type: 'system', content: '__LOGOUT__' },
      { type: 'success', content: 'Logged out successfully' },
    ],
  },
];

// Parse regular commands (non-slash)
async function handleRegularCommand(
  input: string,
  state: AppState
): Promise<CommandResult[]> {
  const parts = input.trim().split(/\s+/);
  const command = parts[0]?.toLowerCase();
  const subcommand = parts[1]?.toLowerCase();
  const args = parts.slice(2);

  if (!state.mcpConnected) {
    return [{ type: 'error', content: 'Not connected to MCP server' }];
  }

  const client = getMCPClient();

  switch (command) {
    case 'agent':
      return handleAgentCommand(client, subcommand, args);

    case 'update':
      return handleUpdateCommand(client);

    case 'server':
      return handleServerCommand(client, subcommand, args);

    default:
      return [
        { type: 'error', content: `Unknown command: ${command}` },
        { type: 'info', content: 'Type /help for available commands' },
      ];
  }
}

async function handleAgentCommand(
  client: ReturnType<typeof getMCPClient>,
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

    default:
      return [
        {
          type: 'error',
          content: subcommand
            ? `Unknown agent subcommand: ${subcommand}`
            : 'Usage: agent <list|status|ping|rotate> [args]',
        },
      ];
  }
}

async function executeAgentList(
  client: ReturnType<typeof getMCPClient>
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
  client: ReturnType<typeof getMCPClient>,
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
  client: ReturnType<typeof getMCPClient>,
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

interface RotateTokenResponse {
  agent_id: string;
  server_id: string;
  grace_period_seconds: number;
  token_expires_at: string;
}

async function executeAgentRotate(
  client: ReturnType<typeof getMCPClient>,
  serverId: string
): Promise<CommandResult[]> {
  const response = await client.callTool<RotateTokenResponse>(
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

async function handleServerCommand(
  client: ReturnType<typeof getMCPClient>,
  subcommand: string,
  _args: string[]
): Promise<CommandResult[]> {
  switch (subcommand) {
    case 'list':
      const response = await client.callTool<{ servers: ServerInfo[] }>(
        'list_servers',
        {}
      );

      if (!response.success) {
        return [{ type: 'error', content: response.error || 'Failed to list servers' }];
      }

      const servers = response.data?.servers || [];

      if (servers.length === 0) {
        return [{ type: 'info', content: 'No servers found.' }];
      }

      const results: CommandResult[] = [
        { type: 'info', content: `Found ${servers.length} server(s):` },
      ];

      for (const server of servers) {
        results.push({
          type: server.status === 'online' ? 'success' : 'info',
          content: `  [${server.id}] ${server.name} - ${server.hostname}`,
        });
      }

      return results;

    default:
      return [
        {
          type: 'error',
          content: subcommand
            ? `Unknown server subcommand: ${subcommand}`
            : 'Usage: server <list>',
        },
      ];
  }
}

async function handleUpdateCommand(
  client: ReturnType<typeof getMCPClient>
): Promise<CommandResult[]> {
  const response = await client.callTool<{
    current_version: string;
    latest_version: string;
    update_available: boolean;
  }>('check_updates', {});

  if (!response.success) {
    return [{ type: 'error', content: response.error || 'Failed to check updates' }];
  }

  const data = response.data;
  if (!data) {
    return [{ type: 'error', content: 'No update information available' }];
  }

  if (data.update_available) {
    return [
      { type: 'info', content: `Current version: ${data.current_version}` },
      {
        type: 'success',
        content: `Update available: ${data.latest_version}`,
      },
    ];
  }

  return [
    { type: 'success', content: `You are running the latest version: ${data.current_version}` },
  ];
}

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
    const cmdName = parts[0]?.toLowerCase();
    const args = parts.slice(1);

    for (const cmd of slashCommands) {
      if (cmd.name === cmdName || cmd.aliases.includes(cmdName)) {
        return cmd.handler(args, state);
      }
    }

    return [
      { type: 'error', content: `Unknown command: /${cmdName}` },
      { type: 'info', content: 'Type /help for available commands' },
    ];
  }

  // Handle regular commands
  return handleRegularCommand(trimmed, state);
}
