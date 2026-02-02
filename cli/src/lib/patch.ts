/**
 * Update management module
 *
 * Handles checking for updates using the MCP server.
 */

import { getMCPClient } from './mcp-client.js';

export interface ComponentVersions {
  backend: string;
  frontend: string;
  api: string;
}

export interface UpdateCheckResult {
  success: boolean;
  components?: ComponentVersions;
  latest_version?: string;
  update_available: boolean;
  release_url?: string;
  release_notes?: string;
  message?: string;
  error?: string;
}

interface UpdateData {
  components: Record<string, string>;
  latest_version?: string;
  update_available: boolean;
  release_url?: string;
  release_notes?: string;
  message?: string;
}

interface VersionsData {
  backend: string;
  frontend: string;
  api: string;
  components: Record<string, { version: string; updated_at: string }>;
}

/**
 * Get current component versions via MCP
 */
export async function getComponentVersions(): Promise<ComponentVersions> {
  const client = getMCPClient();
  const response = await client.callTool<VersionsData>('get_component_versions');

  if (response.success && response.data) {
    return {
      backend: response.data.backend,
      frontend: response.data.frontend,
      api: response.data.api
    };
  }

  return {
    backend: '1.0.0',
    frontend: '1.0.0',
    api: '1.0.0'
  };
}

/**
 * Check for updates from GitHub releases via MCP
 */
export async function checkForUpdates(): Promise<UpdateCheckResult> {
  const client = getMCPClient();
  const response = await client.callTool<UpdateData>('check_updates');

  if (response.success && response.data) {
    return {
      success: true,
      components: {
        backend: response.data.components.backend || '1.0.0',
        frontend: response.data.components.frontend || '1.0.0',
        api: response.data.components.api || '1.0.0'
      },
      latest_version: response.data.latest_version,
      update_available: response.data.update_available,
      release_url: response.data.release_url,
      release_notes: response.data.release_notes,
      message: response.data.message
    };
  }

  return {
    success: false,
    update_available: false,
    error: response.error || 'Failed to check for updates'
  };
}
