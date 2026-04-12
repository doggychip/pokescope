import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Routes, Route, useLocation } from 'react-router-dom'
import { ClerkProvider, SignIn, SignUp } from '@clerk/clerk-react'
import './index.css'
import Landing from './Landing.jsx'
import App from './App.jsx'
import ProtectedRoute from './ProtectedRoute.jsx'
import { LangProvider, getLangFromPath } from './i18n/index.jsx'

const clerkKey = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY

const ClerkWrapper = ({ children }) => {
  if (!clerkKey || clerkKey === 'pk_test_PLACEHOLDER') {
    return <>{children}</>
  }
  return (
    <ClerkProvider publishableKey={clerkKey}>
      {children}
    </ClerkProvider>
  )
}

function AppRoutes() {
  const location = useLocation()
  const lang = getLangFromPath(location.pathname)

  return (
    <LangProvider lang={lang}>
      <Routes>
        {/* English (default) */}
        <Route path="/" element={<Landing />} />
        <Route path="/dashboard" element={<ProtectedRoute><App /></ProtectedRoute>} />

        {/* Chinese */}
        <Route path="/zh" element={<Landing />} />
        <Route path="/zh/dashboard" element={<ProtectedRoute><App /></ProtectedRoute>} />

        {/* Japanese */}
        <Route path="/ja" element={<Landing />} />
        <Route path="/ja/dashboard" element={<ProtectedRoute><App /></ProtectedRoute>} />

        {/* Auth routes */}
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
      </Routes>
    </LangProvider>
  )
}

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <BrowserRouter>
      <ClerkWrapper>
        <AppRoutes />
      </ClerkWrapper>
    </BrowserRouter>
  </StrictMode>,
)
