/**
 * Bottom navigation bar with centered tab menu
 */

import { Box, Text } from 'ink';
import React from 'react';
import { COLORS } from '../../app/theme.js';

export interface NavItem {
  key: string;
  label: string;
}

interface NavBarProps {
  items: readonly NavItem[];
  activeTab: string;
}

export function NavBar({ items, activeTab }: NavBarProps) {
  return (
    <Box flexDirection="column" marginTop={1}>
      <Box justifyContent="center">
        {items.map((item, index) => {
          const isActive = item.key === activeTab;
          const separator = index < items.length - 1 ? ' \u2502 ' : '';
          return (
            <Box key={item.key}>
              <Text
                color={isActive ? COLORS.bright : COLORS.dim}
                bold={isActive}
                inverse={isActive}
              >
                {` ${item.label.toUpperCase()} `}
              </Text>
              {separator ? (
                <Text color={COLORS.dim}>{separator}</Text>
              ) : null}
            </Box>
          );
        })}
      </Box>
    </Box>
  );
}
