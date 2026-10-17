import { BrowserRouter, Route, Routes } from 'react-router-dom'

import { useMe } from './api/hooks'
import Layout from './components/Layout'
import { Loading } from './components/ui'
import Dashboard from './pages/Dashboard'
import Fitness from './pages/Fitness'
import Login from './pages/Login'
import Records from './pages/Records'
import RunDetail from './pages/RunDetail'
import Runs from './pages/Runs'
import Settings from './pages/Settings'
import Shoes from './pages/Shoes'
import Training from './pages/Training'

export default function App() {
  const me = useMe()
  if (me.isLoading) return <Loading />
  if (!me.data?.logged_in) return <Login />
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="runs" element={<Runs />} />
          <Route path="runs/:id" element={<RunDetail />} />
          <Route path="shoes" element={<Shoes />} />
          <Route path="fitness" element={<Fitness />} />
          <Route path="training" element={<Training />} />
          <Route path="records" element={<Records />} />
          <Route path="settings" element={<Settings />} />
          <Route path="*" element={<Dashboard />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
