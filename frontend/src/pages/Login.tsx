import { useState } from 'react'

import { useLogin } from '../api/hooks'
import { Button, ErrorNote, inputClass } from '../components/ui'

export default function Login() {
  const login = useLogin()
  const [password, setPassword] = useState('')
  return (
    <div className="flex min-h-screen items-center justify-center bg-nav px-4">
      <form
        className="w-full max-w-sm rounded-2xl bg-surface p-6 shadow-xl"
        onSubmit={(e) => {
          e.preventDefault()
          login.mutate(password)
        }}
      >
        <div className="mb-5 flex items-center gap-2.5">
          <img src="/favicon.svg" alt="" className="h-9 w-9 rounded-lg" />
          <h1 className="text-xl font-semibold text-ink">Unicorn</h1>
        </div>
        <label className="mb-1 block text-sm font-medium text-ink-2" htmlFor="password">
          Password
        </label>
        <input
          id="password"
          type="password"
          autoFocus
          autoComplete="current-password"
          className={inputClass}
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        {login.error && <div className="mt-3"><ErrorNote error={login.error} /></div>}
        <Button type="submit" variant="primary" className="mt-4 w-full py-2" disabled={!password || login.isPending}>
          {login.isPending ? 'Signing in…' : 'Sign in'}
        </Button>
      </form>
    </div>
  )
}
