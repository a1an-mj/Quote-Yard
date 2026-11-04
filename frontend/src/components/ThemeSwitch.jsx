import { originOf } from '../lib/motion'
import { useTheme } from '../lib/theme'

export default function ThemeSwitch() {
  const [theme, setTheme] = useTheme()
  return (
    <div className="qy-seg qy-seg--slide" role="group" aria-label="Theme" data-on={theme}>
      <span className="qy-seg__pill" aria-hidden="true" />
      {['light', 'dark'].map((name) => (
        <button
          key={name}
          type="button"
          className={theme === name ? 'on' : ''}
          aria-pressed={theme === name}
          onClick={(e) => setTheme(name, originOf(e))}
        >
          {name === 'light' ? 'Light' : 'Dark'}
        </button>
      ))}
    </div>
  )
}
