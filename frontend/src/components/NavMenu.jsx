import { useEffect, useId, useState } from 'react'
import { useLocation } from 'react-router-dom'

// On phones and tablets the nav's links sit behind a Menu button. On wider
// screens the button is hidden and the children lay out in the nav as usual.
export default function NavMenu({ children }) {
  const [open, setOpen] = useState(false)
  const { pathname, hash } = useLocation()
  const id = useId()

  useEffect(() => setOpen(false), [pathname, hash])

  // A link to a spot on the same page changes no route, so close on the tap too.
  const closeOnLink = (e) => {
    if (e.target.closest('a')) setOpen(false)
  }

  return (
    <>
      <button className="qy-btn qy-btn--quiet qy-nav__toggle" type="button" aria-expanded={open} aria-controls={id} onClick={() => setOpen(!open)}>
        {open ? 'Close' : 'Menu'}
      </button>
      <div id={id} className={`qy-nav__menu ${open ? 'qy-nav__menu--open' : ''}`} onClick={closeOnLink}>
        {children}
      </div>
    </>
  )
}
