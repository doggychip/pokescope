import { useAuth } from '@clerk/clerk-react'
import { Navigate } from 'react-router-dom'

const clerkKey = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY
const isDevMode = !clerkKey || clerkKey === 'pk_test_PLACEHOLDER'

export default function ProtectedRoute({ children }) {
  // In dev mode without Clerk configured, allow access
  if (isDevMode) return children

  const { isLoaded, isSignedIn } = useAuth()

  if (!isLoaded) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', background: '#0a0b0f', color: '#6b7280' }}>
        Loading...
      </div>
    )
  }

  if (!isSignedIn) {
    return <Navigate to="/sign-in" replace />
  }

  return children
}
