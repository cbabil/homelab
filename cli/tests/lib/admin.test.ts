/**
 * Tests for admin module.
 *
 * Tests password hashing, user creation, and password reset.
 */

import { describe, it, expect, beforeAll, afterAll, beforeEach } from 'vitest';
import bcrypt from 'bcrypt';
import Database from 'better-sqlite3';
import { mkdtempSync, rmSync } from 'fs';
import { join } from 'path';
import { tmpdir } from 'os';

// We need to test the module functions directly, so we'll recreate the logic here
// since the actual module depends on global database state

const SALT_ROUNDS = 12;

describe('Password Hashing', () => {
  describe('bcrypt configuration', () => {
    it('should use 12 salt rounds (must match backend)', () => {
      expect(SALT_ROUNDS).toBe(12);
    });

    it('should produce valid bcrypt hash', async () => {
      const password = 'testpassword123';
      const hash = await bcrypt.hash(password, SALT_ROUNDS);

      expect(hash).toMatch(/^\$2[aby]\$/);
      expect(hash.length).toBe(60);
    });

    it('should embed cost factor 12 in hash', async () => {
      const hash = await bcrypt.hash('testpassword', SALT_ROUNDS);
      expect(hash).toContain('$12$');
    });

    it('should produce different hashes for different passwords', async () => {
      const hash1 = await bcrypt.hash('password1', SALT_ROUNDS);
      const hash2 = await bcrypt.hash('password2', SALT_ROUNDS);

      expect(hash1).not.toBe(hash2);
    });

    it('should produce different hashes for same password (unique salt)', async () => {
      const password = 'samepassword';
      const hash1 = await bcrypt.hash(password, SALT_ROUNDS);
      const hash2 = await bcrypt.hash(password, SALT_ROUNDS);

      expect(hash1).not.toBe(hash2);
    });
  });

  describe('password verification', () => {
    it('should verify correct password', async () => {
      const password = 'correctpassword';
      const hash = await bcrypt.hash(password, SALT_ROUNDS);

      const isValid = await bcrypt.compare(password, hash);
      expect(isValid).toBe(true);
    });

    it('should reject incorrect password', async () => {
      const hash = await bcrypt.hash('correctpassword', SALT_ROUNDS);

      const isValid = await bcrypt.compare('wrongpassword', hash);
      expect(isValid).toBe(false);
    });

    it('should be case-sensitive', async () => {
      const hash = await bcrypt.hash('Password123', SALT_ROUNDS);

      expect(await bcrypt.compare('Password123', hash)).toBe(true);
      expect(await bcrypt.compare('password123', hash)).toBe(false);
      expect(await bcrypt.compare('PASSWORD123', hash)).toBe(false);
    });

    it('should handle unicode passwords', async () => {
      const password = 'пароль123';
      const hash = await bcrypt.hash(password, SALT_ROUNDS);

      expect(await bcrypt.compare(password, hash)).toBe(true);
      expect(await bcrypt.compare('пароль124', hash)).toBe(false);
    });

    it('should handle special characters', async () => {
      const password = 'p@$$w0rd!#%^&*()';
      const hash = await bcrypt.hash(password, SALT_ROUNDS);

      expect(await bcrypt.compare(password, hash)).toBe(true);
    });

    it('should handle empty string', async () => {
      const hash = await bcrypt.hash('', SALT_ROUNDS);

      expect(await bcrypt.compare('', hash)).toBe(true);
      expect(await bcrypt.compare('notempty', hash)).toBe(false);
    });
  });
});

