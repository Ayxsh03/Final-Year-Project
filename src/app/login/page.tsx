
'use client';
import { useState } from 'react';
import { supabase } from '@/lib/supabase/client';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [msg, setMsg] = useState('');

  async function onLogin(e: any) {
    e.preventDefault();
    const { error } = await supabase.auth.signInWithPassword({ email, password });
    if (error) setMsg(error.message);
    else window.location.href = '/dashboard';
  }

  async function onOAuth(provider: 'google' | 'github') {
    const { error } = await supabase.auth.signInWithOAuth({ provider, options: { redirectTo: window.location.origin + '/dashboard' } });
    if (error) setMsg(error.message);
  }

  return (
    <div className="min-h-screen flex items-center justify-center">
      <form onSubmit={onLogin} className="w-full max-w-sm border rounded p-6 space-y-3">
        <h1 className="text-xl font-semibold">Sign in</h1>
        <input className="border rounded px-2 py-1 w-full" placeholder="email" value={email} onChange={e=>setEmail(e.target.value)} />
        <input className="border rounded px-2 py-1 w-full" placeholder="password" type="password" value={password} onChange={e=>setPassword(e.target.value)} />
        <button className="w-full border rounded px-2 py-1" type="submit">Sign in</button>
        <div className="flex gap-2">
          <button type="button" className="border rounded px-2 py-1 w-full" onClick={()=>onOAuth('google')}>Google</button>
          <button type="button" className="border rounded px-2 py-1 w-full" onClick={()=>onOAuth('github')}>GitHub</button>
        </div>
        {msg && <div className="text-red-500 text-sm">{msg}</div>}
      </form>
    </div>
  );
}
