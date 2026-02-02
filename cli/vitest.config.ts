import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    globals: true,
    environment: 'node',
    include: ['tests/**/*.test.{ts,tsx}'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html'],
      exclude: [
        'node_modules',
        'dist',
        'tests/**/*.test.{ts,tsx}',
        'src/bin/tomo.tsx', // Entry point tested via integration tests
        '**/index.ts', // Re-export files
        'vitest.config.ts',
      ],
    },
  },
});
