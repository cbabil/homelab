import { Box, Text, useInput } from 'ink';
import React, { useState, useEffect, useMemo } from 'react';
import type { OutputMessage } from './types.js';

interface OutputHistoryProps {
  messages: OutputMessage[];
  height?: number;
  focused?: boolean;
}

const TYPE_COLORS: Record<string, string> = {
  info: 'white',
  success: 'green',
  error: 'red',
  command: 'cyan',
  system: 'gray',
};

const TYPE_PREFIXES: Record<string, string> = {
  info: '',
  success: '[OK] ',
  error: '[ERROR] ',
  command: '> ',
  system: '',
};

function formatTimestamp(date: Date): string {
  return date.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  });
}

export function OutputHistory({
  messages,
  height = 15,
  focused = false,
}: OutputHistoryProps) {
  const [scrollOffset, setScrollOffset] = useState(0);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    const maxScroll = Math.max(0, messages.length - height);
    setScrollOffset(maxScroll);
  }, [messages.length, height]);

  // Handle keyboard scrolling when focused
  useInput(
    (input, key) => {
      if (!focused) return;

      const maxScroll = Math.max(0, messages.length - height);

      if (key.upArrow || input === 'k') {
        setScrollOffset((prev) => Math.max(0, prev - 1));
      } else if (key.downArrow || input === 'j') {
        setScrollOffset((prev) => Math.min(maxScroll, prev + 1));
      } else if (key.pageUp) {
        setScrollOffset((prev) => Math.max(0, prev - height));
      } else if (key.pageDown) {
        setScrollOffset((prev) => Math.min(maxScroll, prev + height));
      } else if (input === 'g') {
        setScrollOffset(0);
      } else if (input === 'G') {
        setScrollOffset(maxScroll);
      }
    },
    { isActive: focused }
  );

  // Calculate visible messages
  const visibleMessages = useMemo(() => {
    return messages.slice(scrollOffset, scrollOffset + height);
  }, [messages, scrollOffset, height]);

  // Show scroll indicator
  const canScrollUp = scrollOffset > 0;
  const canScrollDown = scrollOffset < messages.length - height;

  return (
    <Box flexDirection="column" height={height}>
      {canScrollUp && (
        <Text color="gray" dimColor>
          {'  --- scroll up for more ---'}
        </Text>
      )}

      {visibleMessages.map((msg) => (
        <Box key={msg.id}>
          <Text color="gray" dimColor>
            {formatTimestamp(msg.timestamp)}{' '}
          </Text>
          <Text color={TYPE_COLORS[msg.type] || 'white'}>
            {TYPE_PREFIXES[msg.type] || ''}
            {msg.content}
          </Text>
        </Box>
      ))}

      {/* Fill empty space if not enough messages */}
      {visibleMessages.length < height - (canScrollUp ? 1 : 0) && (
        <Box height={height - visibleMessages.length - (canScrollUp ? 1 : 0)} />
      )}

      {canScrollDown && (
        <Text color="gray" dimColor>
          {'  --- scroll down for more ---'}
        </Text>
      )}
    </Box>
  );
}
