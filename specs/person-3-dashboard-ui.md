# Person 3 — Dashboard UI (Frontend) — Implementation Spec

> **Owner:** Person 3.
> **Scope:** every file under `frontend/`. Next.js 15 App Router, Tailwind, shadcn/ui, framer-motion, zustand, react-use-websocket, react-query.
> **Not your scope:** anything under `backend/`, `demo/openclaw-config/`, `demo/docker-compose.yml`, scenario JSON, or the Deputy Dusty Python CLI. Person 1 owns gateway + REST. Person 2 owns Dusty + scenarios + adapters. Person 4 owns policies + classifier + audit store.
> **Read first:** `specs/_shared-context.md`. All DTOs, the demo script, and the API contract are defined there. This document does not re-derive them — it builds on them.

## 0. "Ready to code" checklist

Tick these in order. If any item fails, fix before moving on.

- [ ] Node 20.x active (`node -v`).
- [ ] You're at repo root (`/Users/ianrowe/git/Agent_Sheriff`). `frontend/` is empty or absent.
- [ ] You've read `specs/_shared-context.md` end-to-end (especially "API contracts" and "Demo").
- [ ] You agree the three-scene demo (good → injection → approval) is the only acceptance test that matters.
- [ ] Person 1 has either real `/v1/*` endpoints up, or you have decided to ship with `NEXT_PUBLIC_USE_MOCKS=1` and the bundled fixtures in `src/mocks/`.
- [ ] The palette is memorised: parchment `#f3e9d2`, dark brown `#3b2a1a`, brass `#b8864b`, wanted red `#a4161a`, allowed green `#2d6a4f`, approval amber `#d68c1e`. No purple/blue except the small AI-glow on the AI-risk KPI.
- [ ] You've installed `pnpm` or `npm` (this spec uses `npm`; switch consistently if you prefer pnpm).
- [ ] You've installed Rye and Inter via `next/font` — no external `<link>` tags.
- [ ] You can render at 1920×1080 and at 1280px wide (the demo will go to a projector).

> **Backend contract is authoritative.** Person 1 owns all DTO shapes. Any disagreement between this spec and `person-1-backend-core.md` is resolved in favor of P1. Mirror P1's DTOs verbatim in `frontend/src/lib/types.ts`. If a field name, enum value, or response shape differs here, P1's spec wins — open a PR to update this file rather than deviating in code.

---

## 1. Hour-0 setup commands (do these first, in order)

From repo root:

```bash
# 1. Scaffold (pin to 15.x — `@latest` drifts and has hit peer-dep loops)
npx create-next-app@15 frontend --typescript --tailwind --app --src-dir --no-eslint --import-alias "@/*"
cd frontend

# 2. Pin core dependencies (versions in §2 below — overwrite package.json after this step)
npm install \
  next@15.0.3 react@19.0.0 react-dom@19.0.0 \
  tailwindcss@3.4.14 postcss@8.4.49 autoprefixer@10.4.20 \
  lucide-react@0.460.0 framer-motion@11.11.17 \
  react-use-websocket@4.11.1 zustand@5.0.1 \
  clsx@2.1.1 class-variance-authority@0.7.1 tailwind-merge@2.5.4 tailwindcss-animate@1.0.7 \
  @tanstack/react-query@5.59.20 @tanstack/react-virtual@3.10.9 \
  @uiw/react-codemirror@4.23.6 @codemirror/lang-yaml@6.1.1 @codemirror/state@6.4.1 @codemirror/view@6.34.1 \
  sonner@1.7.0 \
  zod@3.23.8 \
  date-fns@4.1.0

npm install -D \
  @types/node@22.9.0 @types/react@19.0.0 @types/react-dom@19.0.0 \
  typescript@5.6.3 \
  msw@2.6.4

# 3. shadcn init (accept defaults, base color = neutral, css variables = yes)
npx shadcn@latest init

# 4. shadcn components (run as one line — all of these are used)
npx shadcn@latest add button card badge dialog table sheet tabs input textarea select scroll-area tooltip sonner separator skeleton

# 5. Verify dev server boots before you touch anything else
npm run dev
# open http://localhost:3000 — should render the Next.js default page
```

After step 5 boots cleanly, replace `package.json`, `tailwind.config.ts`, `src/app/layout.tsx`, `src/app/globals.css` with the contents in §2–§4 below. Then start building pages.

> **Escape hatch — if Next 15 / React 19 breaks.** Pin `create-next-app@15.x` (the `@latest` tag drifts). If install fails (peer-dep loop), or if you hit a hydration error inside shadcn/ui or framer-motion that you can't resolve in 30 minutes, fall back to **Next 14.2.x + React 18.3.x with shadcn/ui pinned**. Use this alternate `dependencies` block in `package.json` instead of the §2 block:
>
> ```json
> {
>   "dependencies": {
>     "next": "14.2.18",
>     "react": "18.3.1",
>     "react-dom": "18.3.1",
>     "@radix-ui/react-dialog": "1.1.2",
>     "@radix-ui/react-scroll-area": "1.2.1",
>     "@radix-ui/react-select": "2.1.2",
>     "@radix-ui/react-separator": "1.1.0",
>     "@radix-ui/react-slot": "1.1.0",
>     "@radix-ui/react-tabs": "1.1.1",
>     "@radix-ui/react-tooltip": "1.1.4",
>     "@tanstack/react-query": "5.59.20",
>     "@tanstack/react-virtual": "3.10.9",
>     "@uiw/react-codemirror": "4.23.6",
>     "@codemirror/lang-yaml": "6.1.1",
>     "@codemirror/state": "6.4.1",
>     "@codemirror/view": "6.34.1",
>     "class-variance-authority": "0.7.1",
>     "clsx": "2.1.1",
>     "date-fns": "4.1.0",
>     "framer-motion": "11.11.17",
>     "lucide-react": "0.460.0",
>     "react-use-websocket": "4.11.1",
>     "sonner": "1.7.0",
>     "tailwind-merge": "2.5.4",
>     "tailwindcss-animate": "1.0.7",
>     "zod": "3.23.8",
>     "zustand": "5.0.1"
>   },
>   "devDependencies": {
>     "@types/node": "22.9.0",
>     "@types/react": "18.3.12",
>     "@types/react-dom": "18.3.1",
>     "autoprefixer": "10.4.20",
>     "msw": "2.6.4",
>     "postcss": "8.4.49",
>     "tailwindcss": "3.4.14",
>     "typescript": "5.6.3"
>   }
> }
> ```
>
> When falling back, regenerate the lockfile (`rm -rf node_modules package-lock.json && npm install`). All component code in §5/§12 is React-18-compatible; the only Next-15-specific bit is the default async-by-default route segment config, which we don't rely on.

---

## 2. `frontend/package.json` (full file — overwrite after `create-next-app`)

```json
{
  "name": "agentsheriff-frontend",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "typecheck": "tsc --noEmit"
  },
  "dependencies": {
    "@codemirror/lang-yaml": "6.1.1",
    "@codemirror/state": "6.4.1",
    "@codemirror/view": "6.34.1",
    "@radix-ui/react-dialog": "1.1.2",
    "@radix-ui/react-scroll-area": "1.2.1",
    "@radix-ui/react-select": "2.1.2",
    "@radix-ui/react-separator": "1.1.0",
    "@radix-ui/react-slot": "1.1.0",
    "@radix-ui/react-tabs": "1.1.1",
    "@radix-ui/react-tooltip": "1.1.4",
    "@tanstack/react-query": "5.59.20",
    "@tanstack/react-virtual": "3.10.9",
    "@uiw/react-codemirror": "4.23.6",
    "class-variance-authority": "0.7.1",
    "clsx": "2.1.1",
    "date-fns": "4.1.0",
    "framer-motion": "11.11.17",
    "lucide-react": "0.460.0",
    "next": "15.0.3",
    "react": "19.0.0",
    "react-dom": "19.0.0",
    "react-use-websocket": "4.11.1",
    "sonner": "1.7.0",
    "tailwind-merge": "2.5.4",
    "tailwindcss-animate": "1.0.7",
    "zod": "3.23.8",
    "zustand": "5.0.1"
  },
  "devDependencies": {
    "@types/node": "22.9.0",
    "@types/react": "19.0.0",
    "@types/react-dom": "19.0.0",
    "autoprefixer": "10.4.20",
    "msw": "2.6.4",
    "postcss": "8.4.49",
    "tailwindcss": "3.4.14",
    "typescript": "5.6.3"
  }
}
```

---

## 3. `frontend/tailwind.config.ts` (full file)

