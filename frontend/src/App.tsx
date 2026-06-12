import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import SendContract from './pages/SendContract'
import ContractDetail from './pages/ContractDetail'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/send" element={<SendContract />} />
          <Route path="/contracts/:id" element={<ContractDetail />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
