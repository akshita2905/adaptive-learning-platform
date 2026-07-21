import React, { useEffect, useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import api from "../api/client.js";
import Card from "../components/Card.jsx";
import Layout from "../components/Layout.jsx";
import { useAuth } from "../context/AuthContext.jsx";

/**
 * Email/password login; stores JWT via AuthContext.
 */
export default function LoginPage() {
  const navigate = useNavigate();
  const { login, isAuthenticated } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    document.title = "Sign in — Learning Path";
  }, []);

  if (isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  const onSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const { data } = await api.post("/login", { email, password });
      login(data);
      navigate("/");
    } catch (err) {
      const msg = err.response?.data?.detail || err.message || "Login failed";
      setError(typeof msg === "string" ? msg : JSON.stringify(msg));
    } finally {
      setLoading(false);
    }
  };

  return (
    <Layout title="Sign in">
      <div className="mx-auto max-w-md">
        <Card>
          <form onSubmit={onSubmit} className="space-y-4">
            {error && (
              <p className="rounded-lg border border-red-500/40 bg-red-950/40 px-3 py-2 text-sm text-red-200">
                {error}
              </p>
            )}
            <div>
              <label className="mb-1 block text-sm text-slate-400">Email</label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full rounded-xl border border-slate-600 bg-slate-900/80 px-4 py-2.5 text-white outline-none ring-brand-500/0 transition focus:ring-2 focus:ring-brand-500"
              />
            </div>
            <div>
              <label className="mb-1 block text-sm text-slate-400">Password</label>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full rounded-xl border border-slate-600 bg-slate-900/80 px-4 py-2.5 text-white outline-none focus:ring-2 focus:ring-brand-500"
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-xl bg-brand-600 py-3 font-semibold text-white shadow-glow transition hover:bg-brand-500 disabled:opacity-60"
            >
              {loading ? "Signing in…" : "Sign in"}
            </button>
          </form>
          <p className="mt-6 text-center text-sm text-slate-500">
            No account?{" "}
            <Link to="/register" className="text-brand-400 hover:underline">
              Register
            </Link>
          </p>
        </Card>
      </div>
    </Layout>
  );
}
