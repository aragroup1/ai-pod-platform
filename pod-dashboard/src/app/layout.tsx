import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import Navigation from '@/components/Navigation';
  
const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'AI POD Dashboard',
  description: 'Manage your AI Print-on-Demand Platform',
}

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        <Navigation />  {/* Add this */}
        {children}
      </body>
    </html>
  );
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>{children}</body>
    </html>
  )
}
