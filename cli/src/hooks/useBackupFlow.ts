/**
 * Hook for the backup export/import prompt flow.
 */

import { useState, useCallback } from 'react';
import { exportBackup, importBackup } from '../lib/backup.js';
import type { ActivityEntry } from '../app/dashboard-types.js';
import { validatePassword } from '../lib/validation.js';

type BackupStep = 'export-password' | 'import-password' | null;

interface BackupFlowOptions {
  addActivity: (type: ActivityEntry['type'], message: string) => void;
  setInputValue: (value: string) => void;
  setRunning: (running: boolean) => void;
}

export function useBackupFlow({
  addActivity,
  setInputValue,
  setRunning,
}: BackupFlowOptions) {
  const [step, setStep] = useState<BackupStep>(null);
  const [path, setPath] = useState('');
  const [overwrite, setOverwrite] = useState(false);

  const startExport = useCallback((exportPath: string) => {
    setPath(exportPath);
    setStep('export-password');
  }, []);

  const startImport = useCallback((importPath: string, withOverwrite: boolean) => {
    setPath(importPath);
    setOverwrite(withOverwrite);
    setStep('import-password');
  }, []);

  const handleSubmit = useCallback(
    async (input: string) => {
      const validation = validatePassword(input);
      if (!validation.valid) {
        addActivity('ERR', validation.error || 'Invalid password');
        setInputValue('');
        return;
      }

      setInputValue('');
      setRunning(true);

      if (step === 'export-password') {
        addActivity('SYS', `Exporting backup to ${path}...`);
        try {
          const result = await exportBackup(path, input);
          if (result.success) {
            addActivity('OK', `Backup exported to ${result.path || path}`);
            if (result.checksum) {
              addActivity('SYS', `Checksum: ${result.checksum}`);
            }
          } else {
            addActivity('ERR', result.error || 'Failed to export backup');
          }
        } catch (err) {
          const msg = err instanceof Error ? err.message : 'Failed to export backup';
          addActivity('ERR', msg);
        } finally {
          setRunning(false);
          setStep(null);
          setPath('');
        }
        return;
      }

      if (step === 'import-password') {
        addActivity('SYS', `Importing backup from ${path}...`);
        try {
          const result = await importBackup(path, input, overwrite);
          if (result.success) {
            addActivity('OK', `Backup imported from ${path}`);
            if (result.users_imported !== undefined) {
              addActivity('SYS', `Users: ${result.users_imported}, Servers: ${result.servers_imported}`);
            }
          } else {
            addActivity('ERR', result.error || 'Failed to import backup');
          }
        } catch (err) {
          const msg = err instanceof Error ? err.message : 'Failed to import backup';
          addActivity('ERR', msg);
        } finally {
          setRunning(false);
          setStep(null);
          setPath('');
          setOverwrite(false);
        }
      }
    },
    [step, path, overwrite, addActivity, setInputValue, setRunning]
  );

  const promptLabel = step === 'export-password' ? 'Encryption password: '
    : step === 'import-password' ? 'Decryption password: '
    : undefined;

  return {
    step,
    startExport,
    startImport,
    handleSubmit,
    promptLabel,
    promptMask: step !== null,
    isActive: step !== null,
  };
}
