import React from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";

/**
 * Shell with header, branding, and auth actions.
 */
export default function Layout({ children, title }) {
  const { user, logout, isAuthenticated } = useAuth();

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <header className="border-b border-slate-800/80 bg-slate-950/80 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4">
          <Link to="/" className="font-display text-xl font-semibold tracking-tight text-white">
            Learning<span className="text-brand-500">Path</span>
          </Link>
          {isAuthenticated && (
            <div className="flex items-center gap-4 text-sm text-slate-400">
              <span className="hidden sm:inline">{user?.full_name}</span>
              <button
                type="button"
                onClick={logout}
                className="rounded-lg border border-slate-700 px-3 py-1.5 text-slate-200 transition hover:border-brand-500/50 hover:text-white"
              >
                Log out
              </button>
            </div>
          )}
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-4 py-10">
        {title && (
          <h1 className="font-display mb-8 text-3xl font-bold text-white text-balance md:text-4xl">
            {title}
          </h1>
        )}
        {children}
      </main>
    </div>
  );
}
