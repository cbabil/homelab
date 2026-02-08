/**
 * Settings view with internal tab navigation (left/right arrows)
 */

import { Box, Text, useInput } from 'ink';
import React, { useState } from 'react';
import { COLORS } from '../theme.js';
import { Panel } from '../../components/dashboard/Panel.js';

interface SettingsViewProps {
  mcpUrl: string;
  refreshInterval: number;
  autoRefresh: boolean;
  version: string;
}

type SettingsTab = 'connection' | 'preferences' | 'about';

const TABS: { key: SettingsTab; label: string }[] = [
  { key: 'connection', label: 'CONNECTION' },
  { key: 'preferences', label: 'PREFERENCES' },
  { key: 'about', label: 'ABOUT' },
];

function SettingRow({ label, value }: { label: string; value: string }) {
  return (
    <Box>
      <Text color={COLORS.dim}>{label.padEnd(20)}</Text>
      <Text color={COLORS.bright}>{value}</Text>
    </Box>
  );
}

function SettingsTabBar({ activeTab }: { activeTab: SettingsTab }) {
  return (
    <Box marginBottom={1}>
      {TABS.map((tab, index) => {
        const isActive = tab.key === activeTab;
        const separator = index < TABS.length - 1 ? ' \u2502 ' : '';
        return (
          <Box key={tab.key}>
            <Text
              color={isActive ? COLORS.bright : COLORS.dim}
              bold={isActive}
              inverse={isActive}
            >
              {` ${tab.label} `}
            </Text>
            {separator ? (
              <Text color={COLORS.dim}>{separator}</Text>
            ) : null}
          </Box>
        );
      })}
      <Text color={COLORS.dim}>{'  \u2190\u2192 navigate'}</Text>
    </Box>
  );
}

export function SettingsView({
  mcpUrl,
  refreshInterval,
  autoRefresh,
  version,
}: SettingsViewProps) {
  const [activeTab, setActiveTab] = useState<SettingsTab>('connection');

  useInput((_input, key) => {
    if (key.leftArrow) {
      const idx = TABS.findIndex((t) => t.key === activeTab);
      const prev = (idx - 1 + TABS.length) % TABS.length;
      setActiveTab(TABS[prev]!.key);
    } else if (key.rightArrow) {
      const idx = TABS.findIndex((t) => t.key === activeTab);
      const next = (idx + 1) % TABS.length;
      setActiveTab(TABS[next]!.key);
    }
  });

  const renderTab = () => {
    switch (activeTab) {
      case 'connection':
        return (
          <Box flexDirection="column">
            <SettingRow label="MCP Server URL" value={mcpUrl} />
            <Box marginTop={1}>
              <Text color={COLORS.dim}>
                {'Set MCP_SERVER_URL environment variable to change.'}
              </Text>
            </Box>
          </Box>
        );
      case 'preferences':
        return (
          <Box flexDirection="column">
            <SettingRow
              label="Refresh Interval"
              value={`${refreshInterval / 1000}s`}
            />
            <SettingRow
              label="Auto Refresh"
              value={autoRefresh ? 'ON' : 'OFF'}
            />
          </Box>
        );
      case 'about':
        return (
          <Box flexDirection="column">
            <SettingRow label="CLI Version" value={version} />
            <Box marginTop={1}>
              <Text color={COLORS.dim}>
                {'Use environment variables to configure settings.'}
              </Text>
            </Box>
          </Box>
        );
    }
  };

  return (
    <Panel title="SETTINGS">
      <Box flexDirection="column">
        <SettingsTabBar activeTab={activeTab} />
        {renderTab()}
      </Box>
    </Panel>
  );
}
