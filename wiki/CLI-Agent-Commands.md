# CLI Agent Commands

This page covers CLI commands for managing Tomo Agents on remote servers.

---

## Overview

The Tomo Agent is a lightweight service that runs on managed servers providing:
- Real-time metrics collection
- Secure command execution
- WebSocket-based communication
- Docker container management

---

## Agent List

List all agents and their status.

```bash
tomo agent list
```

**Output:**
```
ID  SERVER           STATUS      VERSION  LAST SEEN
1   Production       Connected   1.0.0    Just now
2   Development      Connected   1.0.0    2 min ago
3   Staging          Offline     0.9.0    3 hours ago
```

**Options:**

| Option | Description |
|--------|-------------|
| `--json` | JSON output |
| `--status <status>` | Filter by status |

---

## Agent Install

Install the agent on a remote server.

```bash
tomo agent install <server-id>
```

**Options:**

| Option | Description |
|--------|-------------|
| `--force` | Reinstall if exists |
| `--version <ver>` | Specific version |

**Example:**

```bash
tomo agent install 1 --force
```

**Process:**
1. Connects to server via SSH
2. Installs Python (if needed)
3. Deploys agent package
4. Configures systemd service
5. Starts agent
6. Verifies connection

---

## Agent Update

Update an agent to the latest version.

```bash
tomo agent update <server-id>
```

**Options:**

| Option | Description |
|--------|-------------|
| `--version <ver>` | Specific version |
| `--force` | Force update |

**Update all agents:**

```bash
tomo agent update-all
```

---

## Agent Status

Check detailed agent status.

```bash
tomo agent status <server-id>
```

**Output:**
```
Agent Status: Connected
  Version:     1.0.0
  Uptime:      5 days 3 hours
  Last Seen:   Just now

Connection:
  WebSocket:   wss://server:8765
  Latency:     45ms

Metrics:
  CPU:         23%
  Memory:      4.2 GB / 16 GB (26%)
  Disk:        120 GB / 500 GB (24%)

Docker:
  Containers:  8 running, 2 stopped
  Images:      15
```

---

## Agent Logs

View agent logs from a remote server.

```bash
tomo agent logs <server-id>
```

**Options:**

| Option | Description |
|--------|-------------|
| `--follow`, `-f` | Stream logs |
| `--lines <n>` | Number of lines |
| `--since <time>` | Since timestamp |

**Example:**

```bash
tomo agent logs 1 --follow --lines 100
```

---

## Agent Restart

Restart the agent service.

```bash
tomo agent restart <server-id>
```

This SSHs to the server and restarts the systemd service.

---

## Agent Stop

Stop the agent service.

```bash
tomo agent stop <server-id>
```

---

## Agent Start

Start a stopped agent.

```bash
tomo agent start <server-id>
```

---

## Agent Uninstall

Remove the agent from a server.

```bash
tomo agent uninstall <server-id>
```

**Options:**

| Option | Description |
|--------|-------------|
| `--keep-data` | Preserve agent data |
| `--force` | Skip confirmation |

**Process:**
1. Stops agent service
2. Removes systemd unit
3. Deletes agent files
4. Cleans up configuration

---

## Token Management

### Rotate Token

Rotate the authentication token for an agent.

```bash
tomo agent rotate-token <server-id>
```

The agent will automatically reconnect with the new token.

### Rotate All Tokens

Rotate tokens for all agents.

```bash
tomo agent rotate-all
```

### View Token

Display the current agent token (admin only).

```bash
tomo agent token <server-id>
```

---

## Agent Configuration

### Show Config

View agent configuration.

```bash
tomo agent config <server-id>
```

**Output:**
```
Agent Configuration:
  Server URL:     wss://tomo.local:8765
  Token:          ****...****
  Metrics Interval: 30s
  Log Level:      INFO
```

### Update Config

Update agent configuration remotely.

