'use client';
import { useState } from 'react';
import { apiClient } from '@/core/api/client';
import { useRouter } from 'next/navigation';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const router = useRouter();

  const handleLogin = async () => {
    if (isLoading) return;
    setIsLoading(true);
    setErrorMessage('');
    try {
      const params = new URLSearchParams();
      params.append('username', email);
      params.append('password', password);
      
      const { data } = await apiClient.post('/auth/login', params, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      });
      localStorage.setItem('token', data.access_token);
      router.push('/builder');
    } catch (e) {
      console.error(e);
      setErrorMessage('Login failed. Please check your email and password.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="relative min-h-screen overflow-hidden bg-blue-900 text-gray-900">
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_20%_10%,rgba(255,255,255,0.06),transparent_40%),radial-gradient(circle_at_80%_90%,rgba(255,255,255,0.04),transparent_45%)]" />
        <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.05)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.04)_1px,transparent_1px)] bg-[size:28px_28px]" />
      </div>

      <div className="relative z-10 flex min-h-screen items-center justify-center px-6 py-10">
        <div className="w-full max-w-md rounded-2xl border border-gray-300 bg-gray-200 p-8 shadow-lg">
          <div className="mb-8 flex items-center justify-between">
            <div>
              <div className="inline-flex items-center gap-2 rounded-full border border-gray-300 bg-gray-100 px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-gray-700">
                AI Builder
                <span className="h-1.5 w-1.5 rounded-full bg-blue-500 animate-pulse" />
              </div>
              <h1 className="mt-4 text-3xl font-bold text-gray-900">
                Welcome Back
              </h1>
              <p className="mt-2 text-sm text-gray-600">
                Sign in to continue your AI workflow.
              </p>
            </div>
            <div className="hidden sm:block">
              <div className="relative h-14 w-14">
                <div className="absolute inset-0 rounded-2xl bg-blue-600/20 blur-[4px]" />
                <div className="absolute inset-1 rounded-2xl border border-gray-300 bg-white" />
                <div className="absolute inset-0 flex items-center justify-center text-xs font-semibold text-blue-700">
                  AI
                </div>
                <div className="absolute -right-2 -top-2 h-3 w-3 rounded-full bg-blue-500/70 animate-ping" />
              </div>
            </div>
          </div>

          <div className="space-y-5">
            <div>
              <label className="mb-2 block text-xs font-semibold uppercase tracking-widest text-gray-600">
                Email Address
              </label>
              <input
                className="w-full rounded-xl border border-gray-300 bg-white px-4 py-3 text-sm text-gray-900 placeholder-gray-400 shadow-inner outline-none transition-all focus:border-blue-600 focus:ring-2 focus:ring-blue-200"
                placeholder="name@company.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>

            <div>
              <label className="mb-2 block text-xs font-semibold uppercase tracking-widest text-gray-600">
                Password
              </label>
              <input
                className="w-full rounded-xl border border-gray-300 bg-white px-4 py-3 text-sm text-gray-900 placeholder-gray-400 shadow-inner outline-none transition-all focus:border-blue-600 focus:ring-2 focus:ring-blue-200"
                placeholder="********"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>

            <button
              onClick={handleLogin}
              disabled={isLoading}
              className="group relative w-full overflow-hidden rounded-xl bg-blue-600 px-4 py-3 text-sm font-semibold text-white shadow-md transition-all duration-300 hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-70"
            >
              <span className="relative inline-flex items-center justify-center gap-3">
                <span>{isLoading ? "Signing in..." : "Sign In"}</span>
                {isLoading && (
                  <span className="relative flex h-5 w-5 items-center justify-center">
                    <span className="absolute h-5 w-5 rounded-full border-2 border-white/40 border-t-white animate-spin" />
                    <span className="absolute h-2.5 w-2.5 rounded-full bg-white/80 blur-[1px] animate-pulse" />
                  </span>
                )}
              </span>
            </button>

            <div className="flex items-center gap-2 text-xs text-gray-600">
              <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
              Secure channel enabled. Your build context is encrypted.
            </div>

            {errorMessage && !isLoading && (
              <div className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-xs text-rose-700">
                <div className="flex items-center gap-2 font-semibold text-rose-700">
                  <span className="h-2 w-2 rounded-full bg-rose-400" />
                  Access denied
                </div>
                <p className="mt-1 text-rose-600">{errorMessage}</p>
              </div>
            )}

            {isLoading && (
              <div className="mt-2 flex items-center justify-center">
                <div className="relative w-full rounded-xl border border-gray-300 bg-gray-100 px-4 py-4 text-center text-xs font-medium text-gray-700">
                  <div className="mx-auto mb-3 h-16 w-16">
                    <div className="relative h-16 w-16">
                      <div className="absolute inset-0 rounded-full bg-blue-600/20 blur-[4px] animate-pulse" />
                      <div className="absolute inset-1 rounded-full bg-white" />
                      <div className="absolute inset-2 rounded-full bg-gradient-to-br from-white via-blue-100 to-blue-200" />
                      <div className="absolute inset-0 rounded-full border border-blue-200/70" />
                      <div className="absolute inset-0 animate-[spin_2.4s_linear_infinite]">
                        <span className="absolute left-1/2 top-0 -translate-x-1/2 h-2 w-2 rounded-full bg-blue-500" />
                        <span className="absolute left-1/2 bottom-0 -translate-x-1/2 h-1.5 w-1.5 rounded-full bg-blue-300" />
                      </div>
                      <div className="absolute inset-1 animate-[spin_1.6s_linear_infinite] [animation-direction:reverse]">
                        <span className="absolute right-0 top-1/2 -translate-y-1/2 h-1.5 w-1.5 rounded-full bg-blue-400" />
                        <span className="absolute left-0 top-1/2 -translate-y-1/2 h-1.5 w-1.5 rounded-full bg-blue-200" />
                      </div>
                    </div>
                  </div>
                  <p className="tracking-wide">Synchronizing workspace...</p>
                  <div className="mt-3 flex items-end justify-center gap-1">
                    <span className="h-2 w-1 rounded-full bg-blue-500/80 animate-pulse" />
                    <span className="h-3 w-1 rounded-full bg-blue-400/80 animate-pulse [animation-delay:120ms]" />
                    <span className="h-4 w-1 rounded-full bg-blue-300/80 animate-pulse [animation-delay:240ms]" />
                    <span className="h-3 w-1 rounded-full bg-blue-400/80 animate-pulse [animation-delay:360ms]" />
                    <span className="h-2 w-1 rounded-full bg-blue-500/80 animate-pulse [animation-delay:480ms]" />
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
