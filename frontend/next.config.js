/** @type {import('next').NextConfig} */
// 后端地址优先级:
// 1. 显式的 BACKEND_URL 环境变量 (最高, 想临时指向别的后端时用)
// 2. 在 Vercel 上 (process.env.VERCEL=1) 默认走线上 Render 后端
// 3. 本地开发默认走本机 uvicorn
const PROD_BACKEND = "https://career-twin-backend.onrender.com";
const backendUrl =
  process.env.BACKEND_URL ||
  (process.env.VERCEL ? PROD_BACKEND : "http://127.0.0.1:8001");

const nextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${backendUrl}/api/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;