```bash
tomo agent config <server-id> --set metrics_interval=60
```

**Configurable options:**

| Option | Description | Default |
|--------|-------------|---------|
| `metrics_interval` | Metrics collection interval | 30s |
| `log_level` | Logging verbosity | INFO |
| `reconnect_interval` | Reconnection delay | 5s |

---

## Diagnostics

### Connection Test

Test connectivity to an agent.

```bash
tomo agent ping <server-id>
```

**Output:**
```
Pinging agent on Production...
Response time: 45ms
Status: OK
```

### Health Check

Run health diagnostics.

```bash
tomo agent health <server-id>
```

**Output:**
```
Agent Health Check:
  ✓ Service running
  ✓ WebSocket connected
  ✓ Token valid
  ✓ Docker accessible
  ✓ Metrics collecting

  Overall: Healthy
```

---

## Scripting Examples

### Check All Agents

```bash
#!/bin/bash
# check-agents.sh

tomo agent list --json | jq -r '.[] | "\(.id) \(.status)"' | \
while read id status; do
  if [ "$status" != "Connected" ]; then
    echo "WARNING: Agent $id is $status"
    # Send notification
  fi
done
```

### Update All Outdated Agents

```bash
#!/bin/bash
# update-agents.sh

CURRENT_VERSION="1.0.0"

tomo agent list --json | \
  jq -r ".[] | select(.version != \"$CURRENT_VERSION\") | .id" | \
while read id; do
  echo "Updating agent $id..."
  tomo agent update "$id"
done
```

### Monitor Agent Health

```bash
#!/bin/bash
# monitor-agents.sh

while true; do
  tomo agent list --json | jq -r '.[] | select(.status != "Connected") | .server' | \
  while read server; do
    echo "$(date): Agent on $server is not connected"
    # Alert
  done
  sleep 60
done
```

### Bulk Token Rotation

```bash
#!/bin/bash
# rotate-tokens.sh

echo "Rotating all agent tokens..."
tomo agent rotate-all

echo "Verifying connections..."
sleep 10
tomo agent list
```

---

## Troubleshooting

### Agent Won't Connect

| Issue | Solution |
|-------|----------|
| Firewall blocking | Open port 8765 |
| Token expired | Rotate token |
| Version mismatch | Update agent |
| Server unreachable | Check network |

### Agent Keeps Disconnecting

1. Check network stability
2. Review agent logs
3. Check server resources
4. Verify firewall rules

### Cannot Install Agent

| Issue | Solution |
|-------|----------|
| SSH fails | Check server credentials |
| Python missing | Will be auto-installed |
| Permission denied | Use sudo-capable user |
| Package fails | Check internet on server |

### Metrics Not Collecting

1. Verify agent is connected
2. Check agent logs for errors
3. Restart agent service
4. Verify Docker permissions

---

## Agent Architecture

```
┌─────────────────────────────────────────────┐
│              Tomo              │
│                (Main Server)                │
│                                             │
│  ┌─────────────────────────────────────┐    │
│  │       WebSocket Server (:8765)      │    │
│  └────────────────┬────────────────────┘    │
└───────────────────┼─────────────────────────┘
                    │
        ┌───────────┼───────────┐
        │           │           │
        ▼           ▼           ▼
┌───────────┐ ┌───────────┐ ┌───────────┐
│  Agent 1  │ │  Agent 2  │ │  Agent 3  │
│  Server A │ │  Server B │ │  Server C │
│           │ │           │ │           │
│ • Metrics │ │ • Metrics │ │ • Metrics │
│ • Docker  │ │ • Docker  │ │ • Docker  │
│ • Commands│ │ • Commands│ │ • Commands│
└───────────┘ └───────────┘ └───────────┘
```

---

## Next Steps

- [[Server-Management]] - Manage servers
- [[CLI-Admin-Commands]] - Admin commands
- [[CLI-Overview]] - CLI overview
