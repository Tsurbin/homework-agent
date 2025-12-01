import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api/agent": {
        target: "http://localhost:8000", // Your backend host:port
        changeOrigin: true,
        // rewrite: (path) => path.replace(/^\/api\/agent/, "/agent"), // optional: strip prefix
      },
    },
  },
})
