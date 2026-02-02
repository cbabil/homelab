/**
 * Tests for useMCP hook using a wrapper component.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render } from 'ink-testing-library';
import React, { useEffect, useState } from 'react';
import { Text } from 'ink';
import type { MCPClient } from '../../src/lib/mcp-client.js';

// Mock the mcp-client module
vi.mock('../../src/lib/mcp-client.js', () => ({
  initMCPClient: vi.fn(),
  closeMCPClient: vi.fn(),
  getMCPClient: vi.fn(),
}));

import { useMCP } from '../../src/hooks/useMCP.js';
import {
  initMCPClient,
  closeMCPClient,
  getMCPClient,
} from '../../src/lib/mcp-client.js';

// Test wrapper component that uses the hook
function TestComponent({ mcpUrl }: { mcpUrl?: string }) {
  const { connected, connecting, error, callTool } = useMCP(mcpUrl);
  const [toolResult, setToolResult] = useState<string>('');

  useEffect(() => {
    if (connected) {
      callTool('test_tool', { arg: 'value' }).then((result) => {
        setToolResult(JSON.stringify(result));
      });
    }
  }, [connected, callTool]);

  if (connecting) {
    return <Text>Connecting...</Text>;
  }

  if (error) {
    return <Text>Error: {error}</Text>;
  }

  if (connected) {
    return (
      <Text>
        Connected{toolResult ? `: ${toolResult}` : ''}
      </Text>
    );
  }

  return <Text>Unknown</Text>;
}

describe('useMCP Hook', () => {
  let mockClient: Partial<MCPClient> & { callTool: ReturnType<typeof vi.fn> };

  beforeEach(() => {
    vi.clearAllMocks();
    mockClient = {
      callTool: vi.fn().mockResolvedValue({ success: true, data: { test: 'data' } }),
      connect: vi.fn(),
      disconnect: vi.fn(),
      isConnected: vi.fn().mockReturnValue(true),
    };
    vi.mocked(getMCPClient).mockReturnValue(mockClient as unknown as MCPClient);
  });

  it('should show connecting state initially', () => {
    vi.mocked(initMCPClient).mockReturnValue(new Promise(() => {}));

    const { lastFrame } = render(<TestComponent />);

    expect(lastFrame()).toContain('Connecting');
  });

  it('should show connected state after successful connection', async () => {
    vi.mocked(initMCPClient).mockResolvedValue(mockClient as unknown as MCPClient);

    const { lastFrame } = render(<TestComponent />);

    await vi.waitFor(() => {
      expect(lastFrame()).toContain('Connected');
    }, { timeout: 2000 });
  });

  it('should show error state after failed connection', async () => {
    vi.mocked(initMCPClient).mockRejectedValue(new Error('Connection failed'));

    const { lastFrame } = render(<TestComponent />);

    await vi.waitFor(() => {
      expect(lastFrame()).toContain('Error: Connection failed');
    }, { timeout: 2000 });
  });

  it('should call initMCPClient with provided URL', async () => {
    vi.mocked(initMCPClient).mockResolvedValue(mockClient as unknown as MCPClient);

    render(<TestComponent mcpUrl="http://custom:8000/mcp" />);

    await vi.waitFor(() => {
      expect(initMCPClient).toHaveBeenCalledWith('http://custom:8000/mcp');
    });
  });

  it('should call initMCPClient with default URL when not provided', async () => {
    vi.mocked(initMCPClient).mockResolvedValue(mockClient as unknown as MCPClient);

    render(<TestComponent />);

    await vi.waitFor(() => {
      expect(initMCPClient).toHaveBeenCalled();
    });
  });

  it('should close client on unmount', async () => {
    vi.mocked(initMCPClient).mockResolvedValue(mockClient as unknown as MCPClient);

    const { unmount } = render(<TestComponent />);

    await vi.waitFor(() => {
      expect(initMCPClient).toHaveBeenCalled();
    });

    unmount();

    expect(closeMCPClient).toHaveBeenCalled();
  });

  it('should provide working callTool function', async () => {
    vi.mocked(initMCPClient).mockResolvedValue(mockClient as unknown as MCPClient);

    const { lastFrame } = render(<TestComponent />);

    await vi.waitFor(() => {
      expect(lastFrame()).toContain('Connected');
    }, { timeout: 2000 });

    await vi.waitFor(() => {
      expect(mockClient.callTool).toHaveBeenCalledWith('test_tool', { arg: 'value' });
    }, { timeout: 2000 });
  });

  it('should handle callTool response', async () => {
    vi.mocked(initMCPClient).mockResolvedValue(mockClient as unknown as MCPClient);
    mockClient.callTool.mockResolvedValue({ success: true, data: { result: 'test' } });

    const { lastFrame } = render(<TestComponent />);

    await vi.waitFor(() => {
      expect(lastFrame()).toContain('success');
    }, { timeout: 2000 });
  });
});
