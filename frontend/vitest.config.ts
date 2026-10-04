import { defineConfig } from 'vitest/config'
import { resolve } from 'path'

export default defineConfig({
  resolve: { alias: { '@': resolve(__dirname, 'src') } },
  server: { hmr: false },
  test: { include: ['src/**/*.test.ts'] }
})
