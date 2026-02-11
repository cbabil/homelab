/**
 * Hook for the backup export/import prompt flow.
 */

import { useState, useCallback } from 'react';
import { exportBackup, importBackup } from '../lib/backup.js';
import type { ActivityEntry } from '../app/dashboard-types.js';
import { validatePassword } from '../lib/validation.js';
import { t } from '../i18n/index.js';

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
        addActivity('ERR', validation.error || t('validation.invalidPassword'));
        setInputValue('');
        return;
      }

      setInputValue('');
      setRunning(true);

      if (step === 'export-password') {
        addActivity('SYS', t('backup.exportingTo', { path }));
        try {
          const result = await exportBackup(path, input);
          if (result.success) {
            addActivity('OK', t('backup.exportSuccess', { path: result.path || path }));
            if (result.checksum) {
              addActivity('SYS', t('backup.checksumLabel', { checksum: result.checksum }));
            }
          } else {
            addActivity('ERR', result.error || t('backup.failedToExport'));
          }
        } catch (err) {
          const msg = err instanceof Error ? err.message : t('backup.failedToExport');
          addActivity('ERR', msg);
        } finally {
          setRunning(false);
          setStep(null);
          setPath('');
        }
        return;
      }

      if (step === 'import-password') {
        addActivity('SYS', t('backup.importingFrom', { path }));
        try {
          const result = await importBackup(path, input, overwrite);
          if (result.success) {
            addActivity('OK', t('backup.importSuccess', { path }));
            if (result.users_imported !== undefined) {
              addActivity('SYS', t('backup.importStats', { users: result.users_imported, servers: result.servers_imported }));
            }
          } else {
            addActivity('ERR', result.error || t('backup.failedToImport'));
          }
        } catch (err) {
          const msg = err instanceof Error ? err.message : t('backup.failedToImport');
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

  const promptLabel = step === 'export-password' ? t('prompts.encryptionPassword')
    : step === 'import-password' ? t('prompts.decryptionPassword')
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
