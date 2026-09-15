import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { resolve } from 'node:path';

export default defineConfig({
  plugins: [react()],
  base: '/static/islands/',
  build: {
    outDir: '../static/islands', emptyOutDir: true, manifest: 'manifest.json',
    sourcemap: false, target: 'es2022',
    rollupOptions: { input: {
      sources: resolve(import.meta.dirname, 'src/sources.tsx'),
      archive: resolve(import.meta.dirname, 'src/archive.tsx'),
      chronology: resolve(import.meta.dirname, 'src/chronology.tsx'),
    } },
  },
});