```ts
import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    container: { center: true, padding: "1.5rem", screens: { "2xl": "1440px" } },
    extend: {
      colors: {
        parchment: {
          DEFAULT: "#f3e9d2",
          50:  "#fbf6e8",
          100: "#f7efd9",
          200: "#f3e9d2",
          300: "#e7d6a8",
          400: "#d6bd7a",
        },
        brown: {
          DEFAULT: "#3b2a1a",
          50:  "#7a5a3a",
          100: "#5a4127",
          200: "#3b2a1a",
          300: "#2a1d11",
          400: "#1a1209",
        },
        brass:    { DEFAULT: "#b8864b", light: "#d4a572", dark: "#8c6432" },
        wanted:   { DEFAULT: "#a4161a", light: "#c92a2e", dark: "#7a0e12" },
        allowed:  { DEFAULT: "#2d6a4f", light: "#3f8f6c", dark: "#1f4a36" },
        approval: { DEFAULT: "#d68c1e", light: "#e8a847", dark: "#a66a14" },
        ai:       { DEFAULT: "#6b5b95", glow: "#8a7bb5" },
        // shadcn variables (kept so default components still render)
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        muted: { DEFAULT: "hsl(var(--muted))", foreground: "hsl(var(--muted-foreground))" },
        card: { DEFAULT: "hsl(var(--card))", foreground: "hsl(var(--card-foreground))" },
        popover: { DEFAULT: "hsl(var(--popover))", foreground: "hsl(var(--popover-foreground))" },
        primary: { DEFAULT: "hsl(var(--primary))", foreground: "hsl(var(--primary-foreground))" },
        secondary: { DEFAULT: "hsl(var(--secondary))", foreground: "hsl(var(--secondary-foreground))" },
        accent: { DEFAULT: "hsl(var(--accent))", foreground: "hsl(var(--accent-foreground))" },
        destructive: { DEFAULT: "hsl(var(--destructive))", foreground: "hsl(var(--destructive-foreground))" },
      },
      fontFamily: {
        rye:   ["var(--font-rye)", "serif"],
        inter: ["var(--font-inter)", "system-ui", "sans-serif"],
      },
      fontSize: {
        // floor at 14px for projector readability
        xs:  ["0.875rem", { lineHeight: "1.25rem" }],
        sm:  ["0.95rem",  { lineHeight: "1.4rem"  }],
      },
      borderRadius: { lg: "var(--radius)", md: "calc(var(--radius) - 2px)", sm: "calc(var(--radius) - 4px)" },
      boxShadow: {
        parchment: "0 1px 0 rgba(59,42,26,0.06), 0 8px 24px -12px rgba(59,42,26,0.35)",
        wanted: "0 4px 20px -4px rgba(164,22,26,0.45)",
        brass: "0 0 0 2px #b8864b",
        "ai-glow": "0 0 18px 2px rgba(138,123,181,0.55)",
      },
      keyframes: {
        "stamp-in": {
          "0%":   { transform: "scale(2.4) rotate(-22deg)", opacity: "0" },
          "60%":  { transform: "scale(0.95) rotate(-6deg)", opacity: "1" },
          "80%":  { transform: "scale(1.05) rotate(-3deg)" },
          "100%": { transform: "scale(1) rotate(-3deg)", opacity: "1" },
        },
        "ticker-in": {
          "0%":   { transform: "translateY(-6px)", opacity: "0" },
          "100%": { transform: "translateY(0)",     opacity: "1" },
        },
        "pulse-amber": {
          "0%,100%": { boxShadow: "0 0 0 0 rgba(214,140,30,0.55)" },
          "50%":     { boxShadow: "0 0 0 10px rgba(214,140,30,0)" },
        },
      },
      animation: {
        "stamp-in": "stamp-in 700ms cubic-bezier(.2,.7,.2,1.4) both",
        "ticker-in": "ticker-in 220ms ease-out both",
        "pulse-amber": "pulse-amber 1.6s ease-out infinite",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};

export default config;
```

---

## 4. `frontend/src/app/globals.css` (full file)

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

/* shadcn css variables — Old West tuned */
@layer base {
  :root {
    --background: 41 67% 89%;          /* parchment */
    --foreground: 24 38% 17%;          /* brown */
    --card: 41 67% 92%;
    --card-foreground: 24 38% 17%;
    --popover: 41 67% 92%;
    --popover-foreground: 24 38% 17%;
    --primary: 32 43% 51%;             /* brass */
    --primary-foreground: 41 67% 95%;
    --secondary: 24 38% 17%;
    --secondary-foreground: 41 67% 95%;
    --muted: 41 30% 78%;
    --muted-foreground: 24 25% 35%;
    --accent: 32 43% 51%;
    --accent-foreground: 24 38% 17%;
    --destructive: 359 76% 37%;        /* wanted red */
    --destructive-foreground: 41 67% 95%;
    --border: 32 25% 65%;
    --input: 32 25% 65%;
    --ring: 32 43% 51%;                /* brass focus */
    --radius: 0.6rem;
  }
}

