/**
 * Status badge component for agent/server status display
 *
 * Renders: [ACTIVE], [IDLE], [OFFLINE], [LOCKED]
 */

import { Text } from 'ink';
import React from 'react';
import { BADGES, type BadgeStatus } from '../../app/theme.js';

interface StatusBadgeProps {
  status: BadgeStatus;
}

export function StatusBadge({ status }: StatusBadgeProps) {
  const badge = BADGES[status];

  return (
    <Text color={badge.color}>{`[${badge.label}]`}</Text>
  );
}
