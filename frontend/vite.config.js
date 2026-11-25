import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

// 远端隧道试用：VITE_TUNNEL=1 npm run dev
const tunnel = process.env.VITE_TUNNEL === "1";

export default defineConfig({
  plugins: [vue()],
  server: {
    // 0.0.0.0 = 本机 + 局域网都能访问（原来只听 127.0.0.1，只能本机开）
    host: "0.0.0.0",
    port: 5173,
    strictPort: true,
    // ngrok 域名访问时放行 Host，避免被 Vite 拦成空白页
    allowedHosts: [
      ".ngrok-free.dev",
      ".ngrok-free.app",
      ".ngrok.io",
      ".ngrok.app",
      ".trycloudflare.com",
    ],
    hmr: tunnel
      ? {
          protocol: "wss",
          clientPort: 443,
        }
      : undefined,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8001",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
    },
  },
});
