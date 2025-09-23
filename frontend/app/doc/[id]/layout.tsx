// Layout for document reader pages
import { ReactNode } from 'react'

interface LayoutProps {
  children: ReactNode
}

export default function DocumentLayout({ children }: LayoutProps) {
  return (
    <div className="h-screen flex flex-col">
      {children}
    </div>
  )
}
