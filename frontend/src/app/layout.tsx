import type { Metadata } from "next";
import { Rye, Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import { Providers } from "./providers";
import { Sidebar } from "@/components/Sidebar";

const rye = Rye({
  variable: "--font-rye",
  subsets: ["latin"],
  weight: "400",
});

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

const jetbrainsMono = JetBrains_Mono({
  variable: "--font-jetbrains-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "AgentSheriff",
  description: "The permission layer for the agentic frontier.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${rye.variable} ${inter.variable} ${jetbrainsMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col font-sans">
        <svg
          width="0"
          height="0"
          style={{ position: "absolute" }}
          aria-hidden="true"
        >
          <defs>
            <filter id="parchment-noise">
              <feTurbulence
                type="fractalNoise"
                baseFrequency="0.85"
                numOctaves={2}
                seed={7}
                stitchTiles="stitch"
              />
              <feColorMatrix
                type="matrix"
                values="0 0 0 0 0.17 0 0 0 0 0.10 0 0 0 0 0.06 0 0 0 0.22 0"
              />
            </filter>
            <symbol id="sheriff-star" viewBox="0 0 24 24">
              <path
                d="M12 1 L14.587 8.441 L22.462 8.601 L16.186 13.360 L18.465 20.898 L12 16.4 L5.535 20.898 L7.814 13.360 L1.538 8.601 L9.413 8.441 Z"
                fill="currentColor"
              />
            </symbol>
          </defs>
        </svg>
        <Providers>
          <div className="flex flex-1">
            <Sidebar />
            <main className="flex-1 px-10 py-8">{children}</main>
          </div>
        </Providers>
      </body>
    </html>
  );
}
