import { useState } from "react";
import { Link } from "react-router-dom";
import { KeyRound, ArrowLeft } from "lucide-react";

export function ForgotPassword() {
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState("idle"); // 'idle' | 'loading' | 'success' | 'error'
  const [message, setMessage] = useState("");

  async function onSubmit(e) {
    e.preventDefault();
    setStatus("loading");
    setMessage("");

    try {
      const res = await fetch("/api/auth/forgot-password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Something went wrong");
      }
      setStatus("success");
      setMessage(data.message || "Reset link sent!");
    } catch (err) {
      setStatus("error");
      setMessage(err instanceof Error ? err.message : "Failed to send reset link");
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-slate-50 to-blue-50/30 px-4 py-12 sm:px-6 lg:px-8 relative overflow-hidden">
      {/* Decorative background blobs */}
      <div className="absolute top-0 -left-4 w-72 h-72 bg-blue-400 rounded-full mix-blend-multiply filter blur-3xl opacity-10 animate-blob"></div>
      <div className="absolute top-0 -right-4 w-72 h-72 bg-emerald-400 rounded-full mix-blend-multiply filter blur-3xl opacity-10 animate-blob animation-delay-2000"></div>
      <div className="absolute -bottom-8 left-20 w-72 h-72 bg-indigo-400 rounded-full mix-blend-multiply filter blur-3xl opacity-10 animate-blob animation-delay-4000"></div>

      <div className="relative w-full max-w-md rounded-3xl border border-white/40 bg-white/70 backdrop-blur-xl p-8 sm:p-10 shadow-2xl shadow-blue-900/5">
        <div className="mb-8 flex flex-col items-center text-center">
          <div className="mb-6 flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-blue-500 to-indigo-600 text-white shadow-lg shadow-blue-500/30 transform transition hover:scale-105">
            <KeyRound className="h-8 w-8" />
          </div>
          <h1 className="font-display text-3xl font-bold tracking-tight text-slate-900">Forgot Password</h1>
          <p className="mt-3 text-sm text-slate-500 px-4">
            Enter your email address and we'll send you a secure link to reset your password.
          </p>
        </div>

        {status === "success" ? (
          <div className="rounded-xl bg-emerald-50 p-4 text-center">
            <p className="text-sm font-medium text-emerald-800">{message}</p>
            <Link
              to="/login"
              className="mt-6 inline-flex items-center gap-2 text-sm font-semibold text-emerald-700 hover:text-emerald-800"
            >
              <ArrowLeft className="h-4 w-4" /> Back to Login
            </Link>
          </div>
        ) : (
          <form onSubmit={onSubmit} className="space-y-4">
            <div>
              <label className="mb-1 block text-xs font-medium text-slate-600" htmlFor="email">
                Email Address
              </label>
              <input
                id="email"
                type="email"
                autoComplete="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full rounded-xl border border-slate-200 bg-white/50 px-4 py-3 text-sm outline-none transition-all placeholder:text-slate-400 focus:border-blue-500 focus:bg-white focus:ring-4 focus:ring-blue-500/10"
                required
                placeholder="name@example.com"
              />
            </div>
            {status === "error" ? (
              <div className="rounded-lg bg-red-50 p-3 text-sm text-red-600 border border-red-100 animate-in fade-in slide-in-from-top-2">
                {message}
              </div>
            ) : null}
            <button
              type="submit"
              disabled={status === "loading"}
              className="mt-6 w-full rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 px-4 py-3 text-sm font-semibold text-white shadow-md shadow-blue-500/20 transition-all hover:shadow-lg hover:shadow-blue-500/30 hover:-translate-y-0.5 disabled:opacity-70 disabled:hover:translate-y-0"
            >
              {status === "loading" ? (
                <span className="flex items-center justify-center gap-2">
                  <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/20 border-t-white"></span>
                  Sending...
                </span>
              ) : (
                "Send Reset Link"
              )}
            </button>
            <div className="mt-6 text-center">
              <Link
                to="/login"
                className="inline-flex items-center gap-2 text-xs font-medium text-slate-500 hover:text-slate-700"
              >
                <ArrowLeft className="h-3 w-3" /> Back to Login
              </Link>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
