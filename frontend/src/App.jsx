import { useLayoutEffect } from 'react'
import { Route, Routes, useLocation, useNavigationType } from 'react-router-dom'
import CrashScreen from './components/CrashScreen'
import { RequireLogin } from './lib/auth'
import { noteEntry } from './lib/motion'
import Admin from './pages/Admin'
import Categories from './pages/Categories'
import ForgotPassword from './pages/auth/ForgotPassword'
import Login from './pages/auth/Login'
import ResetPassword from './pages/auth/ResetPassword'
import Signup from './pages/auth/Signup'
import Verify from './pages/auth/Verify'
import Home from './pages/Home'
import Feedback from './pages/Feedback'
import Landing from './pages/Landing'
import { Privacy, Terms } from './pages/Legal'
import NotFound from './pages/NotFound'
import Product from './pages/Product'
import Results from './pages/Results'
import Saved from './pages/Saved'
import { VendorForgot, VendorJoin, VendorLogin, VendorReset } from './pages/vendor/VendorAuth'
import VendorDashboard from './pages/vendor/VendorDashboard'

export default function App() {
  const { pathname, key } = useLocation()
  useLayoutEffect(noteEntry, [key]) // for the Back circle
  const how = useNavigationType()
  // A new page opens at its top. Back/Forward (POP) keep the browser's place, and
  // filters or tabs on the same page (same pathname) don't jump.
  useLayoutEffect(() => {
    if (how !== 'POP') window.scrollTo(0, 0)
  }, [pathname]) // eslint-disable-line react-hooks/exhaustive-deps
  return (
    <CrashScreen page={pathname}>
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/signup" element={<Signup />} />
      <Route path="/verify" element={<Verify />} />
      <Route path="/login" element={<Login />} />
      <Route path="/forgot-password" element={<ForgotPassword />} />
      <Route path="/reset-password" element={<ResetPassword />} />
      <Route path="/home" element={<RequireLogin><Home /></RequireLogin>} />
      <Route path="/categories" element={<RequireLogin><Categories /></RequireLogin>} />
      <Route path="/product/:id" element={<RequireLogin><Product /></RequireLogin>} />
      <Route path="/saved" element={<RequireLogin><Saved /></RequireLogin>} />
      <Route path="/search" element={<RequireLogin><Results /></RequireLogin>} />
      <Route path="/admin" element={<RequireLogin><Admin /></RequireLogin>} />
      <Route path="/vendor" element={<VendorDashboard />} />
      <Route path="/vendor/login" element={<VendorLogin />} />
      <Route path="/vendor/join" element={<VendorJoin />} />
      <Route path="/vendor/forgot-password" element={<VendorForgot />} />
      <Route path="/vendor/reset" element={<VendorReset />} />
      <Route path="/feedback" element={<Feedback />} />
      <Route path="/privacy" element={<Privacy />} />
      <Route path="/terms" element={<Terms />} />
      <Route path="*" element={<NotFound />} />
    </Routes>
    </CrashScreen>
  )
}
