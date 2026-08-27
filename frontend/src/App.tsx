import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { Layout } from './components/Layout'
import { Overview } from './pages/Overview'
import { Monitor } from './pages/Monitor'
import { ProjectDetailPage } from './pages/ProjectDetail'
import { Alerts } from './pages/Alerts'
import { Analytics } from './pages/Analytics'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Overview />} />
          <Route path="/monitor" element={<Monitor />} />
          <Route path="/project/:id" element={<ProjectDetailPage />} />
          <Route path="/alerts" element={<Alerts />} />
          <Route path="/analytics" element={<Analytics />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
