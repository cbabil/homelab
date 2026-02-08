/**
 * ASCII art header for the dashboard
 */

import { Box, Text } from 'ink';
import React from 'react';
import { COLORS } from '../../app/theme.js';

const ASCII_ART = `
 ████████╗ ██████╗ ███╗   ███╗ ██████╗
 ╚══██╔══╝██╔═══██╗████╗ ████║██╔═══██╗
    ██║   ██║   ██║██╔████╔██║██║   ██║
    ██║   ██║   ██║██║╚██╔╝██║██║   ██║
    ██║   ╚██████╔╝██║ ╚═╝ ██║╚██████╔╝
    ╚═╝    ╚═════╝ ╚═╝     ╚═╝ ╚═════╝
              A D M I N
`.trimStart();

export function AsciiHeader() {
  return (
    <Box flexDirection="column" alignItems="center">
      {ASCII_ART.split('\n').map((line, i) => (
        <Text key={i} color={COLORS.primary}>
          {line}
        </Text>
      ))}
    </Box>
  );
}
