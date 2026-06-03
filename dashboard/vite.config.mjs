import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'node:path'
import autoprefixer from 'autoprefixer'

export default defineConfig(() => {
  return {
    base: './',
    build: {
      outDir: 'build',
    },
    css: {
      postcss: {
        plugins: [
          autoprefixer({}), // add options if needed
        ],
      },
    },
    // Many source modules carry JSX inside plain ``.js`` files. Vite 8
    // (Rolldown/Oxc) no longer infers a JSX loader from the old
    // ``esbuild.loader`` hack used under Vite 5, so we let
    // @vitejs/plugin-react own the JSX transform for both ``.js`` and
    // ``.jsx`` (it already includes ``.js`` by default; the explicit
    // pattern keeps the intent obvious and survives plugin defaults).
    optimizeDeps: {
      force: true,
    },
    plugins: [react({ include: /\.(js|jsx|ts|tsx)$/ })],
    resolve: {
      alias: [
        {
          find: 'src/',
          replacement: `${path.resolve(__dirname, 'src')}/`,
        },
        {
          find: '@utils',
          replacement: path.resolve(__dirname, 'src/utils'),
        },
      ],
      extensions: ['.mjs', '.js', '.ts', '.jsx', '.tsx', '.json', '.scss'],
    },
    server: {
      port: 3000,
      proxy: {
        // https://vitejs.dev/config/server-options.html
      },
    },
  }
})
