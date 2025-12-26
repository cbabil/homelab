/**
 * User-Added Server Data
 * 
 * Servers added by users through the homelab interface.
 * 
 * To export your servers:
 * 1. Go to the Servers page
 * 2. Click the "Export" button to download a JSON file
 * 3. Save your server configurations for backup or sharing
 * 
 * To import servers:
 * 1. Go to the Servers page  
 * 2. Click the "Import" button to upload a JSON file
 * 3. Select your previously exported server configuration file
 */

import { ServerConnection } from '@/types/server'

export const userServers: ServerConnection[] = [
  // User-added servers will appear here when you add them through the UI
  // Use the Export/Import buttons in the Servers page to backup/restore your configurations
]