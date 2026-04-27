import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { GraduationCap } from "lucide-react";
import { useAuth } from "../context/AuthContext";

export function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("alex@learnflow.demo");
  const [password, setPassword] = useState("learnflow123");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [searchParams] = useSearchParams();
  const resetSuccess = searchParams.get("reset") === "success";

  async function onSubmit(e) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      await login(email, password);
      navigate("/dashboard", { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-100 px-4">
      <div className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-8 shadow-xl shadow-slate-200/50">
        <div className="mb-8 flex flex-col items-center text-center">
          <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-blue-600 text-white">
            <GraduationCap className="h-8 w-8" />
          </div>
          <h1 className="font-display text-2xl text-slate-900">LearnFlow</h1>
          <p className="mt-1 text-sm text-slate-500">Sign in to continue learning</p>
        </div>

        {resetSuccess && (
          <div className="mb-6 rounded-lg bg-emerald-50 p-3 text-center text-sm font-medium text-emerald-800 border border-emerald-100 animate-in fade-in slide-in-from-top-2">
            Password reset successfully. Please log in with your new password.
          </div>
        )}

        <form onSubmit={onSubmit} className="space-y-4">
          <div>
            <label className="mb-1 block text-xs font-medium text-slate-600" htmlFor="email">
              Email
            </label>
            <input
              id="email"
              type="email"
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none ring-blue-500/30 focus:ring-2"
              required
            />
          </div>
          <div>
            <div className="mb-1 flex items-center justify-between">
              <label className="block text-xs font-medium text-slate-600" htmlFor="password">
                Password
              </label>
              <Link to="/forgot-password" className="text-xs font-semibold text-blue-600 hover:underline">
                Forgot Password?
              </Link>
            </div>
            <input
              id="password"
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none ring-blue-500/30 focus:ring-2"
              required
            />
          </div>
          {error ? <p className="text-sm text-red-600">{error}</p> : null}
          <button
            type="submit"
            disabled={busy}
            className="w-full rounded-lg bg-blue-600 py-2.5 text-sm font-semibold text-white transition hover:bg-blue-700 disabled:opacity-60"
          >
            {busy ? "Signing in…" : "Sign in"}
          </button>
        </form>
        <p className="mt-6 text-center text-xs text-slate-500">
          New here?{" "}
          <Link to="/signup" className="font-semibold text-blue-700 hover:underline">
            Create an account
          </Link>
        </p>
        <p className="mt-6 text-center text-xs text-slate-400">
          Demo: seed the database, then use <span className="font-mono text-slate-600">alex@learnflow.demo</span>
        </p>
      </div>
    </div>
  );
}