@layer base {
  html, body { background: hsl(var(--background)); color: hsl(var(--foreground)); }
  body {
    /* Parchment grain via inline SVG noise — no extra HTTP request. */
    background-image:
      url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='220' height='220'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='2' stitchTiles='stitch'/><feColorMatrix values='0 0 0 0 0.23  0 0 0 0 0.16  0 0 0 0 0.10  0 0 0 0.08 0'/></filter><rect width='100%' height='100%' filter='url(%23n)'/></svg>"),
      radial-gradient(ellipse at top, #fbf6e8 0%, #f3e9d2 55%, #e7d6a8 100%);
    background-blend-mode: multiply, normal;
    font-feature-settings: "kern", "liga", "ss01";
    letter-spacing: -0.005em;
  }
  ::selection { background: #b8864b; color: #fbf6e8; }
  /* Default focus = brass ring, visible on projectors */
  :focus-visible { outline: 2px solid #b8864b; outline-offset: 2px; border-radius: 4px; }
  h1,h2,h3,h4 { font-family: var(--font-rye), serif; color: #3b2a1a; letter-spacing: 0; }
  h1 { font-size: 2.25rem; line-height: 1.05; }   /* never larger than 4xl */
  h2 { font-size: 1.75rem; line-height: 1.1; }
  h3 { font-size: 1.25rem; line-height: 1.2; }
}

@layer components {
  /* Torn-paper card — applied to .paper */
  .paper {
    position: relative;
    background: linear-gradient(180deg, #fbf6e8 0%, #f3e9d2 100%);
    border: 1px solid rgba(59,42,26,0.18);
    box-shadow: 0 1px 0 rgba(59,42,26,0.06), 0 8px 24px -12px rgba(59,42,26,0.35);
    -webkit-mask-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100' preserveAspectRatio='none'><path d='M0,3 Q4,0 9,2 T20,3 T32,1 T44,3 T58,2 T72,3 T86,1 T100,3 L100,97 Q96,100 91,98 T80,97 T68,99 T56,97 T42,98 T28,97 T14,99 T0,97 Z' fill='black'/></svg>");
    mask-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100' preserveAspectRatio='none'><path d='M0,3 Q4,0 9,2 T20,3 T32,1 T44,3 T58,2 T72,3 T86,1 T100,3 L100,97 Q96,100 91,98 T80,97 T68,99 T56,97 T42,98 T28,97 T14,99 T0,97 Z' fill='black'/></svg>");
    -webkit-mask-size: 100% 100%; mask-size: 100% 100%;
  }
  .paper-flat {
    background: linear-gradient(180deg, #fbf6e8 0%, #f3e9d2 100%);
    border: 1px solid rgba(59,42,26,0.18);
    box-shadow: 0 1px 0 rgba(59,42,26,0.06), 0 8px 24px -12px rgba(59,42,26,0.35);
    border-radius: var(--radius);
  }
  .wanted-stamp {
    transform: rotate(-3deg);
    border: 4px double #a4161a;
    color: #a4161a;
    padding: 0.25rem 0.75rem;
    font-family: var(--font-rye), serif;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    background: rgba(251,246,232,0.4);
  }
  .ai-glow { box-shadow: 0 0 18px 2px rgba(138,123,181,0.55); }
}

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.001ms !important;
    transition-duration: 0.001ms !important;
  }
}
```

---

## 5. `frontend/src/app/layout.tsx` (full file)

```tsx
import type { Metadata } from "next";
import { Inter, Rye } from "next/font/google";
import "./globals.css";
import { Sidebar } from "@/components/Sidebar";
import { Providers } from "@/components/Providers";
import { ConnectionBanner } from "@/components/ConnectionBanner";
import { Toaster } from "sonner";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter", display: "swap" });
const rye   = Rye({ subsets: ["latin"], variable: "--font-rye",   weight: "400", display: "swap" });

export const metadata: Metadata = {
  title: "AgentSheriff — Frontier Justice for AI",
  description: "External permission, audit, and approval layer for AI agents.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${inter.variable} ${rye.variable}`}>
      <body className="font-inter min-h-screen antialiased">
        <Providers>
          <ConnectionBanner />
          <div className="flex min-h-screen">
            <Sidebar />
            <main className="flex-1 px-8 py-6 max-w-[1600px] mx-auto w-full">
              {children}
            </main>
          </div>
          <Toaster position="bottom-right" theme="light" richColors closeButton />
        </Providers>
      </body>
    </html>
  );
}
```

`src/components/Providers.tsx`:

```tsx
"use client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState, useEffect } from "react";
import { useStreamBootstrap } from "@/lib/ws";

export function Providers({ children }: { children: React.ReactNode }) {
  const [qc] = useState(() => new QueryClient({
    defaultOptions: { queries: { staleTime: 5_000, refetchOnWindowFocus: false, retry: 1 } },
  }));
  return (
    <QueryClientProvider client={qc}>
      <StreamBoot />
      {children}
    </QueryClientProvider>
  );
}

function StreamBoot() {
  useStreamBootstrap();
  return null;
}
```

---

## 6. Design system rules (enforce these in code review)

| Rule | Implementation |
|---|---|
| Headings always Rye, never larger than `text-4xl` | `globals.css` h1 cap; eslint-disable inline tw classes that exceed it |
| Body uses Inter `tracking-tight` | Body is `font-inter`; default letter-spacing set in globals |
| Cards: torn-paper edge OR brown drop-shadow | Use `.paper` (mask) for posters/approvals, `.paper-flat` for tables/ledger |
| Icons from lucide only | `Shield`, `Gavel`, `Scroll`, `HandCoins`, `Skull`, `BadgeCheck`, `UserX`, `Activity`, `WifiOff`, `Wifi`, `Play` |
| All motion via framer-motion `spring` stiffness 180 | `transition={{ type: "spring", stiffness: 180, damping: 22 }}` everywhere except slam-in |
| No purple/blue except `ai.glow` for AI-risk KPI | Only the AI risk KPI card may use the `ai-glow` shadow |
| Responsive ≥ 1280px wide | Test in `next dev` with viewport at 1280×800 and 1920×1080 |
| Min 14px font on screen | Tailwind `text-xs` redefined to 14px (see config) |
| Contrast ≥ 4.5:1 | Brown `#3b2a1a` on parchment `#f3e9d2` = 9.4:1; never use brass on parchment for body text |
| Focus ring brass | `:focus-visible { outline: 2px solid #b8864b; }` |
| `ApprovalState` badge palette | `pending` → approval amber filled; `approved` → allowed green filled; `denied` → wanted red filled; `redacted` → approval amber **outlined** (border only, parchment background); `timed_out` → brown-50 muted filled. Never render `expired` — backend uses `timed_out`. |

Logo SVG (drop in `components/Sidebar.tsx`):

```tsx
<svg viewBox="0 0 64 64" className="h-9 w-9" aria-hidden>
  <defs>
    <radialGradient id="bg" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stopColor="#d4a572"/><stop offset="100%" stopColor="#8c6432"/>
    </radialGradient>
  </defs>
  <polygon fill="url(#bg)" stroke="#3b2a1a" strokeWidth="2"
    points="32,2 39,12 51,10 49,22 60,28 51,36 53,48 41,48 32,58 23,48 11,48 13,36 4,28 15,22 13,10 25,12"/>
  <text x="32" y="38" textAnchor="middle" fontFamily="serif" fontWeight="900" fontSize="18" fill="#3b2a1a">AS</text>
</svg>
```

---

## 7. Type mirror — `frontend/src/lib/types.ts` (full file)

These mirror Person 4's Pydantic DTOs verbatim. If Person 4 changes any field, change here too.

```ts
// Mirrors backend/src/agentsheriff/models/dto.py
export type Decision = "allow" | "deny" | "approval_required";
export type AgentState = "active" | "jailed" | "revoked";
export type ApprovalAction = "approve" | "deny" | "redact";
export type ApprovalScope = "once" | "always_recipient" | "always_tool";
export type ApprovalState = "pending" | "approved" | "denied" | "redacted" | "timed_out";

export interface ToolCallContext {
  task_id?: string;
  source_prompt?: string;
  source_content?: string;
}

export interface ToolCallRequest {
  agent_id: string;
  tool: string;
  args: Record<string, unknown>;
  context?: ToolCallContext;
}

export interface ToolCallResponse {
  decision: Decision;
  approval_id?: string;
  reason: string;
  policy_id?: string;
  risk_score: number;          // 0–100
  result?: unknown;            // adapter output, present iff decision==="allow"
  user_explanation?: string | null; // Sonnet humanised explanation, nullable; present on deny / approval_required
}

export interface AgentDTO {
  id: string;
  label: string;
  state: AgentState;
  created_at: string;          // ISO-8601 UTC
  last_seen_at: string;        // ISO-8601 UTC (was last_seen — renamed to match backend)
  jailed_reason?: string;      // populated when state !== "active"
  requests_today: number;      // backend-computed
  blocked_today: number;       // backend-computed
}

export interface AuditEntryDTO {
  id: string;
  ts: string;                  // ISO-8601 UTC
  agent_id: string;
  agent_label: string;         // backend-supplied snapshot; do not look up from agents map
  tool: string;
  args: Record<string, unknown>;
  decision: Decision;
  reason: string;
  policy_id?: string;
  risk_score: number;
  user_explanation?: string | null; // nullable — backend may emit null when Sonnet declined to humanise
  result?: unknown;
}

export interface ApprovalDTO {
  id: string;
  created_at: string;
  expires_at: string;          // ISO-8601 UTC; backend-set (created_at + 120s). Client computes remaining as expires_at - now() — never derive from a local timestamp.
  agent_id: string;
  agent_label: string;
  tool: string;
  args: Record<string, unknown>;
  reason: string;
  user_explanation?: string;
  risk_score: number;
  state: ApprovalState;
  resolved_action?: ApprovalAction;
  resolved_scope?: ApprovalScope;
}

export interface PolicyTemplate { name: string; description: string; }
export interface PoliciesPayload { yaml: string; updated_at: string; }

// WS frames — discriminated union on .type
export type StreamFrame =
  | { type: "audit";       payload: AuditEntryDTO }
  | { type: "approval";    payload: ApprovalDTO }
  | { type: "agent_state"; payload: { agent_id: string; state: AgentState } }
  | { type: "heartbeat";   payload: { ts: string } };

// REST request bodies
export interface ApprovalActionBody { action: ApprovalAction; scope: ApprovalScope; }
export interface ApplyTemplateBody { name: string; }
export interface SavePolicyBody { yaml: string; }

// Demo trigger (Person 2 endpoint — see §11)
export type ScenarioId = "good" | "injection" | "approval";
```

---

## 8. API client — `frontend/src/lib/api.ts` (full file)

```ts
"use client";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type {
  AgentDTO, ApprovalDTO, AuditEntryDTO, PoliciesPayload, PolicyTemplate,
  ApprovalActionBody, ApplyTemplateBody, SavePolicyBody, ScenarioId,
} from "./types";

const API_BASE  = process.env.NEXT_PUBLIC_API_BASE  ?? "http://localhost:8000";
const USE_MOCKS = process.env.NEXT_PUBLIC_USE_MOCKS === "1";

async function jfetch<T>(path: string, init?: RequestInit): Promise<T> {
  if (USE_MOCKS) return (await import("@/mocks/router")).mockFetch<T>(path, init);
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText} on ${path}`);
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

// ---------- queries ----------
export const useAgents = () =>
  useQuery({ queryKey: ["agents"], queryFn: () => jfetch<AgentDTO[]>("/v1/agents"), refetchInterval: 15_000 });

export const useApprovals = (state: "pending" | "all" = "pending") =>
  useQuery({
    queryKey: ["approvals", state],
    queryFn: () => jfetch<ApprovalDTO[]>(`/v1/approvals${state === "pending" ? "?state=pending" : ""}`),
    refetchInterval: 5_000,
  });

/**
 * `GET /v1/audit?limit=&agent_id=&decision=&since=` → AuditEntryDTO[]
 * Used by the Ledger page (filters) and by the poll-fallback path in `useStreamBootstrap`
 * when the WebSocket has been disconnected for >5s.
 */
export interface AuditQuery {
  limit?: number;
  agent_id?: string;
  decision?: "allow" | "deny" | "approval_required";
  since?: string; // ISO-8601 UTC
}
function auditPath(q: AuditQuery = {}): string {
  const sp = new URLSearchParams();
  if (q.limit    != null) sp.set("limit",    String(q.limit));
  if (q.agent_id)         sp.set("agent_id", q.agent_id);
  if (q.decision)         sp.set("decision", q.decision);
  if (q.since)            sp.set("since",    q.since);
  const qs = sp.toString();
  return `/v1/audit${qs ? `?${qs}` : ""}`;
}
export const useAudit = (q: AuditQuery = { limit: 500 }) =>
  useQuery({
    queryKey: ["audit", q],
    queryFn: () => jfetch<AuditEntryDTO[]>(auditPath(q)),
  });

/**
 * `GET /health` → { status: "ok"; ts: string }
 * Used by `<ConnectionIndicator/>` for a passive health ping when the WebSocket
 * is in `disconnected` or `connecting` state. Refetches every 5s while unhealthy.
 */
export interface HealthDTO { status: "ok"; ts: string }
export const useHealth = (enabled = true) =>
  useQuery({
    queryKey: ["health"],
    queryFn: () => jfetch<HealthDTO>("/health"),
    refetchInterval: 5_000,
    enabled,
  });

export const usePolicies = () =>
  useQuery({ queryKey: ["policies"], queryFn: () => jfetch<PoliciesPayload>("/v1/policies") });

export const usePolicyTemplates = () =>
  useQuery({ queryKey: ["policy-templates"], queryFn: () => jfetch<PolicyTemplate[]>("/v1/policies/templates") });

// ---------- mutations ----------
export function useApproveDecision() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (vars: { id: string; body: ApprovalActionBody }) =>
      jfetch<ApprovalDTO>(`/v1/approvals/${vars.id}`, { method: "POST", body: JSON.stringify(vars.body) }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["approvals"] }); },
  });
}

export function useApplyTemplate() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: ApplyTemplateBody) =>
      jfetch<PoliciesPayload>("/v1/policies/apply-template", { method: "POST", body: JSON.stringify(body) }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["policies"] }); },
  });
}

export function useSavePolicy() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: SavePolicyBody) =>
      jfetch<PoliciesPayload>("/v1/policies", { method: "PUT", body: JSON.stringify(body) }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["policies"] }); },
  });
}

export function useJailAgent() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => jfetch<AgentDTO>(`/v1/agents/${id}/jail`, { method: "POST" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["agents"] }),
  });
}

export function useRevokeAgent() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => jfetch<AgentDTO>(`/v1/agents/${id}/revoke`, { method: "POST" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["agents"] }),
  });
}

export function useReleaseAgent() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => jfetch<AgentDTO>(`/v1/agents/${id}/release`, { method: "POST" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["agents"] }),
  });
}

/**
 * `POST /v1/demo/run/{scenario_id}` → { started: boolean; pid?: number }
 * Person 1 owns this endpoint (kicks off `python -m agentsheriff.demo.deputy_dusty --scenario X`
 * in a subprocess). `pid` is returned when the subprocess was spawned successfully so the UI
 * can disable re-run while the prior run is still in flight.
 */
export interface RunScenarioResponse { started: boolean; pid?: number }
export function useRunScenario() {
  return useMutation({
    mutationFn: (id: ScenarioId) =>
      jfetch<RunScenarioResponse>(`/v1/demo/run/${id}`, { method: "POST" }),
  });
}
```

---

## 9. WebSocket — `frontend/src/lib/ws.ts` (full file)

```ts
"use client";
import useWebSocket, { ReadyState } from "react-use-websocket";
import { useEffect, useRef } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useSheriffStore } from "./store";
import type { StreamFrame } from "./types";

