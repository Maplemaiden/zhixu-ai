# 前端 · Vue 3 + Vite

中期竖切页面：课程步骤 / 智能答疑 / 计算校验 / 练习题。

## 启动

先开后端（8000），再开前端：

```bash
cd frontend
npm install
npm run dev
```

浏览器打开终端提示的地址（一般是 http://127.0.0.1:5173 ）。  
请求通过 Vite 代理转到 `http://127.0.0.1:8000`（见 `vite.config.js`）。
