/**
 * Tests for StatusBar component.
 */

import { describe, it, expect } from 'vitest';
import { render } from 'ink-testing-library';
import React from 'react';
import { StatusBar } from '../../src/app/StatusBar.js';

describe('StatusBar', () => {
  describe('connection status', () => {
    it('should show Connected when mcpConnected is true', () => {
      const { lastFrame } = render(
        <StatusBar
          mcpConnected={true}
          mcpConnecting={false}
          mcpError={null}
          authenticated={false}
          username={null}
          isRunningCommand={false}
        />
      );

      expect(lastFrame()).toContain('Connected');
    });

    it('should show Connecting when mcpConnecting is true', () => {
      const { lastFrame } = render(
        <StatusBar
          mcpConnected={false}
          mcpConnecting={true}
          mcpError={null}
          authenticated={false}
          username={null}
          isRunningCommand={false}
        />
      );

      expect(lastFrame()).toContain('Connecting');
    });

    it('should show Disconnected when not connected', () => {
      const { lastFrame } = render(
        <StatusBar
          mcpConnected={false}
          mcpConnecting={false}
          mcpError={null}
          authenticated={false}
          username={null}
          isRunningCommand={false}
        />
      );

      expect(lastFrame()).toContain('Disconnected');
    });

    it('should show error message when mcpError is set', () => {
      const { lastFrame } = render(
        <StatusBar
          mcpConnected={false}
          mcpConnecting={false}
          mcpError="Connection refused"
          authenticated={false}
          username={null}
          isRunningCommand={false}
        />
      );

      expect(lastFrame()).toContain('Connection refused');
    });
  });

  describe('auth status', () => {
    it('should show username when authenticated', () => {
      const { lastFrame } = render(
        <StatusBar
          mcpConnected={true}
          mcpConnecting={false}
          mcpError={null}
          authenticated={true}
          username="admin"
          isRunningCommand={false}
        />
      );

      expect(lastFrame()).toContain('admin');
    });

    it('should show Not authenticated when not logged in', () => {
      const { lastFrame } = render(
        <StatusBar
          mcpConnected={true}
          mcpConnecting={false}
          mcpError={null}
          authenticated={false}
          username={null}
          isRunningCommand={false}
        />
      );

      expect(lastFrame()).toContain('Not authenticated');
    });
  });

  describe('command status', () => {
    it('should show Running when isRunningCommand is true', () => {
      const { lastFrame } = render(
        <StatusBar
          mcpConnected={true}
          mcpConnecting={false}
          mcpError={null}
          authenticated={true}
          username="admin"
          isRunningCommand={true}
        />
      );

      expect(lastFrame()).toContain('Running');
    });

    it('should not show Running when isRunningCommand is false', () => {
      const { lastFrame } = render(
        <StatusBar
          mcpConnected={true}
          mcpConnecting={false}
          mcpError={null}
          authenticated={true}
          username="admin"
          isRunningCommand={false}
        />
      );

      expect(lastFrame()).not.toContain('Running');
    });
  });

  describe('keyboard hints', () => {
    it('should show help hint', () => {
      const { lastFrame } = render(
        <StatusBar
          mcpConnected={true}
          mcpConnecting={false}
          mcpError={null}
          authenticated={false}
          username={null}
          isRunningCommand={false}
        />
      );

      expect(lastFrame()).toContain('/help');
    });

    it('should show quit hint', () => {
      const { lastFrame } = render(
        <StatusBar
          mcpConnected={true}
          mcpConnecting={false}
          mcpError={null}
          authenticated={false}
          username={null}
          isRunningCommand={false}
        />
      );

      expect(lastFrame()).toContain('/quit');
    });
  });
});
