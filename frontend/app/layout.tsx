import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Career Twin",
  description: "看清未来有哪几条路",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}
