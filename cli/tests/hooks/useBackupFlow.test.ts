/**
 * Tests for useBackupFlow hook.
 *
 * Uses a manual React useState mock with index-based state tracking.
 * IMPORTANT: The state slot order must match the useState declarations
 * in useBackupFlow.ts (step=0, path=1, overwrite=2). If the hook's
 * state declarations are reordered, these tests will silently break.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

vi.mock('../../src/lib/backup.js', () => ({
  exportBackup: vi.fn(),
  importBackup: vi.fn(),
}));

vi.mock('../../src/lib/validation.js', () => ({
  validatePassword: vi.fn(),
}));

// Manual React hook mock — tracks state by declaration order.
// See file header for coupling risk.
const stateStore = new Map<number, unknown>();
let stateIdx = 0;

vi.mock('react', () => ({
  useState: vi.fn((initial: unknown) => {
    const idx = stateIdx++;
    if (!stateStore.has(idx)) {
      stateStore.set(idx, initial);
    }
    const setter = (val: unknown) => {
      stateStore.set(idx, val);
    };
    return [stateStore.get(idx), setter];
  }),
  useCallback: vi.fn((fn: unknown) => fn),
}));

import { exportBackup, importBackup } from '../../src/lib/backup.js';
import { validatePassword } from '../../src/lib/validation.js';

describe('useBackupFlow', () => {
  let addActivity: ReturnType<typeof vi.fn>;
  let setInputValue: ReturnType<typeof vi.fn>;
  let setRunning: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    vi.clearAllMocks();
    stateStore.clear();
    stateIdx = 0;
    addActivity = vi.fn();
    setInputValue = vi.fn();
    setRunning = vi.fn();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  async function getHook() {
    stateIdx = 0;
    const { useBackupFlow } = await import('../../src/hooks/useBackupFlow.js');
    return useBackupFlow({ addActivity, setInputValue, setRunning });
  }

  describe('initial state', () => {
    it('should not be active initially', async () => {
      const flow = await getHook();

      expect(flow.isActive).toBe(false);
      expect(flow.step).toBeNull();
      expect(flow.promptLabel).toBeUndefined();
      expect(flow.promptMask).toBe(false);
    });
  });

  describe('password validation', () => {
    it('should reject weak password and show error', async () => {
      vi.mocked(validatePassword).mockReturnValue({
        valid: false,
        error: 'Password must be at least 12 characters',
      });

      const flow = await getHook();
      await flow.handleSubmit('weak');

      expect(addActivity).toHaveBeenCalledWith(
        'ERR',
        'Password must be at least 12 characters'
      );
      expect(setInputValue).toHaveBeenCalledWith('');
    });

    it('should reject empty password', async () => {
      vi.mocked(validatePassword).mockReturnValue({
        valid: false,
        error: 'Password is required',
      });

      const flow = await getHook();
      await flow.handleSubmit('');

      expect(addActivity).toHaveBeenCalledWith('ERR', 'Password is required');
      expect(setInputValue).toHaveBeenCalledWith('');
    });

    it('should not call export or import when password is invalid', async () => {
      vi.mocked(validatePassword).mockReturnValue({
        valid: false,
        error: 'Password must contain a number',
      });

      const flow = await getHook();
      await flow.handleSubmit('NoNumberHere!!');

      expect(exportBackup).not.toHaveBeenCalled();
      expect(importBackup).not.toHaveBeenCalled();
      expect(setRunning).not.toHaveBeenCalled();
    });

    it('should use fallback error when validation error is undefined', async () => {
      vi.mocked(validatePassword).mockReturnValue({
        valid: false,
      });

      const flow = await getHook();
      await flow.handleSubmit('bad');

      expect(addActivity).toHaveBeenCalledWith('ERR', 'Invalid password');
    });
  });

  describe('export flow', () => {
    it('should call exportBackup with valid password', async () => {
      vi.mocked(validatePassword).mockReturnValue({ valid: true });
      vi.mocked(exportBackup).mockResolvedValue({
        success: true,
        path: '/tmp/backup.enc',
        checksum: 'abc123',
      });

      const flow = await getHook();
      flow.startExport('/tmp/backup.enc');

      // Re-render to pick up state change
      const flow2 = await getHook();
      await flow2.handleSubmit('MyStr0ngP@ss!x');

      expect(exportBackup).toHaveBeenCalledWith('/tmp/backup.enc', 'MyStr0ngP@ss!x');
      expect(setRunning).toHaveBeenCalledWith(true);
    });

    it('should show error when exportBackup fails', async () => {
      vi.mocked(validatePassword).mockReturnValue({ valid: true });
      vi.mocked(exportBackup).mockResolvedValue({
        success: false,
        error: 'Disk full',
      });

      const flow = await getHook();
      flow.startExport('/tmp/backup.enc');

      const flow2 = await getHook();
      await flow2.handleSubmit('MyStr0ngP@ss!x');

      expect(addActivity).toHaveBeenCalledWith('ERR', 'Disk full');
      expect(setRunning).toHaveBeenCalledWith(false);
    });

    it('should show error when exportBackup throws', async () => {
      vi.mocked(validatePassword).mockReturnValue({ valid: true });
      vi.mocked(exportBackup).mockRejectedValue(new Error('Network error'));

      const flow = await getHook();
      flow.startExport('/tmp/backup.enc');

      const flow2 = await getHook();
      await flow2.handleSubmit('MyStr0ngP@ss!x');

      expect(addActivity).toHaveBeenCalledWith('ERR', 'Network error');
      expect(setRunning).toHaveBeenCalledWith(false);
    });
  });

  describe('import flow', () => {
    it('should call importBackup with valid password', async () => {
      vi.mocked(validatePassword).mockReturnValue({ valid: true });
      vi.mocked(importBackup).mockResolvedValue({
        success: true,
        users_imported: 5,
        servers_imported: 3,
      });

      const flow = await getHook();
      flow.startImport('/tmp/backup.enc', false);

      const flow2 = await getHook();
      await flow2.handleSubmit('MyStr0ngP@ss!x');

      expect(importBackup).toHaveBeenCalledWith('/tmp/backup.enc', 'MyStr0ngP@ss!x', false);
    });

    it('should show error when importBackup fails', async () => {
      vi.mocked(validatePassword).mockReturnValue({ valid: true });
      vi.mocked(importBackup).mockResolvedValue({
        success: false,
        error: 'Invalid backup file',
      });

      const flow = await getHook();
      flow.startImport('/tmp/backup.enc', false);

      const flow2 = await getHook();
      await flow2.handleSubmit('MyStr0ngP@ss!x');

      expect(addActivity).toHaveBeenCalledWith('ERR', 'Invalid backup file');
      expect(setRunning).toHaveBeenCalledWith(false);
    });

    it('should show error when importBackup throws', async () => {
      vi.mocked(validatePassword).mockReturnValue({ valid: true });
      vi.mocked(importBackup).mockRejectedValue(new Error('Corrupted file'));

      const flow = await getHook();
      flow.startImport('/tmp/backup.enc', false);

      const flow2 = await getHook();
      await flow2.handleSubmit('MyStr0ngP@ss!x');

      expect(addActivity).toHaveBeenCalledWith('ERR', 'Corrupted file');
      expect(setRunning).toHaveBeenCalledWith(false);
    });
  });
});