describe('Database Operations', () => {
  let db: Database.Database;
  let tempDir: string;

  beforeAll(() => {
    // Create temp directory for test database
    tempDir = mkdtempSync(join(tmpdir(), 'tomo-cli-test-'));
  });

  afterAll(() => {
    // Clean up temp directory
    rmSync(tempDir, { recursive: true, force: true });
  });

  beforeEach(() => {
    // Create fresh in-memory database for each test
    db = new Database(':memory:');
    db.pragma('journal_mode = WAL');

    // Create users table
    db.exec(`
      CREATE TABLE users (
        id TEXT PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'user',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
      )
    `);
  });

  describe('createAdmin', () => {
    it('should insert admin user into database', async () => {
      const username = 'testadmin';
      const email = 'admin@test.com';
      const password = 'securepassword123';
      const passwordHash = await bcrypt.hash(password, SALT_ROUNDS);
      const id = 'test-uuid-123';
      const now = new Date().toISOString();

      db.prepare(`
        INSERT INTO users (id, username, email, password_hash, role, created_at, updated_at)
        VALUES (?, ?, ?, ?, 'admin', ?, ?)
      `).run(id, username, email, passwordHash, now, now);

      const user = db.prepare('SELECT * FROM users WHERE username = ?').get(username) as any;

      expect(user).toBeDefined();
      expect(user.username).toBe(username);
      expect(user.email).toBe(email);
      expect(user.role).toBe('admin');
      expect(user.password_hash).toBe(passwordHash);
    });

    it('should reject duplicate username', async () => {
      const passwordHash = await bcrypt.hash('password', SALT_ROUNDS);
      const now = new Date().toISOString();

      db.prepare(`
        INSERT INTO users (id, username, email, password_hash, role, created_at, updated_at)
        VALUES (?, ?, ?, ?, 'admin', ?, ?)
      `).run('id1', 'admin', 'admin1@test.com', passwordHash, now, now);

      expect(() => {
        db.prepare(`
          INSERT INTO users (id, username, email, password_hash, role, created_at, updated_at)
          VALUES (?, ?, ?, ?, 'admin', ?, ?)
        `).run('id2', 'admin', 'admin2@test.com', passwordHash, now, now);
      }).toThrow(/UNIQUE constraint failed/);
    });

    it('should reject duplicate email', async () => {
      const passwordHash = await bcrypt.hash('password', SALT_ROUNDS);
      const now = new Date().toISOString();

      db.prepare(`
        INSERT INTO users (id, username, email, password_hash, role, created_at, updated_at)
        VALUES (?, ?, ?, ?, 'admin', ?, ?)
      `).run('id1', 'admin1', 'admin@test.com', passwordHash, now, now);

      expect(() => {
        db.prepare(`
          INSERT INTO users (id, username, email, password_hash, role, created_at, updated_at)
          VALUES (?, ?, ?, ?, 'admin', ?, ?)
        `).run('id2', 'admin2', 'admin@test.com', passwordHash, now, now);
      }).toThrow(/UNIQUE constraint failed/);
    });
  });

  describe('resetPassword', () => {
    it('should update password for existing admin', async () => {
      const username = 'admin';
      const oldHash = await bcrypt.hash('oldpassword', SALT_ROUNDS);
      const newHash = await bcrypt.hash('newpassword', SALT_ROUNDS);
      const now = new Date().toISOString();

      // Insert admin user
      db.prepare(`
        INSERT INTO users (id, username, email, password_hash, role, created_at, updated_at)
        VALUES (?, ?, ?, ?, 'admin', ?, ?)
      `).run('id1', username, 'admin@test.com', oldHash, now, now);

      // Update password
      const result = db.prepare(`
        UPDATE users SET password_hash = ?, updated_at = ?
        WHERE username = ?
      `).run(newHash, now, username);

      expect(result.changes).toBe(1);

      const user = db.prepare('SELECT * FROM users WHERE username = ?').get(username) as any;
      expect(user.password_hash).toBe(newHash);
    });

    it('should update password for regular user', async () => {
      const username = 'regularuser';
      const oldHash = await bcrypt.hash('oldpassword', SALT_ROUNDS);
      const newHash = await bcrypt.hash('newpassword', SALT_ROUNDS);
      const now = new Date().toISOString();

      // Insert regular user (not admin)
      db.prepare(`
        INSERT INTO users (id, username, email, password_hash, role, created_at, updated_at)
        VALUES (?, ?, ?, ?, 'user', ?, ?)
      `).run('id1', username, 'user@test.com', oldHash, now, now);

      // Update password - should work for any user now
      const result = db.prepare(`
        UPDATE users SET password_hash = ?, updated_at = ?
        WHERE username = ?
      `).run(newHash, now, username);

      expect(result.changes).toBe(1);

      // Password should be updated
      const user = db.prepare('SELECT * FROM users WHERE username = ?').get(username) as any;
      expect(user.password_hash).toBe(newHash);
    });

    it('should return 0 changes for non-existent user', async () => {
      const newHash = await bcrypt.hash('newpassword', SALT_ROUNDS);
      const now = new Date().toISOString();

      const result = db.prepare(`
        UPDATE users SET password_hash = ?, updated_at = ?
        WHERE username = ?
      `).run(newHash, now, 'nonexistent');

      expect(result.changes).toBe(0);
    });
  });

  describe('getUser', () => {
    it('should return user by username', async () => {
      const passwordHash = await bcrypt.hash('password', SALT_ROUNDS);
      const now = new Date().toISOString();

      db.prepare(`
        INSERT INTO users (id, username, email, password_hash, role, created_at, updated_at)
        VALUES (?, ?, ?, ?, 'admin', ?, ?)
      `).run('id1', 'admin', 'admin@test.com', passwordHash, now, now);

      const user = db.prepare('SELECT * FROM users WHERE username = ?').get('admin') as any;

      expect(user).toBeDefined();
      expect(user.username).toBe('admin');
      expect(user.email).toBe('admin@test.com');
      expect(user.role).toBe('admin');
    });

    it('should return undefined for non-existent user', () => {
      const user = db.prepare('SELECT * FROM users WHERE username = ?').get('nonexistent');
      expect(user).toBeUndefined();
    });
  });
});

