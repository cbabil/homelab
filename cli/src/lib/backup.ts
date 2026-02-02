/**
 * Backup management module
 *
 * Handles backup export and import operations via MCP server.
 */

import { getMCPClient } from './mcp-client.js';

export interface ExportResult {
  success: boolean;
  path?: string;
  checksum?: string;
  error?: string;
}

export interface ImportResult {
  success: boolean;
  users_imported?: number;
  servers_imported?: number;
  apps_imported?: number;
  error?: string;
}

interface ExportResponse {
  path: string;
  checksum: string;
}

interface ImportResponse {
  users_imported: number;
  servers_imported: number;
  apps_imported?: number;
}

/**
 * Export backup to encrypted file via MCP
 */
export async function exportBackup(
  outputPath: string,
  password: string
): Promise<ExportResult> {
  const client = getMCPClient();
  const response = await client.callTool<ExportResponse>('export_backup', {
    output_path: outputPath,
    password,
  });

  if (response.success && response.data) {
    return {
      success: true,
      path: response.data.path,
      checksum: response.data.checksum,
    };
  }

  return {
    success: false,
    error: response.error || response.message || 'Failed to export backup',
  };
}

/**
 * Import backup from encrypted file via MCP
 */
export async function importBackup(
  inputPath: string,
  password: string,
  overwrite: boolean = false
): Promise<ImportResult> {
  const client = getMCPClient();
  const response = await client.callTool<ImportResponse>('import_backup', {
    input_path: inputPath,
    password,
    overwrite,
  });

  if (response.success && response.data) {
    return {
      success: true,
      users_imported: response.data.users_imported,
      servers_imported: response.data.servers_imported,
      apps_imported: response.data.apps_imported,
    };
  }

  return {
    success: false,
    error: response.error || response.message || 'Failed to import backup',
  };
}
