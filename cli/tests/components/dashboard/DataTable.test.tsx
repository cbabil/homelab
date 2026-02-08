/**
 * Tests for DataTable component.
 */

import { describe, it, expect } from 'vitest';
import { render } from 'ink-testing-library';
import React from 'react';
import { Text } from 'ink';
import { DataTable, type DataColumn } from '../../../src/components/dashboard/DataTable.js';

interface TestRow {
  id: string;
  name: string;
  status: string;
}

const testColumns: DataColumn<TestRow>[] = [
  { key: 'id', header: 'ID', width: 10 },
  { key: 'name', header: 'Name', width: 15 },
  { key: 'status', header: 'Status', width: 10 },
];

const testData: TestRow[] = [
  { id: 'srv-001', name: 'Web Server', status: 'online' },
  { id: 'srv-002', name: 'DB Server', status: 'offline' },
];

describe('DataTable', () => {
  it('should render column headers in uppercase', () => {
    const { lastFrame } = render(
      <DataTable columns={testColumns} data={testData} />
    );

    const frame = lastFrame() || '';
    expect(frame).toContain('ID');
    expect(frame).toContain('NAME');
    expect(frame).toContain('STATUS');
  });

  it('should render data rows', () => {
    const { lastFrame } = render(
      <DataTable columns={testColumns} data={testData} />
    );

    const frame = lastFrame() || '';
    expect(frame).toContain('srv-001');
    expect(frame).toContain('Web Server');
    expect(frame).toContain('online');
  });

  it('should render separator row', () => {
    const { lastFrame } = render(
      <DataTable columns={testColumns} data={testData} />
    );

    const frame = lastFrame() || '';
    expect(frame).toContain('---');
  });

  it('should show empty message when no data', () => {
    const { lastFrame } = render(
      <DataTable columns={testColumns} data={[]} emptyMessage="Nothing here" />
    );

    expect(lastFrame()).toContain('Nothing here');
  });

  it('should show default empty message', () => {
    const { lastFrame } = render(
      <DataTable columns={testColumns} data={[]} />
    );

    expect(lastFrame()).toContain('No data available');
  });

  it('should support custom render function', () => {
    const columnsWithRender: DataColumn<TestRow>[] = [
      { key: 'id', header: 'ID', width: 10 },
      {
        key: 'status',
        header: 'Status',
        width: 12,
        render: (row) => <Text color="green">{`[${row.status.toUpperCase()}]`}</Text>,
      },
    ];

    const { lastFrame } = render(
      <DataTable columns={columnsWithRender} data={testData} />
    );

    const frame = lastFrame() || '';
    expect(frame).toContain('[ONLINE]');
  });

  it('should show dash for null values', () => {
    const dataWithNull = [{ id: 'srv-003', name: 'Test', status: null as unknown as string }];

    const { lastFrame } = render(
      <DataTable columns={testColumns} data={dataWithNull} />
    );

    expect(lastFrame()).toContain('-');
  });

  it('should truncate long values', () => {
    const longData = [
      { id: 'very-long-server-id-12345', name: 'Test', status: 'ok' },
    ];

    const { lastFrame } = render(
      <DataTable columns={testColumns} data={longData} />
    );

    const frame = lastFrame() || '';
    expect(frame).toContain('..');
  });
});
