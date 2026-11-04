import { useLayoutEffect, useRef, useState } from 'react'

// The underline under the chosen tab, sliding to whichever tab is chosen next.
// Put it inside a `qy-tabs qy-tabs--slide` tablist; it finds the tabs itself.
export default function TabBar() {
  const ref = useRef(null)
  const [pos, setPos] = useState(null)

  useLayoutEffect(() => {
    const list = ref.current?.parentElement
    if (!list) return undefined
    const place = () => {
      const on = list.querySelector('[role="tab"][aria-selected="true"]')
      setPos(on ? { left: on.offsetLeft, top: on.offsetTop + on.offsetHeight - 2, width: on.offsetWidth } : null)
    }
    place()
    // Tabs change width when their counts load, and the chosen one changes.
    const sizes = new ResizeObserver(place)
    sizes.observe(list)
    list.querySelectorAll('[role="tab"]').forEach((tab) => sizes.observe(tab))
    const choice = new MutationObserver(place)
    choice.observe(list, { subtree: true, attributeFilter: ['aria-selected'] })
    return () => {
      sizes.disconnect()
      choice.disconnect()
    }
  }, [])

  return <span ref={ref} className="qy-tabs__bar" aria-hidden="true" style={pos ?? { display: 'none' }} />
}
