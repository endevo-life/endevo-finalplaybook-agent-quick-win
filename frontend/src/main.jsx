import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './styles/global.css'
import App from './App.jsx'

// Theme switch: ?theme=b2b (or ?theme=b2c) applies the palette and remembers it.
// See docs/THEME-handoff.md. Lets you preview the B2B/ENDevo look without a build.
const themeParam = new URLSearchParams(window.location.search).get('theme')
const theme = themeParam || localStorage.getItem('fp_theme')
if (theme === 'b2b') document.documentElement.setAttribute('data-theme', 'b2b')
else document.documentElement.removeAttribute('data-theme')
if (themeParam) localStorage.setItem('fp_theme', themeParam)

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
