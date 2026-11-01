import { Route, Routes } from 'react-router-dom'
import { RequireLogin } from './lib/auth'
import Categories from './pages/Categories'
import ForgotPassword from './pages/auth/ForgotPassword'
import Login from './pages/auth/Login'
import ResetPassword from './pages/auth/ResetPassword'
import Signup from './pages/auth/Signup'
import Verify from './pages/auth/Verify'
import Home from './pages/Home'
import Landing from './pages/Landing'
import NotFound from './pages/NotFound'
import Product from './pages/Product'
import Results from './pages/Results'
import Saved from './pages/Saved'

export default function App() {
  return (
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
      <Route path="*" element={<NotFound />} />
    </Routes>
  )
}
