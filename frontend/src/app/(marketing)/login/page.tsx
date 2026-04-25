"use client";

import Link from "next/link";
import { GOOGLE_SIGNIN_URL } from "@/lib/api";

export default function LoginPage() {
  const startGoogle = () => {
    window.location.href = GOOGLE_SIGNIN_URL;
  };

  return (
    <main className="flex flex-1 items-center justify-center p-8">
      <div className="w-full max-w-md border border-brass/40 bg-parchment-deep/40 p-8 shadow-[4px_4px_0_#2b1810]">
        <div className="mb-8 flex flex-col items-center gap-3 text-center">
          <div className="text-brass-dark">
            <svg width="40" height="40" aria-hidden>
              <use href="#sheriff-star" />
            </svg>
          </div>
          <h1 className="font-heading text-3xl text-ink">
            Sign in to the office
          </h1>
          <p className="text-sm text-ink-soft">
            The Sheriff reviews every badge at the door.
          </p>
        </div>

        <button
          type="button"
          onClick={startGoogle}
          className="flex w-full items-center justify-center gap-3 border border-ink bg-parchment px-4 py-3 text-sm font-semibold text-ink transition hover:bg-ink hover:text-parchment"
        >
          <GoogleGlyph />
          Sign in with Google
        </button>

        <p className="mt-6 text-center">
          <Link
            href="/"
            className="font-mono text-[10px] uppercase tracking-[0.22em] text-ink-soft underline-offset-4 hover:text-ink hover:underline"
          >
            ← Back to landing
          </Link>
        </p>
      </div>
    </main>
  );
}

function GoogleGlyph() {
  return (
    <svg
      width="18"
      height="18"
      viewBox="0 0 24 24"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden
    >
      <path
        fill="#4285F4"
        d="M23.49 12.27c0-.83-.07-1.63-.21-2.41H12v4.56h6.44c-.28 1.48-1.12 2.74-2.39 3.58v2.98h3.86c2.26-2.08 3.58-5.14 3.58-8.71z"
      />
      <path
        fill="#34A853"
        d="M12 24c3.24 0 5.95-1.08 7.93-2.92l-3.86-2.98c-1.07.72-2.44 1.14-4.07 1.14-3.13 0-5.78-2.11-6.73-4.96H1.28v3.1C3.25 21.3 7.31 24 12 24z"
      />
      <path
        fill="#FBBC05"
        d="M5.27 14.28a7.18 7.18 0 0 1 0-4.56v-3.1H1.28a12 12 0 0 0 0 10.76l3.99-3.1z"
      />
      <path
        fill="#EA4335"
        d="M12 4.75c1.77 0 3.35.61 4.6 1.8l3.43-3.43C17.95 1.19 15.24 0 12 0 7.31 0 3.25 2.7 1.28 6.62l3.99 3.1C6.22 6.86 8.87 4.75 12 4.75z"
      />
    </svg>
  );
}
