import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function LoginPage() {
  const { login, isAuthenticated, status } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (status !== "loading" && isAuthenticated) {
      navigate("/alerts", { replace: true });
    }
  }, [isAuthenticated, navigate, status]);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      await login(email.trim(), password);
      navigate("/alerts", { replace: true });
    } catch (err: any) {
      setError(err?.message || "Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#080604]">
      <form onSubmit={handleSubmit} className="p-6 bg-[#0b0b0b] rounded shadow-md w-full max-w-sm border border-zinc-900">
        <h2 className="text-white text-lg mb-4">Sign in</h2>
        {error && <div className="text-rose-400 text-sm mb-2">{error}</div>}

        <label className="block mb-2 text-slate-400">Email</label>
        <input
          type="email"
          className="w-full mb-3 p-2 bg-[#111] text-white border border-zinc-900 focus:outline-none focus:border-phosphor-teal"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />

        <label className="block mb-2 text-slate-400">Password</label>
        <input
          type="password"
          className="w-full mb-3 p-2 bg-[#111] text-white border border-zinc-900 focus:outline-none focus:border-phosphor-teal"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />

        <button
          disabled={loading || status === "loading"}
          className="w-full p-2 bg-phosphor-teal text-black font-bold uppercase tracking-wider text-sm transition-opacity hover:opacity-90 disabled:opacity-50"
        >
          {loading ? "Signing in..." : "Sign In"}
        </button>
      </form>
    </div>
  );
}
