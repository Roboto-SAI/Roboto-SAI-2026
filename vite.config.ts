import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";
import path from "node:path";
import { componentTagger } from "lovable-tagger";

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => ({
  base: "./",
  cacheDir: path.resolve(__dirname, "./.vite-cache"),
  server: {
    host: "::",
    port: 8080,
    proxy: {
      "/api": {
        // Allow overriding backend URL when running inside Docker
        target: process.env.VITE_API_URL || process.env.API_PROXY_TARGET || "http://localhost:5000",
        changeOrigin: true,
        configure: (proxy, options) => {
          // Safe POST body forward v4: http-proxy event (Vite docs)
          proxy.on('proxyReq', (proxyReq, req, res) => {
            if (req.method === 'POST') {
              const cl = req.headers['content-length'];
              if (cl) proxyReq.setHeader('Content-Length', cl);
            }
          });
        },
      },
    },
  },
  plugins: [react(), mode === "development" && componentTagger()].filter(Boolean),
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  // Removed hardcoded VITE_API_URL - use proxy instead for dev
  // define: {
  //   "import.meta.env.VITE_API_URL": JSON.stringify(process.env.VITE_API_URL || "http://localhost:5000"),
  // },
}));
