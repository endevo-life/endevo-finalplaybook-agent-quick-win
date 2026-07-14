import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Pin a dedicated port so the app always lives at the SAME URL for demos.
// strictPort: true -> fail loudly if the port is taken instead of silently
// hopping to 5174/5175 (which caused "URL taken / nothing loads" confusion).
// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3200,
    strictPort: true,
  },
})
