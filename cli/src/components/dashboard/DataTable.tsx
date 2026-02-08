/**
 * Terminal-style data table with fixed-width columns
 */

import { Box, Text } from 'ink';
import React from 'react';
import { COLORS } from '../../app/theme.js';

export interface DataColumn<T> {
  key: string;
  header: string;
  width: number;
  render?: (row: T) => React.ReactNode;
}

interface DataTableProps<T> {
  columns: DataColumn<T>[];
  data: T[];
  emptyMessage?: string;
  rowKey?: (row: T, index: number) => string;
}

function truncate(text: string, width: number): string {
  if (width < 3) {
    return text.slice(0, Math.max(1, width));
  }
  if (text.length <= width) {
    return text.padEnd(width);
  }
  return text.slice(0, width - 2) + '..';
}

function getColumnValue<T>(row: T, key: string): string {
  const value = (row as Record<string, unknown>)[key];
  if (value === null || value === undefined) return '-';
  return String(value);
}

export function DataTable<T>({
  columns,
  data,
  emptyMessage = 'No data available',
  rowKey,
}: DataTableProps<T>) {
  if (data.length === 0) {
    return (
      <Box>
        <Text color={COLORS.dim}>{emptyMessage}</Text>
      </Box>
    );
  }

  return (
    <Box flexDirection="column">
      {/* Header row */}
      <Box>
        {columns.map((col) => (
          <Box key={col.key} width={col.width}>
            <Text bold color={COLORS.bright}>
              {col.header.toUpperCase().padEnd(col.width)}
            </Text>
          </Box>
        ))}
      </Box>

      {/* Separator */}
      <Box>
        <Text color={COLORS.dim}>
          {columns.map((col) => '-'.repeat(col.width)).join('')}
        </Text>
      </Box>

      {/* Data rows */}
      {data.map((row, rowIndex) => (
        <Box key={rowKey ? rowKey(row, rowIndex) : `row-${rowIndex}`}>
          {columns.map((col) => (
            <Box key={col.key} width={col.width}>
              {col.render ? (
                col.render(row)
              ) : (
                <Text color={COLORS.primary}>
                  {truncate(getColumnValue(row, col.key), col.width)}
                </Text>
              )}
            </Box>
          ))}
        </Box>
      ))}
    </Box>
  );
}
