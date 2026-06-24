import type { Metadata } from "next";
import "./globals.css";
import "./kg.css";

export const metadata: Metadata = {
  title: "KrishiGPT — Farming advice in your language",
  description:
    "Region-aware multilingual agricultural advisor for Indian farmers, grounded in official ICAR Package of Practices.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
