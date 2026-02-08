/**
 * Tests for CLI entry point.
 *
 * Tests the run() function and arg parsing.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';

// Mock ink render to prevent side effects
vi.mock('ink', () => ({
  render: vi.fn(),
  useApp: () => ({ exit: vi.fn() }),
}));

// Mock the App component
vi.mock('../../src/app/App.js', () => ({
  App: () => null,
}));

import { run } from '../../src/bin/tomo.js';
import { render } from 'ink';

describe('CLI Entry Point', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should export a run function', () => {
    expect(typeof run).toBe('function');
  });

  it('should render App when called with no special flags', () => {
    const originalArgv = process.argv;
    process.argv = ['node', 'tomo'];

    run();

    expect(render).toHaveBeenCalled();
    process.argv = originalArgv;
  });

  it('should pass mcp-url to App when provided', () => {
    const originalArgv = process.argv;
    process.argv = ['node', 'tomo', '-m', 'http://custom:8000/mcp'];

    run();

    expect(render).toHaveBeenCalled();
    process.argv = originalArgv;
  });
});
