import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App.jsx'
import { AuthProvider } from './lib/auth.jsx'
// Fonts are served by the site itself, so no visitor data goes to Google. Latin-ext holds the ₹ sign.
import '@fontsource/doto/latin-600.css'
import '@fontsource/doto/latin-ext-600.css'
import '@fontsource/doto/latin-800.css'
import '@fontsource/doto/latin-ext-800.css'
import '@fontsource/geist/latin-400.css'
import '@fontsource/geist/latin-ext-400.css'
import '@fontsource/geist/latin-500.css'
import '@fontsource/geist/latin-ext-500.css'
import '@fontsource/geist/latin-600.css'
import '@fontsource/geist/latin-ext-600.css'
import '@fontsource/geist-mono/latin-400.css'
import '@fontsource/geist-mono/latin-ext-400.css'
import '@fontsource/geist-mono/latin-500.css'
import '@fontsource/geist-mono/latin-ext-500.css'
import './styles/qy.css'
import './styles/app.css'
import './styles/look.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <App />
      </AuthProvider>
    </BrowserRouter>
  </React.StrictMode>
)
