import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { ClerkProvider, SignIn, SignUp } from '@clerk/clerk-react'
import './index.css'
import Landing from './Landing.jsx'
import App from './App.jsx'
import ProtectedRoute from './ProtectedRoute.jsx'

const clerkKey = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY

const ClerkWrapper = ({ children }) => {
  if (!clerkKey || clerkKey === 'pk_test_PLACEHOLDER') {
    // Dev mode — skip Clerk
    return <>{children}</>
  }
  return (
    <ClerkProvider publishableKey={clerkKey}>
      {children}
    </ClerkProvider>
  )
}

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <BrowserRouter>
      <ClerkWrapper>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/sign-in/*" element={
            <div className="auth-page">
              <SignIn routing="path" path="/sign-in" afterSignInUrl="/dashboard" />
            </div>
          } />
          <Route path="/sign-up/*" element={
            <div className="auth-page">
              <SignUp routing="path" path="/sign-up" afterSignUpUrl="/dashboard" />
            </div>
          } />
          <Route path="/dashboard" element={
            <ProtectedRoute>
              <App />
            </ProtectedRoute>
          } />
        </Routes>
      </ClerkWrapper>
    </BrowserRouter>
  </StrictMode>,
)
