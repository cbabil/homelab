/**
 * Application Layout Component
 * 
 * Main layout wrapper that provides navigation and header.
 * Implements the overall UI structure for the application.
 */

import { ReactNode } from 'react'
import { Navigation } from './Navigation'
import { Header } from './Header'

interface AppLayoutProps {
  children: ReactNode
}

export function AppLayout({ children }: AppLayoutProps) {
  return (
    <div className="h-screen bg-background flex flex-col">
      <Header />
      
      <div className="flex flex-1 min-h-0">
        <Navigation />

        <main className="flex-1 overflow-hidden flex flex-col">
          <div className="p-6 flex-1 flex flex-col min-h-0">
            {children}
          </div>
        </main>
      </div>
    </div>
  )
}