const WS_URL =
  process.env.NEXT_PUBLIC_WS_URL ??
  (process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000").replace(/^http/, "ws") + "/v1/stream";

const USE_MOCKS = process.env.NEXT_PUBLIC_USE_MOCKS === "1";

/** Mounted once at app root to wire WS → store. */
export function useStreamBootstrap() {
  const ingest = useSheriffStore(s => s.ingestFrame);
  const setConn = useSheriffStore(s => s.setConnectionState);

  const qc = useQueryClient();
  const prevReadyState = useRef<ReadyState | null>(null);

  const { lastMessage, readyState } = useWebSocket(USE_MOCKS ? null : WS_URL, {
    shouldReconnect: () => true,
    reconnectAttempts: Infinity,
    // 1s → max 10s exponential backoff
    reconnectInterval: (attempt) => Math.min(10_000, 1000 * 2 ** Math.min(attempt, 4)),
    share: true,
    // Server pushes JSON HeartbeatFrame every 15s ({"type":"heartbeat","payload":{"ts":"..."}}).
    // The backend does NOT respond to plain-text "ping" with "pong" — do NOT configure
    // `heartbeat: { message, returnMessage, timeout }` here or react-use-websocket will
    // close the socket every 60s and the WS will flap. Rely on server-initiated heartbeats
    // plus react-use-websocket's automatic reconnect-on-close behaviour.
  });

  useEffect(() => {
    setConn(
      readyState === ReadyState.OPEN ? "connected" :
      readyState === ReadyState.CONNECTING ? "connecting" :
      USE_MOCKS ? "mocked" : "disconnected"
    );
    // P0-6: on WS (re)connect, refetch REST queries so any events missed during
    // the disconnect window (especially pending approvals) are surfaced.
    if (readyState === ReadyState.OPEN && prevReadyState.current !== ReadyState.OPEN) {
      qc.refetchQueries({ queryKey: ["approvals"] });
      qc.refetchQueries({ queryKey: ["agents"] });
      qc.refetchQueries({ queryKey: ["audit"] });
    }
    prevReadyState.current = readyState;
  }, [readyState, setConn, qc]);

  useEffect(() => {
    if (!lastMessage?.data) return;
    try {
      const frame = JSON.parse(lastMessage.data) as StreamFrame;
      ingest(frame);
    } catch (e) { console.warn("Bad WS frame", e); }
  }, [lastMessage, ingest]);
}
```

---

## 10. Zustand store — `frontend/src/lib/store.ts` (full file)

```ts
"use client";
import { create } from "zustand";
import type {
  AgentDTO, ApprovalDTO, AuditEntryDTO, StreamFrame,
} from "./types";

const FEED_MAX = 200;

export type ConnectionState = "connecting" | "connected" | "disconnected" | "mocked";

interface State {
  auditFeed: AuditEntryDTO[];                     // newest first, capped at FEED_MAX
  approvals: Record<string, ApprovalDTO>;
  agents:    Record<string, AgentDTO>;
  connectionState: ConnectionState;
  lastDenyId: string | null;                      // triggers slam-in animation
  // actions
  ingestFrame: (frame: StreamFrame) => void;
  hydrateFromRest: (p: { agents?: AgentDTO[]; approvals?: ApprovalDTO[]; audit?: AuditEntryDTO[] }) => void;
  setConnectionState: (s: ConnectionState) => void;
  clearLastDeny: () => void;
}

export const useSheriffStore = create<State>((set) => ({
  auditFeed: [],
  approvals: {},
  agents: {},
  connectionState: "connecting",
  lastDenyId: null,

  ingestFrame: (frame) => set((st) => {
    switch (frame.type) {
      case "audit": {
        const entry = frame.payload;
        const next = [entry, ...st.auditFeed.filter(e => e.id !== entry.id)].slice(0, FEED_MAX);
        return {
          auditFeed: next,
          lastDenyId: entry.decision === "deny" ? entry.id : st.lastDenyId,
        };
      }
      case "approval": {
        return { approvals: { ...st.approvals, [frame.payload.id]: frame.payload } };
      }
      case "agent_state": {
        const cur = st.agents[frame.payload.agent_id];
        if (!cur) return {};
        return { agents: { ...st.agents, [cur.id]: { ...cur, state: frame.payload.state } } };
      }
      case "heartbeat":
      default: return {};
    }
  }),

  hydrateFromRest: ({ agents, approvals, audit }) => set((st) => ({
    agents:    agents    ? Object.fromEntries(agents.map(a => [a.id, a])) : st.agents,
    approvals: approvals ? Object.fromEntries(approvals.map(a => [a.id, a])) : st.approvals,
    auditFeed: audit ? audit.slice(0, FEED_MAX) : st.auditFeed,
  })),

  setConnectionState: (s) => set({ connectionState: s }),
  clearLastDeny: () => set({ lastDenyId: null }),
}));

// Selectors (stable identities help React.memo)
export const selectKpis = (st: State) => {
  const today = new Date().toISOString().slice(0, 10);
  const todayEntries = st.auditFeed.filter(e => e.ts.startsWith(today));
  return {
    allowed: todayEntries.filter(e => e.decision === "allow").length,
    blocked: todayEntries.filter(e => e.decision === "deny").length,
    awaiting: Object.values(st.approvals).filter(a => a.state === "pending").length,
    jailed:  Object.values(st.agents).filter(a => a.state !== "active").length,
  };
};
```

---

## 11. Pages — exhaustive specs

### 11.1 `src/app/page.tsx` — Town Overview (the demo's opening shot)

**Component tree**

```
<TownOverview>
  <PageHeader title="Town Overview" subtitle="The Sheriff watches every move."/>
  <KpiRow>
    <KpiCard label="Allowed today"        variant="allowed"  icon={BadgeCheck} value={kpis.allowed}/>
    <KpiCard label="Blocked today"        variant="wanted"   icon={Skull}      value={kpis.blocked}/>
    <KpiCard label="Awaiting Sheriff"     variant="approval" icon={Gavel}      value={kpis.awaiting}/>
    <KpiCard label="AI risk (avg today)"  variant="ai"       icon={Activity}   value={kpis.aiRisk} suffix="/100"/>
  </KpiRow>
  <Grid cols=12>
    <Col span=8>
      <Section title="Today on the Frontier">
        <TickerFeed entries={lastN(auditFeed,10)}/>
      </Section>
    </Col>
    <Col span=4>
      <Section title="Active Deputies">
        <AgentMiniCard /> x3
      </Section>
    </Col>
  </Grid>
  <DemoTriggerBar/>
</TownOverview>
```

**State bindings**

- `kpis = useSheriffStore(selectKpis)`. AI-risk KPI extra: `selectAiRisk` averages `risk_score` over the day's audit entries.
- `auditFeed = useSheriffStore(s => s.auditFeed)`.
- `agents = Object.values(useSheriffStore(s => s.agents))`.
- On mount: `useAgents()`, `useApprovals('pending')`, `useAudit()` → push into `hydrateFromRest`.

**Interactions**

- Numbers in `KpiCard` animate on change using framer-motion `MotionNumber` (re-render with `<motion.span key={value} initial={{y:8,opacity:0}} animate={{y:0,opacity:1}}/>`).
- New `audit` frames hit `TickerFeed`; each row enters with `animate-ticker-in`. Newest on top, cap at 10.
- Each `AgentMiniCard` shows: agent label (Rye 18px), state badge (allowed/wanted/brown), last action snippet, "Inspect" link → `/deputies?id=...`.
- `DemoTriggerBar` has three buttons: `Run Good`, `Run Injection`, `Run Approval`. Each fires `useRunScenario().mutate("good"|"injection"|"approval")`. **P1 owns the `POST /v1/demo/run/{scenario_id}` endpoint** (it shells out to Deputy Dusty). On success (`{ started: true, pid? }`) a toast announces "Deputy Dusty rides out (pid {pid})". If `started === false`, show an inline error chip "Sheriff's office busy — try again in a moment". If the mutation 404s (P1 hasn't exposed the route yet), show a tooltip: "Backend endpoint missing — run `python -m agentsheriff.demo.deputy_dusty --scenario X` from `backend/` instead". Disable the button while pending.

**Empty-state copy**

- Empty audit: *"All quiet on the frontier. Run a scenario to see the Sheriff at work."*
- No agents: *"No deputies have ridden into town yet."*
- Disconnected backend: handled globally by `<ConnectionBanner>` (rendered in `app/layout.tsx`, see §12). Town Overview keeps showing last-known state from the store under the banner — no per-page disconnect handling here.

### 11.2 `src/app/wanted/page.tsx` — Wanted Board (demo money shot)

**Component tree**

```
<WantedBoard>
  <PageHeader title="Wanted Board"/>
  <SlamInOverlay/>                 // fixed, listens to lastDenyId
  <Grid cols=3 gap=6>
    {denies.map(e => <WantedPoster entry={e}/>)}
  </Grid>
</WantedBoard>
```

**State bindings**

- `denies = useSheriffStore(s => s.auditFeed.filter(e => e.decision === "deny"))`. Newest first.
- `lastDenyId = useSheriffStore(s => s.lastDenyId)`. After SlamInOverlay finishes, calls `clearLastDeny()`.

**SlamInOverlay (the money moment)**

- Renders nothing while `lastDenyId == null` or `entry.id` already animated (track in component-local set ref).
- When a new deny is detected, render a full-screen `motion.div` containing a giant WantedPoster.
- Variants:

```ts
const slam = {
  initial: { scale: 2.4, rotate: -22, opacity: 0 },
  enter:   { scale: 1.0, rotate: -3,  opacity: 1,
             transition: { type: "spring", stiffness: 600, damping: 12, mass: 1.2 } },
  bounce:  { scale: [1, 1.06, 1], transition: { duration: 0.35, ease: "easeOut" } },
  exit:    { y: 60, scale: 0.6, opacity: 0,
             transition: { duration: 1.2, ease: [0.6, 0, 0.4, 1] } },
};
```

- Sequence: `initial → enter` (0.7s), hold 0.6s, `bounce` (0.35s), `exit` (1.2s). Total ~2.85s. Then call `clearLastDeny()`.
- An audio cue is optional — DO NOT add one unless time at H14+. (Demo speaker may or may not have audio.)
- Frame-time SLA: must enter < 100ms after the WS frame arrives. Achieved because the store update is synchronous; the overlay subscribes to `lastDenyId` only.

**WantedPoster props**

`{ entry: AuditEntryDTO; size?: "card" | "hero" }`. See §12 for full TSX.

**Empty-state copy**

*"No outlaws today. The Sheriff sleeps with one eye open."*

### 11.3 `src/app/approvals/page.tsx` — Badge Approval queue

**Component tree**

```
<ApprovalsPage>
  <PageHeader title="Badge Approvals" right={<KbdHints/>}/>
  <ScrollArea>
    {pending.map(a => <ApprovalCard approval={a}/>)}
  </ScrollArea>
</ApprovalsPage>
```

**ApprovalCard contents (per pending approval)**

- Header: `approval.agent_label` (Rye), tool name (mono), countdown chip computed as `differenceInSeconds(new Date(approval.expires_at), new Date())` (ticks 1Hz, turns wanted-red at <15s). Do **not** compute the countdown from `created_at + 120s` — always use the server-provided `expires_at`.
- Body: classifier rationale (`reason`); humanised `user_explanation`; truncated `args` JSON in a parchment `<pre>`.
- Buttons:
  - **Approve** (allowed-green) — `useApproveDecision().mutate({ id, body: { action: "approve", scope: "once" } })`.
  - **Deny** (wanted-red) — same hook, action `"deny"`.
  - **Redact** (approval-amber) — opens `<Dialog>` showing a **read-only preview** of what the backend will strip server-side (attachments removed, sensitive strings scrubbed). The client never sends `redacted_args` in the body. On confirm, POST `{"action":"redact","scope":"once"}` — the backend performs the strip and re-runs the call. The preview is rendered from the same `approval.args` plus a server-side hint of what would be removed (best-effort; if the backend hasn't shipped a preview field yet, show the full `args` and a banner: "Backend will strip attachments and sensitive strings before re-running.").
  - **Always allow this recipient** / **Always allow this tool** — split menu under Approve.
- Keyboard shortcuts: `A` approve focused card, `D` deny focused card, `R` redact, `↑/↓` navigate. Use a `useHotkeys` snippet built on `keydown` listener (no extra dependency).
- Hint chips at top right: `<kbd>A</kbd> Approve · <kbd>D</kbd> Deny · <kbd>R</kbd> Redact`.
- After resolution: card slides out (`x: 60, opacity: 0` over 220ms); toast `Sheriff approved "<tool>"` (or denied/redacted).

**State bindings**

- Pending approvals from `useApprovals('pending')` + live updates via store.
- `pending = Object.values(useSheriffStore(s => s.approvals)).filter(a => a.state === "pending").sort(byCreatedDesc)`.

**Empty-state copy**

*"The Sheriff's docket is empty. Wait for a deputy to ask for a badge."*

### 11.4 `src/app/deputies/page.tsx`

**Component tree**

- `<DeputiesTable>` with shadcn `Table` columns: Name (bold + Rye small), State (Badge — allowed/approval/brown), Requests today, Blocked today, Last seen (`formatDistanceToNow(new Date(agent.last_seen_at))`), Actions. The "Requests today" and "Blocked today" columns are backend-computed — render the values verbatim, do not recompute on the client.
- Action buttons per row: `Jail` (visible if active), `Release` (visible if jailed), `Revoke` (visible always, danger).
- Row click → opens `<Sheet side="right">` with `<AgentTimeline agentId={id}/>` filtering audit to that agent.
- Search input top-right filters by `label || id`.

**State bindings**

- `agents = Object.values(useSheriffStore(s => s.agents))`.
- Mutations from `useJailAgent`, `useRevokeAgent`, `useReleaseAgent`.

**Empty-state copy**

*"No deputies appointed yet."*

### 11.5 `src/app/laws/page.tsx` — Town Laws (policy editor)

**Component tree**

```
<LawsPage>
  <Grid cols=12 gap=6>
    <Col span=4>
      <Section title="Templates">
        {templates.map(t =>
          <TemplateRow t onApply={()=> applyTemplate.mutate({name:t.name})}/>)}
      </Section>
    </Col>
    <Col span=8>
      <PolicyEditor yaml={data.yaml} onSave={onSave}/>
      <RuleAccordion rules={parsedRules}/>
    </Col>
  </Grid>
</LawsPage>
```

**PolicyEditor** — lazy-loaded CodeMirror (see §12) with YAML mode. Validation runs on save: client-side YAML parse via `yaml` package — wait, dependency-light, use `js-yaml` if needed; otherwise just rely on backend's 422. Inline error block under editor.

**RuleAccordion** — best-effort visual list of parsed rules with toggle switches. **Toggles are visual-only** — actual edits go through YAML save (mention this in a tooltip).

### 11.6 `src/app/ledger/page.tsx` — Sheriff's Ledger

**Component tree**

```
<LedgerPage>
  <FilterBar>
    <Select decision/>
    <Select agent/>
    <Input tool/>
    <DateRange/>
  </FilterBar>
  <VirtualizedAuditList items={filtered}/>
</LedgerPage>
```

- Use `@tanstack/react-virtual` when filtered length > 50.
- Each row: timestamp (mono, brass), `entry.agent_label` (backend-supplied — do not look up from the agents map), decision badge, tool, one-line reason. Hover → highlight. Click → Sheet with full JSON of `args`, `result || reason`, `policy_id`, `risk_score`, `user_explanation`. Use a `<pre>` with monospace + parchment background.

---

## 12. Component specs (and full TSX for the 3 critical ones)

### Component matrix

| Component | Props | States | Key interactions |
|---|---|---|---|
| `Sidebar` | none | active route, connection state | navigation, connection chip |
| `KpiCard` | `{label, value, icon, variant, suffix?}` | static; animates on value change | none |
| `AgentCard` | `{agent}` | hover | click → `/deputies?id=` |
| `AgentMiniCard` | `{agent}` | — | click navigates |
| `WantedPoster` | `{entry, size?}` | normal/hero | "View evidence" → Sheet |
| `ApprovalCard` | `{approval}` | pending/resolving | approve/deny/redact, kbd |
| `AuditTimeline` | `{filter?}` | virtualized when n>50 | row click → Sheet |
| `PolicyEditor` | `{yaml,onSave}` | dirty, saving, error | save, lazy-loaded |
| `ConnectionIndicator` | none | mocked/connected/connecting/disconnected | tooltip |
| `ConnectionBanner` | `{ state: "connected" \| "degraded" \| "disconnected" }` | hidden / shown | dismiss-less; Retry button refetches REST + forces WS reconnect |
| `TickerFeed` | `{entries, max=10}` | — | rows enter with ticker-in |
| `SlamInOverlay` | none | idle/animating | one-shot per `lastDenyId` |

#### `ConnectionBanner` — full spec

- **Props:** `{ state: "connected" | "degraded" | "disconnected" }`.
- **Derivation:** the banner reads `connectionState` from the Zustand store and the latest `useHealth()` result (5s poll). The mapping the parent passes in:
  - `connected`            → `connectionState === "connected"`.
  - `degraded`             → `connectionState !== "connected"` **and** `useHealth()` returned `{status:"ok"}` within the last 10s (REST works, WS reconnecting).
  - `disconnected`         → `connectionState !== "connected"` **and** `useHealth()` is failing.
  - `connectionState === "mocked"` is treated as `connected` (banner hidden).
- **Behaviour:** when `state !== "connected"` for **> 3s**, slide-down a parchment-coloured banner pinned to the top of the page (`fixed inset-x-0 top-0 z-50`). Use the 3s grace window so transient WS reconnects don't flicker. Banner copy:
  - `degraded`     → "Trail's a bit dusty — Sheriff's wire is reconnecting."
  - `disconnected` → "Outlaw country — no wire to the sheriff's office." with a `Retry` button.
- **Retry button:** invalidates `["agents"]`, `["approvals"]`, `["audit"]`, `["health"]` queries via `queryClient.invalidateQueries(...)`. The WS layer auto-reconnects via react-use-websocket — no manual socket handle needed.
- **Wiring:** rendered in `app/layout.tsx` between `<Providers>` and `<div className="flex min-h-screen">` so it sits on top of every page.
- **Accessibility:** `role="status"` `aria-live="polite"`. Honour `prefers-reduced-motion` (drop the slide-down).

```tsx
// src/components/ConnectionBanner.tsx
"use client";
import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { WifiOff, Wifi } from "lucide-react";
import { useQueryClient } from "@tanstack/react-query";
import { useSheriffStore } from "@/lib/store";
import { useHealth } from "@/lib/api";
import { Button } from "@/components/ui/button";

export function ConnectionBanner() {
  const conn = useSheriffStore(s => s.connectionState);
  const wsConnected = conn === "connected" || conn === "mocked";
  const health = useHealth(!wsConnected); // poll only when WS isn't up
  const qc = useQueryClient();

  const derived: "connected" | "degraded" | "disconnected" =
    wsConnected ? "connected"
    : health.data?.status === "ok" ? "degraded"
    : "disconnected";

  // 3s grace before showing — avoids flicker on quick WS reconnects.
  const [show, setShow] = useState(false);
  useEffect(() => {
    if (derived === "connected") { setShow(false); return; }
    const t = setTimeout(() => setShow(true), 3000);
    return () => clearTimeout(t);
  }, [derived]);

  return (
    <AnimatePresence>
      {show && derived !== "connected" && (
        <motion.div
          role="status" aria-live="polite"
          initial={{ y: -40, opacity: 0 }} animate={{ y: 0, opacity: 1 }} exit={{ y: -40, opacity: 0 }}
          transition={{ type: "spring", stiffness: 180, damping: 22 }}
          className="fixed inset-x-0 top-0 z-50 paper-flat border-b-2 border-approval px-6 py-3 flex items-center gap-4"
        >
          {derived === "disconnected"
            ? <WifiOff className="h-5 w-5 text-wanted" aria-hidden/>
            : <Wifi className="h-5 w-5 text-approval-dark" aria-hidden/>}
          <span className="font-rye text-brown-200">
            {derived === "disconnected"
              ? "Outlaw country — no wire to the sheriff's office."
              : "Trail's a bit dusty — Sheriff's wire is reconnecting."}
          </span>
          {derived === "disconnected" && (
            <Button
              size="sm" variant="outline"
              onClick={() => {
                qc.invalidateQueries({ queryKey: ["agents"] });
                qc.invalidateQueries({ queryKey: ["approvals"] });
                qc.invalidateQueries({ queryKey: ["audit"] });
                qc.invalidateQueries({ queryKey: ["health"] });
              }}
            >
              Retry
            </Button>
          )}
        </motion.div>
      )}
    </AnimatePresence>
  );
}
```

### 12.1 `src/components/KpiCard.tsx` (full TSX)

```tsx
"use client";
import { motion, AnimatePresence } from "framer-motion";
import { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

type Variant = "allowed" | "wanted" | "approval" | "ai";

const variantStyles: Record<Variant, { ring: string; text: string; icon: string; extra?: string }> = {
  allowed:  { ring: "ring-allowed",  text: "text-allowed",  icon: "text-allowed-dark"  },
  wanted:   { ring: "ring-wanted",   text: "text-wanted",   icon: "text-wanted-dark"   },
  approval: { ring: "ring-approval", text: "text-approval", icon: "text-approval-dark" },
  ai:       { ring: "ring-ai",       text: "text-ai",       icon: "text-ai",            extra: "ai-glow" },
};

export function KpiCard({
  label, value, icon: Icon, variant, suffix,
}: { label: string; value: number; icon: LucideIcon; variant: Variant; suffix?: string }) {
  const v = variantStyles[variant];
  return (
    <div className={cn(
      "paper-flat px-5 py-4 flex items-center gap-4 ring-1 ring-inset",
      v.ring, v.extra,
    )}>
      <div className={cn("h-12 w-12 grid place-items-center rounded-md bg-parchment-100 border border-brown/10", v.icon)}>
        <Icon className="h-6 w-6" aria-hidden />
      </div>
      <div className="flex-1">
        <div className="text-xs uppercase tracking-wider text-brown-50">{label}</div>
        <div className="flex items-baseline gap-1 leading-none">
          <AnimatePresence mode="popLayout">
            <motion.span
              key={value}
              initial={{ y: 10, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              exit={{ y: -10, opacity: 0 }}
              transition={{ type: "spring", stiffness: 180, damping: 22 }}
              className={cn("font-rye text-3xl", v.text)}
            >
              {value}
            </motion.span>
          </AnimatePresence>
          {suffix && <span className="text-xs text-brown-50">{suffix}</span>}
        </div>
      </div>
    </div>
  );
}
```

### 12.2 `src/components/WantedPoster.tsx` (full TSX)

```tsx
"use client";
import { motion } from "framer-motion";
import { Skull, Eye } from "lucide-react";
import { useState } from "react";
import { Sheet, SheetContent, SheetTrigger, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { format } from "date-fns";
import type { AuditEntryDTO } from "@/lib/types";
import { cn } from "@/lib/utils";

export function WantedPoster({ entry, size = "card" }: { entry: AuditEntryDTO; size?: "card" | "hero" }) {
  const [open, setOpen] = useState(false);
  const big = size === "hero";

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ type: "spring", stiffness: 180, damping: 22 }}
      className={cn(
        "paper relative",
        big ? "p-10 max-w-2xl mx-auto" : "p-6",
      )}
    >
      <div className="absolute top-3 right-3 wanted-stamp text-sm">Wanted</div>

      <div className="flex flex-col items-center text-center gap-3">
        <Skull className={cn("text-wanted", big ? "h-24 w-24" : "h-14 w-14")} aria-hidden/>
        <h2 className={cn("font-rye text-wanted", big ? "text-4xl" : "text-2xl")}>
          {entry.tool}
        </h2>
        <div className="text-xs uppercase tracking-widest text-brown-50">
          {entry.agent_label} · risk {entry.risk_score}
        </div>
        {/* Primary callout: humanised Sonnet explanation. Falls back to classifier reason if absent. */}
        <p className={cn("text-brown-200 max-w-prose font-semibold", big ? "text-lg" : "text-base")}>
          {entry.user_explanation ?? entry.reason}
        </p>
        {/* Subtitle: short policy-engine reason. Hidden when there is no user_explanation (would duplicate the callout above). */}
        {entry.user_explanation && (
          <p className={cn("text-brown-50 max-w-prose italic", big ? "text-sm" : "text-xs")}>
            {entry.reason}
          </p>
        )}
        <div className="text-[11px] text-brown-50">
          {format(new Date(entry.ts), "PP p")}{entry.policy_id ? ` · ${entry.policy_id}` : ""}
        </div>

        <Sheet open={open} onOpenChange={setOpen}>
          <SheetTrigger asChild>
            <Button variant="outline" size="sm" className="mt-2">
              <Eye className="mr-2 h-4 w-4"/> View evidence
            </Button>
          </SheetTrigger>
          <SheetContent side="right" className="w-[640px] max-w-full">
            <SheetHeader><SheetTitle className="font-rye text-wanted">Evidence — {entry.tool}</SheetTitle></SheetHeader>
            <div className="mt-4 space-y-3 text-sm">
              <Field label="Agent">{entry.agent_label} ({entry.agent_id})</Field>
              <Field label="Reason">{entry.reason}</Field>
              {entry.user_explanation && <Field label="Explanation">{entry.user_explanation}</Field>}
              <Field label="Policy">{entry.policy_id ?? "—"}</Field>
              <Field label="Args"><pre className="bg-parchment-100 p-3 rounded text-xs overflow-auto">{JSON.stringify(entry.args, null, 2)}</pre></Field>
              {entry.result !== undefined && <Field label="Result"><pre className="bg-parchment-100 p-3 rounded text-xs overflow-auto">{JSON.stringify(entry.result, null, 2)}</pre></Field>}
            </div>
          </SheetContent>
        </Sheet>
      </div>
    </motion.div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <div className="text-[11px] uppercase tracking-widest text-brown-50 mb-1">{label}</div>
      <div className="text-brown-200">{children}</div>
    </div>
  );
}
```

### 12.3 `src/components/ApprovalCard.tsx` (full TSX)

```tsx
"use client";
import { motion, AnimatePresence } from "framer-motion";
import { useEffect, useState } from "react";
import { Gavel, BadgeCheck, UserX, Pencil } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from "@/components/ui/dialog";
import { toast } from "sonner";
import { differenceInSeconds } from "date-fns";
import { useApproveDecision } from "@/lib/api";
import type { ApprovalDTO, ApprovalScope } from "@/lib/types";
import { cn } from "@/lib/utils";

export function ApprovalCard({ approval }: { approval: ApprovalDTO }) {
  const approve = useApproveDecision();
  const [resolving, setResolving] = useState<null | "approve" | "deny" | "redact">(null);
  const [secondsLeft, setSecondsLeft] = useState(() => differenceInSeconds(new Date(approval.expires_at), new Date()));

  useEffect(() => {
    const t = setInterval(() => setSecondsLeft(differenceInSeconds(new Date(approval.expires_at), new Date())), 1000);
    return () => clearInterval(t);
  }, [approval.expires_at]);

  const submit = async (action: "approve" | "deny" | "redact", scope: ApprovalScope = "once") => {
    setResolving(action);
    try {
      await approve.mutateAsync({ id: approval.id, body: { action, scope } });
      const verb = action === "approve" ? "approved" : action === "deny" ? "denied" : "redacted";
      toast.success(`Sheriff ${verb} ${approval.tool}`);
    } catch (e: any) {
      toast.error(`Failed: ${e.message ?? e}`);
      setResolving(null);
    }
  };

  const danger = secondsLeft <= 15;

  return (
    <AnimatePresence>
      {!resolving && (
        <motion.div
          layout
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ x: 60, opacity: 0 }}
          transition={{ type: "spring", stiffness: 180, damping: 22 }}
          className="paper-flat p-5 mb-4 border-l-4 border-approval"
          tabIndex={0}
          onKeyDown={(e) => {
            if (e.key.toLowerCase() === "a") submit("approve");
            if (e.key.toLowerCase() === "d") submit("deny");
          }}
        >
          <div className="flex items-start gap-4">
            <div className="h-12 w-12 grid place-items-center rounded-md bg-approval/10 text-approval-dark animate-pulse-amber">
              <Gavel className="h-6 w-6"/>
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-3 flex-wrap">
                <h3 className="font-rye text-xl text-brown-200 truncate">{approval.tool}</h3>
                <span className="text-xs uppercase tracking-widest text-brown-50">{approval.agent_label}</span>
                <span className={cn(
                  "text-xs px-2 py-0.5 rounded border",
                  danger ? "border-wanted text-wanted" : "border-approval text-approval-dark",
                )}>
                  {Math.max(secondsLeft, 0)}s left
                </span>
                <span className="text-xs text-brown-50">risk {approval.risk_score}</span>
              </div>
              <p className="mt-2 text-brown-200">{approval.user_explanation || approval.reason}</p>
              <pre className="mt-3 bg-parchment-100 p-3 rounded text-xs overflow-auto max-h-40">
                {JSON.stringify(approval.args, null, 2)}
              </pre>
              <div className="mt-4 flex flex-wrap gap-2">
                <Button onClick={() => submit("approve")} className="bg-allowed text-parchment hover:bg-allowed-dark">
                  <BadgeCheck className="mr-2 h-4 w-4"/> Approve <kbd className="ml-2 text-[10px] opacity-70">A</kbd>
                </Button>
                <Button onClick={() => submit("deny")} className="bg-wanted text-parchment hover:bg-wanted-dark">
                  <UserX className="mr-2 h-4 w-4"/> Deny <kbd className="ml-2 text-[10px] opacity-70">D</kbd>
                </Button>

                <RedactDialog approval={approval} onSubmit={() => submit("redact", "once")}/>

                <Button variant="outline" onClick={() => submit("approve", "always_recipient")}>
                  Always allow this recipient
                </Button>
                <Button variant="outline" onClick={() => submit("approve", "always_tool")}>
                  Always allow this tool
                </Button>
              </div>
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

// Redact dialog: READ-ONLY preview. The backend strips attachments + sensitive strings
// server-side. The client must NOT send `redacted_args` — only `{action:"redact", scope:"once"}`.
function RedactDialog({ approval, onSubmit }: { approval: ApprovalDTO; onSubmit: () => void }) {
  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button variant="outline" className="border-approval text-approval-dark">
          <Pencil className="mr-2 h-4 w-4"/> Redact <kbd className="ml-2 text-[10px] opacity-70">R</kbd>
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-2xl">
        <DialogHeader><DialogTitle className="font-rye">Redact and re-run</DialogTitle></DialogHeader>
        <p className="text-sm text-brown-200">
          The Sheriff's office will strip attachments and scrub sensitive strings on the server
          before re-running this call. The deputy will see only the cleaned arguments.
        </p>
        <pre className="bg-parchment-100 p-3 rounded text-xs overflow-auto max-h-64 font-mono">
          {JSON.stringify(approval.args, null, 2)}
        </pre>
        <DialogFooter>
          <Button onClick={onSubmit} className="bg-approval text-parchment hover:bg-approval-dark">
            Confirm redaction
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
```

(Other components — `Sidebar`, `AgentCard`, `AuditTimeline`, `PolicyEditor`, `ConnectionIndicator`, `TickerFeed`, `SlamInOverlay` — are straightforward applications of the rules above. Build them last; they don't need full TSX in this spec. Sidebar uses lucide icons listed in §6 plus `<ConnectionIndicator/>` at the bottom. ConnectionIndicator: green dot for `connected`, brass dot for `mocked`, red dot + label "Outlaw country — no backend" for `disconnected`/`connecting`. While the WS state is `disconnected` or `connecting`, ConnectionIndicator calls `useHealth(true)` (passive `GET /health` ping every 5s) to surface a softer "backend reachable, WS reconnecting" intermediate state when `health.status === "ok"` but the socket has not yet opened.)

`src/lib/utils.ts`:

```ts
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
export const cn = (...inputs: ClassValue[]) => twMerge(clsx(inputs));
```

---

## 13. Stub-first dev plan (hour 0–2): mocks

While Person 1's backend is partial, run the dashboard end-to-end with `NEXT_PUBLIC_USE_MOCKS=1`.

### Mock router — `src/mocks/router.ts`

```ts
import { z } from "zod";
import agents    from "./agents.json";
import approvals from "./approvals.json";
import audit     from "./audit.json";
import policies  from "./policies.json";
import templates from "./policy-templates.json";

// ----- Zod schemas mirroring lib/types.ts. Used ONLY in dev to fail loudly when
// fixtures drift from the reconciled DTO shapes. Run once at module load.
const zDecision    = z.enum(["allow", "deny", "approval_required"]);
const zAgentState  = z.enum(["active", "jailed", "revoked"]);
const zApprovalAct = z.enum(["approve", "deny", "redact"]);
const zApprovalSt  = z.enum(["pending", "approved", "denied", "redacted", "timed_out"]);

const zAgent = z.object({
  id: z.string(),
  label: z.string(),
  state: zAgentState,
  created_at: z.string(),
  last_seen_at: z.string(),
  jailed_reason: z.string().optional(),
  requests_today: z.number(),
  blocked_today: z.number(),
});

const zApproval = z.object({
  id: z.string(),
  created_at: z.string(),
  expires_at: z.string(),
  agent_id: z.string(),
  agent_label: z.string(),
  tool: z.string(),
  args: z.record(z.unknown()),
  reason: z.string(),
  user_explanation: z.string().optional(),
  risk_score: z.number(),
  state: zApprovalSt,
  resolved_action: zApprovalAct.optional(),
  resolved_scope: z.enum(["once", "always_recipient", "always_tool"]).optional(),
});

const zAuditEntry = z.object({
  id: z.string(),
  ts: z.string(),
  agent_id: z.string(),
  agent_label: z.string(),
  tool: z.string(),
  args: z.record(z.unknown()),
  decision: zDecision,
  reason: z.string(),
  policy_id: z.string().optional(),
  risk_score: z.number(),
  user_explanation: z.string().nullable().optional(),
  result: z.unknown().optional(),
});

// Fail loudly at module load if any fixture has drifted from the DTO shape.
// This prevents silent FE/BE divergence — fix the fixture, never the schema.
function validateFixtures(): void {
  const agentsR    = z.array(zAgent).safeParse(agents);
  const approvalsR = z.array(zApproval).safeParse(approvals);
  const auditR     = z.array(zAuditEntry).safeParse(audit);
  if (!agentsR.success)    throw new Error(`agents.json drift: ${JSON.stringify(agentsR.error.issues, null, 2)}`);
  if (!approvalsR.success) throw new Error(`approvals.json drift: ${JSON.stringify(approvalsR.error.issues, null, 2)}`);
  if (!auditR.success)     throw new Error(`audit.json drift: ${JSON.stringify(auditR.error.issues, null, 2)}`);
}
validateFixtures();

export async function mockFetch<T>(path: string, init?: RequestInit): Promise<T> {
  await new Promise(r => setTimeout(r, 120));
  if (path === "/health") return ({ status: "ok", ts: new Date().toISOString() } as unknown as T);
  if (path === "/v1/agents") return agents as T;
  if (path.startsWith("/v1/approvals?state=pending")) return approvals as T;
  if (path === "/v1/approvals") return approvals as T;
  if (path.startsWith("/v1/audit")) return audit as T; // ignores limit/agent_id/decision/since in the mock
  if (path === "/v1/policies") return policies as T;
  if (path === "/v1/policies/templates") return templates as T;
  if (path.startsWith("/v1/approvals/") && init?.method === "POST") {
    const body = JSON.parse(init.body as string);
    return { id: path.split("/").pop(), state: body.action === "approve" ? "approved" : "denied", ...body } as unknown as T;
  }
  if (path.startsWith("/v1/agents/") && init?.method === "POST") return ({} as T);
  if (path.startsWith("/v1/demo/run/")) return ({ started: true, pid: 4242 } as unknown as T);
  if (path === "/v1/policies" && init?.method === "PUT") return policies as T;
  if (path === "/v1/policies/apply-template") return policies as T;
  throw new Error(`Mock missing for ${path}`);
}
```

### Fixtures (drop-in JSON)

`src/mocks/agents.json`

```json
[
  {"id":"deputy-dusty","label":"Deputy Dusty","state":"active","created_at":"2026-04-24T12:00:00Z","last_seen_at":"2026-04-24T14:00:00Z","requests_today":12,"blocked_today":1},
  {"id":"posse-pat","label":"Posse Pat","state":"active","created_at":"2026-04-24T12:05:00Z","last_seen_at":"2026-04-24T13:51:00Z","requests_today":4,"blocked_today":0},
  {"id":"outlaw-otto","label":"Outlaw Otto","state":"jailed","created_at":"2026-04-24T12:10:00Z","last_seen_at":"2026-04-24T13:30:00Z","jailed_reason":"Attempted data exfiltration","requests_today":2,"blocked_today":2}
]
```

`src/mocks/approvals.json`

```json
[
  {"id":"a-1","created_at":"2026-04-24T13:58:00Z","expires_at":"2026-04-24T14:00:00Z","agent_id":"deputy-dusty","agent_label":"Deputy Dusty",
   "tool":"gmail.send_email","args":{"to":"accountant@example.com","subject":"Invoice","attachments":["invoice.pdf"]},
   "reason":"External recipient + attachment","user_explanation":"Looks legit but external — Sheriff should sign off.",
   "risk_score":52,"state":"pending"}
]
```

`src/mocks/audit.json`

```json
[
  {"id":"e-3","ts":"2026-04-24T13:58:30Z","agent_id":"deputy-dusty","agent_label":"Deputy Dusty","tool":"calendar.create_event","args":{"title":"Sync","starts_at":"..."},"decision":"allow","reason":"Within policy","risk_score":4},
  {"id":"e-2","ts":"2026-04-24T13:57:00Z","agent_id":"outlaw-otto","agent_label":"Outlaw Otto","tool":"gmail.send_email","args":{"to":"outlaw@badmail.com","attachments":["contacts.csv"]},"decision":"deny","reason":"Data exfiltration: external recipient + sensitive attachment","user_explanation":"This deputy tried to ship the contacts list to an outlaw — blocked.","policy_id":"no-external-pii","risk_score":91},
  {"id":"e-1","ts":"2026-04-24T13:56:00Z","agent_id":"deputy-dusty","agent_label":"Deputy Dusty","tool":"gmail.read_inbox","args":{"max":5},"decision":"allow","reason":"Read-only","risk_score":3}
]
```

`src/mocks/policies.json`

```json
{ "yaml": "rules:\n  - id: no-external-pii\n    when: tool == 'gmail.send_email'\n    deny_if: contains(args.attachments, 'contacts.csv')\n", "updated_at": "2026-04-24T13:00:00Z" }
```

`src/mocks/policy-templates.json`

```json
[
  {"name":"default","description":"Sensible defaults"},
  {"name":"healthcare","description":"HIPAA-friendly"},
  {"name":"finance","description":"SOX/PII conservative"},
  {"name":"startup","description":"Move fast, log everything"}
]
```

Ship `frontend/.env.local.example`:

```
# IMPORTANT — these URLs are baked into the JS bundle at BUILD time (NEXT_PUBLIC_*)
# and resolved by the BROWSER, which runs on the developer's HOST — not inside the
# frontend container. Therefore they MUST point at the host-visible address of the
# backend gateway (typically http://localhost:8000), NOT the inter-container DNS
# name `backend:8000`. Using `backend:8000` here will work in `docker compose exec`
# shells but will fail in the browser with ERR_NAME_NOT_RESOLVED.
#
# The `backend:8000` hostname is only valid for inter-container traffic
# (e.g. OpenClaw → backend gateway), which is Person 4's concern, not this app's.
NEXT_PUBLIC_API_BASE=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000/v1/stream
NEXT_PUBLIC_USE_MOCKS=0
NEXT_PUBLIC_POLL_FALLBACK=0
```

> **Browser vs container URLs.** `NEXT_PUBLIC_*` values are inlined at build time and run in the browser. The browser is **not** on the docker network, so it cannot resolve `backend:8000`. Always use `http://localhost:8000` / `ws://localhost:8000/v1/stream` in the frontend env. If the demo runs on a remote host, replace `localhost` with that host's reachable name/IP — never with a docker-internal hostname.

> **Env-var naming is locked.** Use `NEXT_PUBLIC_WS_URL` (full ws:// URL including the `/v1/stream` path). Do **not** introduce `NEXT_PUBLIC_WS_BASE` or any other variant — code, mocks, README, and demo runbook must all reference `NEXT_PUBLIC_WS_URL`.

---

## 14. Hour-by-hour plan

| Hours | Work | Definition of done |
|---|---|---|
| **H0–2** | Scaffold, install deps, drop in `package.json`/`tailwind.config.ts`/`globals.css`/`layout.tsx`/`Providers.tsx`/`utils.ts`, build `Sidebar`, build `KpiCard`, render Town Overview with `NEXT_PUBLIC_USE_MOCKS=1`. Sidebar shows mocked connection chip. | `npm run dev` shows the Town Overview with green theme, real KPIs from fixtures, no console errors. Person 1 can hit you with real `/v1/agents` and your KPIs reflect it. |
| **H2–6** | Wanted Board page + WantedPoster + SlamInOverlay; Approvals page + ApprovalCard + redact dialog. Wire WS via mocked replay (drop a `setInterval` that synthesises `audit` frames if `USE_MOCKS=1`). | Deny entries appear on Wanted Board; new ones trigger slam-in. Approval card renders with countdown and four buttons. Approve toast appears. |
| **H6–10** | Deputies table + Sheet timeline; Ledger virtualized list + filters + Sheet detail; Laws page with template list + lazy-loaded CodeMirror editor. | All five non-overview routes render real or mocked data. `npm run typecheck` clean. |
| **H10–14** | Real WebSocket integration. Hydration on mount via `useAgents/useApprovals/useAudit` → `hydrateFromRest`. Animation polish (spring tuning, ticker enter, KPI roll). Loading skeletons + every empty-state copy from §11. Run all 3 demo scenarios with Person 2's Dusty against Person 1's gateway. | Three scenarios light up the UI in the right places end-to-end. |
| **H14–18** | Demo rehearsal at projector resolution (1080p). Bump font size if hard to read. Fix top 3 visual issues. Verify `prefers-reduced-motion`. Lighthouse pass. Build + `npm start` for the demo machine. | Final video record made (Person 4 owns), backup `record-fallback.mp4` produced. |

---

## 15. Accessibility & projector readiness

- Minimum on-screen font 14px (already set in Tailwind config).
- All body text uses `text-brown-200` on parchment → 9.4:1.
- `:focus-visible` brass ring is 2px solid — visible from 30 ft.
- All buttons reachable by Tab; cards in Approvals and Wanted Board have `tabIndex={0}` and key handlers.
- Headings step h1 → h2 → h3, no heading skip.
- `prefers-reduced-motion` collapses all animations to 0.001ms (built into globals.css).
- `aria-hidden` on decorative icons; meaningful icons get an accessible `aria-label`.
- Colour is never the sole signal: deny entries always have a Skull icon, approvals always have a Gavel + countdown text, allows always have BadgeCheck.

---

## 16. Acceptance criteria

1. `cd frontend && npm run dev` on port 3000 renders Town Overview with no console errors, with `NEXT_PUBLIC_USE_MOCKS=1`.
2. With Person 1's backend running and Person 2's Deputy Dusty firing, the three demo scenarios produce, in order:
   - **Good**: two new green entries in the ticker; KPI `Allowed today` increments by 2.
   - **Injection**: Wanted Poster slam-in within 100ms of the deny frame; `Outlaw Otto` (or whichever agent) appears as `jailed` in Active Deputies; KPI `Blocked today` increments.
   - **Approval**: An ApprovalCard appears on `/approvals`. Clicking Approve closes the card within 200ms perceived latency and toasts success. The original `/v1/tool-call` HTTP response unblocks on the gateway side (Person 1 verifies).
3. Slam-in animation start time ≤ 100ms after the WS frame is received.
4. Approve click → mutation fired → store update → toast: ≤ 200ms.
5. Lighthouse desktop performance ≥ 85 (run with `--preset=desktop` against the production build).
6. `npm run typecheck` passes.
7. App is usable via keyboard alone on Approvals and Deputies pages.

---

## 17. Risks and fallbacks

| Risk | Mitigation | Fallback |
|---|---|---|
| CodeMirror bundle inflates first load | Dynamic-import `PolicyEditor` with `next/dynamic({ ssr: false })`; route-level code-split. | Replace with plain `<Textarea className="font-mono">` if bundle > 1MB. |
| WebSocket flakiness on demo wifi | Exponential backoff already implemented; server pushes JSON `HeartbeatFrame` every 15s, react-use-websocket auto-reconnects on close (no client-side ping/pong). | Behind `NEXT_PUBLIC_POLL_FALLBACK=1` flag, run `setInterval` polls every 1s on `/v1/agents` + `/v1/approvals?state=pending` + `useAudit({ limit: 20, since: <last-seen-ts> })` and merge into the store via `hydrateFromRest`. Wire this in `useStreamBootstrap`: if `connectionState === "disconnected"` for >5s **and** `useHealth()` is returning `{status:"ok"}`, start polling; stop when WS reopens. |
| Animation stutter on projector | `prefers-reduced-motion` honoured; springs tuned to stiffness 180 (not bouncier). | If still stutters, swap framer-motion variants for plain CSS transitions on the affected route. |
| Backend changes a DTO last-minute | Types are mirrored in one file (`lib/types.ts`); a sync diff is one commit. | Keep an end-to-end smoke script that hits `/v1/agents` and JSON-schema-validates with Zod (`AgentDTO` zod schema next to the type). |
| Person 1 doesn't ship `POST /v1/demo/run/{scenario_id}` (P1-owned) | Demo bar uses tooltip with the manual command. Don't block on it. | Document the manual command (`uv run python -m agentsheriff.demo.deputy_dusty --scenario good`) on the empty-state of Town Overview. |

---

## 18. Cross-team contracts (what you depend on)

- **Person 1** must expose: `GET /health`, `GET /v1/agents`, `GET /v1/audit?limit=&agent_id=&decision=&since=`, `GET /v1/approvals?state=pending`, `POST /v1/approvals/{id}`, `GET/PUT /v1/policies`, `GET /v1/policies/templates`, `POST /v1/policies/apply-template`, `POST /v1/agents/{id}/{jail|revoke|release}`, `WS /v1/stream` with frames per shared-context, and `POST /v1/demo/run/{scenario_id}` returning `{started: boolean, pid?: number}` (P1 owns this endpoint — it shells out to Deputy Dusty).
- **Person 2** authors `backend/src/agentsheriff/demo/scenarios/{good,injection,approval}.json` so the visual outcomes match §16. They run Dusty.
- **Person 4** owns DTO field names (`user_explanation`, `risk_score`, etc.). If they rename a field, this spec's `lib/types.ts` is the single update point on the FE side.
- You **publish** nothing back; you read-only the API.

---

### Critical Files for Implementation

- /Users/ianrowe/git/Agent_Sheriff/frontend/src/app/layout.tsx
- /Users/ianrowe/git/Agent_Sheriff/frontend/src/lib/store.ts
- /Users/ianrowe/git/Agent_Sheriff/frontend/src/lib/ws.ts
- /Users/ianrowe/git/Agent_Sheriff/frontend/src/components/WantedPoster.tsx
- /Users/ianrowe/git/Agent_Sheriff/frontend/src/components/ApprovalCard.tsx

---

**Note to caller:** I cannot create `specs/person-3-dashboard-ui.md` from within this read-only planning agent. Paste the spec above (everything between the top horizontal rule and the "Critical Files for Implementation" section) into that file. The file does not currently exist on disk — only `specs/_shared-context.md` is present.