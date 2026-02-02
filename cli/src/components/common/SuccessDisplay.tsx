import { Box, Text } from 'ink';
import React from 'react';

interface SuccessDisplayProps {
  message: string;
  details?: Record<string, string>;
}

export function SuccessDisplay({ message, details }: SuccessDisplayProps) {
  return (
    <Box flexDirection="column">
      <Box>
        <Text color="green">✔ </Text>
        <Text>{message}</Text>
      </Box>
      {details && (
        <Box flexDirection="column" marginLeft={2}>
          {Object.entries(details).map(([key, value]) => (
            <Text key={key} color="gray">
              {key}: {value}
            </Text>
          ))}
        </Box>
      )}
    </Box>
  );
}
