import { Box, Text } from 'ink';
import InkSpinner from 'ink-spinner';
import React from 'react';

interface SpinnerProps {
  text: string;
}

export function Spinner({ text }: SpinnerProps) {
  return (
    <Box>
      <Text color="cyan">
        <InkSpinner type="dots" />
      </Text>
      <Text> {text}</Text>
    </Box>
  );
}
