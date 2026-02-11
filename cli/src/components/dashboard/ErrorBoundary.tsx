/**
 * Error boundary for graceful error handling in view area
 */

import { Box, Text } from 'ink';
import React, { Component, type ErrorInfo, type ReactNode } from 'react';
import { COLORS } from '../../app/theme.js';
import { t } from '../../i18n/index.js';

interface ErrorBoundaryProps {
  children: ReactNode;
  fallbackMessage?: string;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    // Log to stderr so it doesn't interfere with terminal UI
    process.stderr.write(
      `[ErrorBoundary] ${error.message}\n${info.componentStack ?? ''}\n`
    );
  }

  render(): ReactNode {
    if (this.state.hasError) {
      return (
        <Box flexDirection="column" paddingX={1}>
          <Text color={COLORS.error} bold>
            {this.props.fallbackMessage ?? t('common.somethingWentWrong')}
          </Text>
          <Text color={COLORS.dim}>
            {this.state.error?.message ?? t('common.unknownError')}
          </Text>
        </Box>
      );
    }
    return this.props.children;
  }
}
