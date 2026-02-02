import { Box, Text } from 'ink';
import React from 'react';

export function Banner() {
  return (
    <Box flexDirection="column" marginBottom={1}>
      <Text color="cyan">{'╔═══════════════════════════════════════════════╗'}</Text>
      <Text>
        <Text color="cyan">{'║'}</Text>
        <Text>   </Text>
        <Text bold color="white">Tomo</Text>
        <Text color="gray"> - Admin CLI</Text>
        <Text>            </Text>
        <Text color="cyan">{'║'}</Text>
      </Text>
      <Text color="cyan">{'╚═══════════════════════════════════════════════╝'}</Text>
    </Box>
  );
}
