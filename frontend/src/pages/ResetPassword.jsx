import { useState, useEffect } from "react";
import { Link, useSearchParams, useNavigate } from "react-router-dom";
import { KeyRound, ArrowLeft, CheckCircle2 } from "lucide-react";

export function ResetPassword() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token");
  const navigate = useNavigate();

  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [status, setStatus] = useState("idle"); // 'idle' | 'loading' | 'success' | 'error'
  const [message, setMessage] = useState("");

  useEffect(() => {
    if (!token) {
      setStatus("error");
      setMessage("Invalid or missing reset token.");
    }
  }, [token]);

  async function onSubmit(e) {
    e.preventDefault();
    if (password !== confirmPassword) {
      setStatus("error");
      setMessage("Passwords do not match");
      return;
    }
    if (password.length < 6) {
      setStatus("error");
      setMessage("Password must be at least 6 characters long");
      return;
    }

    setStatus("loading");
    setMessage("");

    try {
      const res = await fetch("/api/auth/reset-password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, new_password: password }),
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Something went wrong");
      }
      setStatus("success");
      setMessage(data.message || "Password has been reset successfully!");
    } catch (err) {
      setStatus("error");
      setMessage(err instanceof Error ? err.message : "Failed to reset password");
    }
  }

  if (!token) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-slate-50 to-blue-50/30 px-4 py-12 relative overflow-hidden">
        <div className="absolute top-0 -left-4 w-72 h-72 bg-blue-400 rounded-full mix-blend-multiply filter blur-3xl opacity-10 animate-blob"></div>
        <div className="absolute top-0 -right-4 w-72 h-72 bg-emerald-400 rounded-full mix-blend-multiply filter blur-3xl opacity-10 animate-blob animation-delay-2000"></div>

        <div className="relative w-full max-w-md rounded-3xl border border-white/40 bg-white/70 backdrop-blur-xl p-8 sm:p-10 shadow-2xl shadow-blue-900/5 text-center">
          <h1 className="text-2xl font-bold tracking-tight text-red-600">Invalid Link</h1>
          <p className="mt-3 text-sm text-slate-600">The password reset link is invalid or has expired.</p>
          <Link to="/login" className="mt-8 inline-flex items-center gap-2 text-sm font-semibold text-blue-600 hover:text-blue-700 transition-colors">
            <ArrowLeft className="h-4 w-4" /> Go back to Login
          </Link>
        </div>
      </div>
    );
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
          <h1 className="font-display text-3xl font-bold tracking-tight text-slate-900">Reset Password</h1>
          <p className="mt-3 text-sm text-slate-500 px-4">
            Please enter your new password below.
          </p>
        </div>

        {status === "success" ? (
          <div className="rounded-2xl bg-emerald-50/80 p-8 text-center backdrop-blur-sm border border-emerald-100/50">
            <div className="mx-auto mb-5 flex h-14 w-14 items-center justify-center rounded-full bg-emerald-100 text-emerald-600 shadow-inner">
              <CheckCircle2 className="h-7 w-7" />
            </div>
            <p className="font-medium text-emerald-800">{message}</p>
            <button
              onClick={() => navigate("/login?reset=success")}
              className="mt-8 w-full rounded-xl bg-gradient-to-r from-emerald-500 to-teal-600 px-4 py-3 text-sm font-semibold text-white shadow-md shadow-emerald-500/20 transition-all hover:shadow-lg hover:shadow-emerald-500/30 hover:-translate-y-0.5"
            >
              Log In Now
            </button>
          </div>
        ) : (
          <form onSubmit={onSubmit} className="space-y-5">
            <div>
              <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-600" htmlFor="password">
                New Password
              </label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full rounded-xl border border-slate-200 bg-white/50 px-4 py-3 text-sm outline-none transition-all placeholder:text-slate-400 focus:border-blue-500 focus:bg-white focus:ring-4 focus:ring-blue-500/10"
                required
                minLength={6}
                placeholder="••••••••"
              />
            </div>
            <div>
              <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-600" htmlFor="confirmPassword">
                Confirm Password
              </label>
              <input
                id="confirmPassword"
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="w-full rounded-xl border border-slate-200 bg-white/50 px-4 py-3 text-sm outline-none transition-all placeholder:text-slate-400 focus:border-blue-500 focus:bg-white focus:ring-4 focus:ring-blue-500/10"
                required
                minLength={6}
                placeholder="••••••••"
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
              className="mt-4 w-full rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 px-4 py-3 text-sm font-semibold text-white shadow-md shadow-blue-500/20 transition-all hover:shadow-lg hover:shadow-blue-500/30 hover:-translate-y-0.5 disabled:opacity-70 disabled:hover:translate-y-0"
            >
              {status === "loading" ? (
                <span className="flex items-center justify-center gap-2">
                  <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/20 border-t-white"></span>
                  Resetting...
                </span>
              ) : (
                "Reset Password"
              )}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
