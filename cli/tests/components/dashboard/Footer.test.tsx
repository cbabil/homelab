/**
 * Tests for Footer component.
 */

import { describe, it, expect } from 'vitest';
import { render } from 'ink-testing-library';
import React from 'react';
import { Footer } from '../../../src/components/dashboard/Footer.js';

describe('Footer', () => {
  it('should render version', () => {
    const { lastFrame } = render(
      <Footer
        version="0.1.0"
        mcpUrl="http://localhost:8000/mcp"
        connectionStatus="connected"
      />
    );

    expect(lastFrame()).toContain('VERSION: 0.1.0');
  });

  it('should render MCP URL', () => {
    const { lastFrame } = render(
      <Footer
        version="0.1.0"
        mcpUrl="http://localhost:8000/mcp"
        connectionStatus="connected"
      />
    );

    expect(lastFrame()).toContain('MCP: http://localhost:8000/mcp');
  });

  it('should show connected status', () => {
    const { lastFrame } = render(
      <Footer
        version="0.1.0"
        mcpUrl="http://localhost:8000/mcp"
        connectionStatus="connected"
      />
    );

    expect(lastFrame()).toContain('Connected');
  });

  it('should show disconnected status', () => {
    const { lastFrame } = render(
      <Footer
        version="0.1.0"
        mcpUrl="http://localhost:8000/mcp"
        connectionStatus="disconnected"
      />
    );

    expect(lastFrame()).toContain('Disconnected');
  });

  it('should show connecting status', () => {
    const { lastFrame } = render(
      <Footer
        version="0.1.0"
        mcpUrl="http://localhost:8000/mcp"
        connectionStatus="connecting"
      />
    );

    expect(lastFrame()).toContain('Connecting');
  });
});
