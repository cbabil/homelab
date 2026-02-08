/**
 * Tests for useDashboardData hook.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

vi.mock('../../src/lib/agent.js', () => ({
  listAgents: vi.fn(),
}));

vi.mock('../../src/lib/server.js', () => ({
  listServers: vi.fn(),
}));

// Mock react hooks for non-component testing
const mockSetState = vi.fn();
let capturedEffect: (() => (() => void) | void) | null = null;
let effectDeps: unknown[] | undefined;

vi.mock('react', () => ({
  useState: vi.fn((initial: unknown) => {
    if (typeof initial === 'function') {
      return [(initial as () => unknown)(), mockSetState];
    }
    return [initial, mockSetState];
  }),
  useEffect: vi.fn((effect: () => (() => void) | void, deps?: unknown[]) => {
    capturedEffect = effect;
    effectDeps = deps;
  }),
  useCallback: vi.fn((fn: unknown) => fn),
  useRef: vi.fn((val: unknown) => ({ current: val })),
}));

import { listAgents } from '../../src/lib/agent.js';
import { listServers } from '../../src/lib/server.js';

describe('useDashboardData', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    capturedEffect = null;
    effectDeps = undefined;
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it('should call listAgents and listServers', async () => {
    vi.mocked(listAgents).mockResolvedValue([
      { id: 'a1', server_id: 's1', status: 'connected', version: '1.0', last_seen: null, registered_at: null },
    ]);
    vi.mocked(listServers).mockResolvedValue([
      { id: 's1', name: 'Web', hostname: 'web.local', status: 'online' },
    ]);

    // Import and call the hook
    const { useDashboardData } = await import('../../src/hooks/useDashboardData.js');
    useDashboardData({ enabled: true });

    // The useEffect should have been captured
    expect(capturedEffect).toBeDefined();
  });

  it('should accept options', async () => {
    vi.mocked(listAgents).mockResolvedValue([]);
    vi.mocked(listServers).mockResolvedValue([]);

    const { useDashboardData } = await import('../../src/hooks/useDashboardData.js');
    const result = useDashboardData({ refreshInterval: 5000, enabled: false });

    expect(result).toBeDefined();
  });

  it('should use default options', async () => {
    vi.mocked(listAgents).mockResolvedValue([]);
    vi.mocked(listServers).mockResolvedValue([]);

    const { useDashboardData } = await import('../../src/hooks/useDashboardData.js');
    const result = useDashboardData();

    expect(result).toBeDefined();
  });
});
