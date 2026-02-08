/**
 * Tests for SetupView component.
 */

import { describe, it, expect } from 'vitest';
import { render } from 'ink-testing-library';
import React from 'react';
import { SetupView } from '../../../src/app/views/SetupView.js';

describe('SetupView', () => {
  it('should render setup panel title', () => {
    const { lastFrame } = render(
      <SetupView step="username" username="" error={null} />
    );

    expect(lastFrame()).toContain('INITIAL_SETUP');
  });

  it('should show welcome message', () => {
    const { lastFrame } = render(
      <SetupView step="username" username="" error={null} />
    );

    const frame = lastFrame() || '';
    expect(frame).toContain('Welcome to Tomo');
    expect(frame).toContain('No admin account found');
  });

  it('should show step 1 for username', () => {
    const { lastFrame } = render(
      <SetupView step="username" username="" error={null} />
    );

    expect(lastFrame()).toContain('Step 1/3');
  });

  it('should show step 2 for password with username', () => {
    const { lastFrame } = render(
      <SetupView step="password" username="admin" error={null} />
    );

    const frame = lastFrame() || '';
    expect(frame).toContain('Step 2/3');
    expect(frame).toContain('admin');
  });

  it('should show password requirements on password step', () => {
    const { lastFrame } = render(
      <SetupView step="password" username="admin" error={null} />
    );

    const frame = lastFrame() || '';
    expect(frame).toContain('12 characters');
    expect(frame).toContain('uppercase');
    expect(frame).toContain('special character');
  });

  it('should show step 3 for confirm password', () => {
    const { lastFrame } = render(
      <SetupView step="confirmPassword" username="admin" error={null} />
    );

    expect(lastFrame()).toContain('Step 3/3');
  });

  it('should show creating state', () => {
    const { lastFrame } = render(
      <SetupView step="creating" username="admin" error={null} />
    );

    expect(lastFrame()).toContain('Creating admin account');
  });

  it('should show done state with username', () => {
    const { lastFrame } = render(
      <SetupView step="done" username="admin" error={null} />
    );

    const frame = lastFrame() || '';
    expect(frame).toContain('admin');
    expect(frame).toContain('created');
  });

  it('should show error state', () => {
    const { lastFrame } = render(
      <SetupView step="error" username="" error="Connection failed" />
    );

    const frame = lastFrame() || '';
    expect(frame).toContain('Setup failed');
    expect(frame).toContain('Connection failed');
  });
});
