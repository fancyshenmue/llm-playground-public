import { resolve } from 'path'
import { defineConfig } from 'electron-vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  main: {
    resolve: {
      alias: {
        '@internal': resolve(__dirname, '../../../internal/node')
      }
    }
  },
  preload: {
    resolve: {
      alias: {
        '@internal': resolve(__dirname, '../../../internal/node')
      }
    }
  },
  renderer: {
    resolve: {
      alias: {
        '@renderer': resolve('src/renderer/src'),
        '@internal': resolve(__dirname, '../../../internal/node')
      }
    },
    plugins: [react()]
  }
})
