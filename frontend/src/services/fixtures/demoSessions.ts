/**
 * Demo session data for development/testing when no stored sessions exist.
 * Extracted from sessionManager to keep production code clean.
 */

import type { SessionListEntry } from '../sessionManager';

export function createDemoSessions(): SessionListEntry[] {
  const now = new Date();

  return [
    {
      id: '****8b9c',
      sessionId: 'sess_1703856000000_8b9c1234',
      userId: 'demo-user',
      status: 'idle',
      started: new Date(now.getTime() - 2 * 60 * 60 * 1000),
      lastActivity: new Date(now.getTime() - 15 * 60 * 1000),
      location: 'Chrome 120 on macOS 14.1',
      ip: '192.168.1.100',
      deviceInfo: {
        browser: 'Chrome',
        browserVersion: '120.0',
        os: 'macOS',
        osVersion: '14.1',
        deviceType: 'desktop',
        isMobile: false,
      },
      locationInfo: {
        country: 'US',
        region: 'CA',
        city: 'San Francisco',
        timezone: 'America/Los_Angeles',
      },
      activity: {
        pageViews: 25,
        keystrokes: 450,
        mouseClicks: 120,
        idleTime: 15 * 60 * 1000,
        lastActiveTab: 'Dashboard',
      },
      isCurrentSession: false,
      duration: 2 * 60 * 60 * 1000,
    },
    {
      id: '****3d2f',
      sessionId: 'sess_1703769600000_3d2f5678',
      userId: 'demo-user',
      status: 'expired',
      started: new Date(now.getTime() - 24 * 60 * 60 * 1000),
      lastActivity: new Date(now.getTime() - 8 * 60 * 60 * 1000),
      location: 'Firefox 121 on Windows 11',
      ip: '192.168.1.150',
      deviceInfo: {
        browser: 'Firefox',
        browserVersion: '121.0',
        os: 'Windows',
        osVersion: '11',
        deviceType: 'desktop',
        isMobile: false,
      },
      locationInfo: {
        country: 'US',
        region: 'NY',
        city: 'New York',
        timezone: 'America/New_York',
      },
      activity: {
        pageViews: 45,
        keystrokes: 890,
        mouseClicks: 220,
        idleTime: 8 * 60 * 60 * 1000,
        lastActiveTab: 'Settings',
      },
      isCurrentSession: false,
      duration: 16 * 60 * 60 * 1000,
    },
    {
      id: '****9a7e',
      sessionId: 'sess_1703852400000_9a7e9012',
      userId: 'demo-user',
      status: 'active',
      started: new Date(now.getTime() - 45 * 60 * 1000),
      lastActivity: new Date(now.getTime() - 2 * 60 * 1000),
      location: 'Safari 17 on iPhone 15',
      ip: '10.0.1.50',
      deviceInfo: {
        browser: 'Safari',
        browserVersion: '17.0',
        os: 'iOS',
        osVersion: '17.2',
        deviceType: 'mobile',
        isMobile: true,
      },
      locationInfo: {
        country: 'US',
        region: 'CA',
        city: 'Los Angeles',
        timezone: 'America/Los_Angeles',
      },
      activity: {
        pageViews: 12,
        keystrokes: 180,
        mouseClicks: 65,
        idleTime: 2 * 60 * 1000,
        lastActiveTab: 'Logs',
      },
      isCurrentSession: false,
      duration: 43 * 60 * 1000,
    },
  ];
}
