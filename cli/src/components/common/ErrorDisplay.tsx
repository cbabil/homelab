import { Box, Text } from 'ink';
import React from 'react';

interface ErrorDisplayProps {
  message: string;
  details?: string;
}

export function ErrorDisplay({ message, details }: ErrorDisplayProps) {
  return (
    <Box flexDirection="column">
      <Box>
        <Text color="red">✗ Error: </Text>
        <Text>{message}</Text>
      </Box>
      {details && (
        <Box marginLeft={2}>
          <Text color="gray">{details}</Text>
        </Box>
      )}
    </Box>
  );
}
