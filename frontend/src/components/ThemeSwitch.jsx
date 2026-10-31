import { useTheme } from '../lib/theme'

export default function ThemeSwitch() {
  const [theme, setTheme] = useTheme()
  return (
    <div className="qy-seg" role="group" aria-label="Theme">
      {['light', 'dark'].map((name) => (
        <button
          key={name}
          type="button"
          className={theme === name ? 'on' : ''}
          aria-pressed={theme === name}
          onClick={() => setTheme(name)}
        >
          {name === 'light' ? 'Light' : 'Dark'}
        </button>
      ))}
    </div>
  )
}