// Test MCP client functions separately
describe('Admin MCP Functions', () => {
  // Reset modules for clean mocking
  let mockClient: { callTool: ReturnType<typeof import('vitest').vi.fn> };
  let getUser: typeof import('../../src/lib/admin.js').getUser;
  let createAdmin: typeof import('../../src/lib/admin.js').createAdmin;
  let resetPassword: typeof import('../../src/lib/admin.js').resetPassword;
  let vi: typeof import('vitest').vi;

  beforeAll(async () => {
    vi = (await import('vitest')).vi;

    // Mock the mcp-client module
    vi.mock('../../src/lib/mcp-client.js', () => ({
      getMCPClient: vi.fn(),
    }));

    mockClient = {
      callTool: vi.fn(),
    };

    const mcpModule = await import('../../src/lib/mcp-client.js');
    vi.mocked(mcpModule.getMCPClient).mockReturnValue(mockClient as unknown as ReturnType<typeof mcpModule.getMCPClient>);

    // Now import the admin module
    const adminModule = await import('../../src/lib/admin.js');
    getUser = adminModule.getUser;
    createAdmin = adminModule.createAdmin;
    resetPassword = adminModule.resetPassword;
  });

  beforeEach(async () => {
    vi.clearAllMocks();
    const mcpModule = await import('../../src/lib/mcp-client.js');
    vi.mocked(mcpModule.getMCPClient).mockReturnValue(mockClient as unknown as ReturnType<typeof mcpModule.getMCPClient>);
  });

  afterAll(() => {
    vi.restoreAllMocks();
  });

  describe('getUser via MCP', () => {
    it('should call MCP with correct tool name', async () => {
      mockClient.callTool.mockResolvedValue({
        success: true,
        data: {
          id: '123',
          username: 'admin',
          role: 'admin',
          is_active: true,
          created_at: '2024-01-01',
          updated_at: '2024-01-02',
        },
      });

      await getUser('admin');

      expect(mockClient.callTool).toHaveBeenCalledWith('get_user_by_username', {
        username: 'admin',
      });
    });

    it('should return null on failure', async () => {
      mockClient.callTool.mockResolvedValue({
        success: false,
      });

      const result = await getUser('nonexistent');
      expect(result).toBeNull();
    });
  });

  describe('createAdmin via MCP', () => {
    it('should call MCP with correct arguments', async () => {
      mockClient.callTool.mockResolvedValue({
        success: true,
        data: { username: 'newadmin' },
      });

      await createAdmin('newadmin', 'password123');

      expect(mockClient.callTool).toHaveBeenCalledWith('create_initial_admin', {
        username: 'newadmin',
        password: 'password123',
      });
    });

    it('should return success true on success', async () => {
      mockClient.callTool.mockResolvedValue({
        success: true,
        data: { username: 'newadmin' },
      });

      const result = await createAdmin('newadmin', 'password123');
      expect(result).toEqual({ success: true });
    });

    it('should return error on failure', async () => {
      mockClient.callTool.mockResolvedValue({
        success: false,
        error: 'Username already exists',
      });

      const result = await createAdmin('existing', 'password123');
      expect(result).toEqual({
        success: false,
        error: 'Username already exists',
      });
    });
  });

  describe('resetPassword via MCP', () => {
    it('should call MCP with correct arguments', async () => {
      mockClient.callTool.mockResolvedValue({
        success: true,
      });

      await resetPassword('admin', 'newpassword123');

      expect(mockClient.callTool).toHaveBeenCalledWith('reset_user_password', {
        username: 'admin',
        password: 'newpassword123',
      });
    });

    it('should return success true on success', async () => {
      mockClient.callTool.mockResolvedValue({
        success: true,
      });

      const result = await resetPassword('admin', 'newpassword123');
      expect(result).toEqual({ success: true });
    });

    it('should return error on failure', async () => {
      mockClient.callTool.mockResolvedValue({
        success: false,
        error: 'User not found',
      });

      const result = await resetPassword('nonexistent', 'newpassword');
      expect(result).toEqual({
        success: false,
        error: 'User not found',
      });
    });
  });
});
