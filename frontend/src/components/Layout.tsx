import { NavLink, Outlet } from 'react-router-dom'

const navItems = [
  { to: '/', label: 'Overview' },
  { to: '/monitor', label: 'Monitor' },
  { to: '/alerts', label: 'Alerts' },
  { to: '/analytics', label: 'Analytics' },
]

export function Layout() {
  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar */}
      <aside className="w-60 bg-surface flex flex-col border-r border-gray-200 shrink-0">
        <div className="px-5 py-6">
          <h1 className="text-lg font-bold text-accent tracking-tight">MPLAD-SHIELD</h1>
          <p className="text-xs text-muted mt-1">Risk Intelligence Dashboard</p>
        </div>
        <nav className="flex-1 px-3">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              className={({ isActive }) =>
                `block px-3 py-2.5 rounded-lg text-sm font-medium mb-1 transition-colors ${
                  isActive
                    ? 'bg-accent-soft text-accent'
                    : 'text-ink-2 hover:bg-gray-100'
                }`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="px-5 py-4 border-t border-gray-200">
          <p className="text-[11px] text-muted leading-tight">
            Risk indicators are investigation signals, not findings of wrongdoing.
          </p>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-y-auto">
        <header className="sticky top-0 z-10 bg-surface border-b border-gray-200 px-8 py-4">
          <h2 className="text-base font-semibold text-ink">MPLAD-SHIELD</h2>
        </header>
        <div className="p-8">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
