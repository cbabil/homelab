/**
 * Mock Logs Data
 * 
 * Sample log entries for different categories to populate the logs page.
 */

export interface LogEntry {
  id: string
  timestamp: string
  level: 'info' | 'warn' | 'error' | 'debug'
  source: string
  message: string
  category: 'system' | 'application' | 'security' | 'network'
  details?: string
}

export const mockSystemLogs: LogEntry[] = [
  {
    id: 'sys-001',
    timestamp: '2025-01-11T10:30:15Z',
    level: 'info',
    source: 'systemd',
    message: 'Service docker.service started successfully',
    category: 'system'
  },
  {
    id: 'sys-002',
    timestamp: '2025-01-11T10:29:45Z',
    level: 'warn',
    source: 'kernel',
    message: 'Temperature warning: CPU core 0 reached 85°C',
    category: 'system',
    details: 'Core temperature exceeded normal operating range'
  },
  {
    id: 'sys-003',
    timestamp: '2025-01-11T10:25:30Z',
    level: 'info',
    source: 'cron',
    message: 'Daily backup job completed successfully',
    category: 'system'
  },
  {
    id: 'sys-004',
    timestamp: '2025-01-11T10:20:12Z',
    level: 'error',
    source: 'disk',
    message: 'Disk /dev/sda1 usage above 90%',
    category: 'system',
    details: 'Available space: 2.1GB remaining of 100GB total'
  }
]

export const mockApplicationLogs: LogEntry[] = [
  {
    id: 'app-001',
    timestamp: '2025-01-11T10:32:45Z',
    level: 'info',
    source: 'homelab-frontend',
    message: 'User authentication successful',
    category: 'application'
  },
  {
    id: 'app-002',
    timestamp: '2025-01-11T10:31:20Z',
    level: 'error',
    source: 'postgres',
    message: 'Connection timeout to database server',
    category: 'application',
    details: 'Failed to establish connection after 30 seconds'
  },
  {
    id: 'app-003',
    timestamp: '2025-01-11T10:28:15Z',
    level: 'warn',
    source: 'nginx',
    message: 'High request rate detected from IP 192.168.1.100',
    category: 'application'
  },
  {
    id: 'app-004',
    timestamp: '2025-01-11T10:25:45Z',
    level: 'debug',
    source: 'api-server',
    message: 'Processing server status update request',
    category: 'application'
  }
]

export const mockSecurityLogs: LogEntry[] = [
  {
    id: 'sec-001',
    timestamp: '2025-01-11T10:35:20Z',
    level: 'warn',
    source: 'sshd',
    message: 'Failed SSH login attempt from 203.0.113.42',
    category: 'security',
    details: 'User: root, Failed attempts: 3'
  },
  {
    id: 'sec-002',
    timestamp: '2025-01-11T10:30:45Z',
    level: 'info',
    source: 'fail2ban',
    message: 'IP 203.0.113.42 banned for repeated failed attempts',
    category: 'security'
  },
  {
    id: 'sec-003',
    timestamp: '2025-01-11T10:28:30Z',
    level: 'info',
    source: 'sudo',
    message: 'User admin executed command: systemctl restart nginx',
    category: 'security'
  },
  {
    id: 'sec-004',
    timestamp: '2025-01-11T10:25:15Z',
    level: 'error',
    source: 'firewall',
    message: 'Blocked incoming connection on port 22 from 198.51.100.23',
    category: 'security',
    details: 'Reason: Rate limiting exceeded'
  }
]

export const mockNetworkLogs: LogEntry[] = [
  {
    id: 'net-001',
    timestamp: '2025-01-11T10:33:15Z',
    level: 'info',
    source: 'dhcp',
    message: 'Lease assigned to device MAC:aa:bb:cc:dd:ee:ff',
    category: 'network'
  },
  {
    id: 'net-002',
    timestamp: '2025-01-11T10:30:20Z',
    level: 'warn',
    source: 'router',
    message: 'High bandwidth usage detected on interface eth0',
    category: 'network',
    details: 'Current usage: 850 Mbps out of 1 Gbps capacity'
  },
  {
    id: 'net-003',
    timestamp: '2025-01-11T10:27:45Z',
    level: 'error',
    source: 'dns',
    message: 'Failed to resolve external.example.com',
    category: 'network'
  },
  {
    id: 'net-004',
    timestamp: '2025-01-11T10:25:30Z',
    level: 'info',
    source: 'vpn',
    message: 'VPN client connected from 192.168.100.50',
    category: 'network'
  }
]

export const allMockLogs: LogEntry[] = [
  ...mockSystemLogs,
  ...mockApplicationLogs,
  ...mockSecurityLogs,
  ...mockNetworkLogs
].sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())

export const logCategories = [
  { id: 'all', name: 'All Logs', count: allMockLogs.length },
  { id: 'system', name: 'System', count: mockSystemLogs.length },
  { id: 'application', name: 'Application', count: mockApplicationLogs.length },
  { id: 'security', name: 'Security', count: mockSecurityLogs.length },
  { id: 'network', name: 'Network', count: mockNetworkLogs.length }
]