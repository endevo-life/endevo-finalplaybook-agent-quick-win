import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './styles/global.css'
import App from './App.jsx'

// Theme: B2C (gold/navy/off-white) is the DEFAULT. B2B (ENDevo) is optional.
// Applied from ?theme= or a saved choice; default is always B2C.
const themeParam = new URLSearchParams(window.location.search).get('theme')
if (themeParam) localStorage.setItem('fp_theme', themeParam)
const theme = themeParam || localStorage.getItem('fp_theme') || 'b2c'
if (theme === 'b2b') document.documentElement.setAttribute('data-theme', 'b2b')
else document.documentElement.removeAttribute('data-theme') // b2c = the default :root

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
