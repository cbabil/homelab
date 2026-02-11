/**
 * Scrollable activity log panel with vertical scrollbar
 */

import { Box, Text, useInput } from 'ink';
import React, { useState, useEffect, useMemo, useRef } from 'react';
import { COLORS, formatTimestamp } from '../../app/theme.js';
import { Panel } from './Panel.js';
import type { ActivityEntry } from '../../app/dashboard-types.js';
import { t } from '../../i18n/index.js';

function getTypeColor(type: ActivityEntry['type']): string {
  switch (type) {
    case 'CMD':
      return COLORS.primary;
    case 'OK':
      return COLORS.bright;
    case 'ERR':
      return COLORS.error;
    case 'WARN':
      return COLORS.warn;
    case 'SYS':
      return COLORS.dim;
  }
}

function buildScrollbar(
  height: number,
  totalItems: number,
  offset: number
): string[] {
  if (totalItems <= height) {
    return Array.from({ length: height }, () => ' ');
  }

  const thumbSize = Math.max(1, Math.round((height / totalItems) * height));
  const maxOffset = totalItems - height;
  const thumbPos = Math.round((offset / maxOffset) * (height - thumbSize));

  return Array.from({ length: height }, (_, i) => {
    if (i >= thumbPos && i < thumbPos + thumbSize) {
      return '\u2588'; // █ thumb
    }
    return '\u2502'; // │ track
  });
}

interface ActivityLogProps {
  entries: ActivityEntry[];
  height?: number;
  scrollable?: boolean;
}

export function ActivityLog({
  entries,
  height = 16,
  scrollable = true,
}: ActivityLogProps) {
  const [scrollOffset, setScrollOffset] = useState(() =>
    Math.max(0, entries.length - height)
  );
  const prevLengthRef = useRef(entries.length);

  // Auto-scroll to bottom when new entries arrive
  useEffect(() => {
    if (entries.length > prevLengthRef.current) {
      const maxScroll = Math.max(0, entries.length - height);
      setScrollOffset(maxScroll);
    }
    prevLengthRef.current = entries.length;
  }, [entries.length, height]);

  // Page Up/Down scrolling (arrow keys reserved for CommandPrompt history)
  useInput(
    (_input, key) => {
      const maxScroll = Math.max(0, entries.length - height);

      if (key.pageUp) {
        setScrollOffset((prev) => Math.max(0, prev - height));
      } else if (key.pageDown) {
        setScrollOffset((prev) => Math.min(maxScroll, prev + height));
      }
    },
    { isActive: scrollable && entries.length > height }
  );

  const visibleEntries = useMemo(() => {
    return entries.slice(scrollOffset, scrollOffset + height);
  }, [entries, scrollOffset, height]);

  const scrollbar = buildScrollbar(height, entries.length, scrollOffset);
  const showScrollbar = entries.length > height;

  return (
    <Panel title={t('dashboard.recentActivity')} height={height + 4}>
      {entries.length === 0 ? (
        <Text color={COLORS.dim}>{t('dashboard.noRecentActivity')}</Text>
      ) : (
        <Box height={height}>
          {/* Log content */}
          <Box flexDirection="column" flexGrow={1}>
            {visibleEntries.map((entry) => {
              const color = getTypeColor(entry.type);
              return (
                <Box key={entry.id}>
                  <Text color={entry.type === 'ERR' ? color : COLORS.dim}>
                    {`[${formatTimestamp(entry.timestamp)}]  `}
                  </Text>
                  <Text color={color}>
                    {`${entry.type.padEnd(4)}: `}
                  </Text>
                  <Text color={entry.type === 'ERR' ? color : COLORS.primary}>
                    {entry.message}
                  </Text>
                </Box>
              );
            })}

            {/* Fill empty rows */}
            {visibleEntries.length < height && (
              <Box height={height - visibleEntries.length} />
            )}
          </Box>

          {/* Vertical scrollbar */}
          {showScrollbar ? (
            <Box flexDirection="column" marginLeft={1}>
              {scrollbar.map((char, i) => (
                <Text key={i} color={COLORS.dim}>
                  {char}
                </Text>
              ))}
            </Box>
          ) : null}
        </Box>
      )}
    </Panel>
  );
}
