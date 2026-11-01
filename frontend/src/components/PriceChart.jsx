import { useEffect, useRef, useState } from 'react'
import { formatPrice } from '../lib/format'

const HEIGHT = 240
const PAD = { top: 16, right: 16, bottom: 28, left: 76 }

const day = (iso) => new Date(iso).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })

export default function PriceChart({ series }) {
  const [hover, setHover] = useState(null)
  // Drawn at its real width, so the labels stay readable on a phone.
  const box = useRef(null)
  const [WIDTH, setWidth] = useState(720)
  useEffect(() => {
    const observer = new ResizeObserver(([entry]) => {
      if (entry.contentRect.width) setWidth(entry.contentRect.width)
    })
    observer.observe(box.current)
    return () => observer.disconnect()
  }, [])
  const times = series.map((p) => new Date(p.at).getTime())
  const prices = series.map((p) => p.price)
  const [t0, t1] = [Math.min(...times), Math.max(...times)]
  const [low, high] = [Math.min(...prices), Math.max(...prices)]
  const margin = Math.max((high - low) * 0.15, high * 0.01, 1)
  const [y0, y1] = [low - margin, high + margin]
  const x = (t) => PAD.left + ((t - t0) / (t1 - t0 || 1)) * (WIDTH - PAD.left - PAD.right)
  const y = (v) => PAD.top + (1 - (v - y0) / (y1 - y0)) * (HEIGHT - PAD.top - PAD.bottom)

  // A price holds until the next recorded change, so the line steps.
  const line = series
    .map((p, i) => {
      const px = x(times[i]).toFixed(1)
      const py = y(p.price).toFixed(1)
      return i === 0 ? `M${px} ${py}` : `H${px} V${py}`
    })
    .join(' ')
  const ticks = low === high ? [low] : [low, Math.round((low + high) / 2), high]

  function move(e) {
    const rect = e.currentTarget.getBoundingClientRect()
    const at = ((e.clientX - rect.left) / rect.width) * WIDTH
    let index = 0
    times.forEach((t, i) => {
      if (Math.abs(x(t) - at) < Math.abs(x(times[index]) - at)) index = i
    })
    setHover(index)
  }

  const point = hover == null ? null : series[hover]
  return (
    <div className="qy-chart" ref={box}>
      <svg
        viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
        role="img"
        aria-label={`Lowest listed price from ${day(series[0].at)} to ${day(series[series.length - 1].at)}, between ${formatPrice(low)} and ${formatPrice(high)}. The table below has every point.`}
        onPointerMove={move}
        onPointerLeave={() => setHover(null)}
      >
        {ticks.map((tick) => (
          <g key={tick}>
            <line x1={PAD.left} x2={WIDTH - PAD.right} y1={y(tick)} y2={y(tick)} stroke="var(--qy-line)" />
            <text x={PAD.left - 10} y={y(tick) + 4} textAnchor="end" fontSize="11" fontFamily="var(--qy-mono)" fill="var(--qy-ink-3)">{formatPrice(tick)}</text>
          </g>
        ))}
        <text x={PAD.left} y={HEIGHT - 6} fontSize="11" fontFamily="var(--qy-mono)" fill="var(--qy-ink-3)">{day(series[0].at)}</text>
        <text x={WIDTH - PAD.right} y={HEIGHT - 6} textAnchor="end" fontSize="11" fontFamily="var(--qy-mono)" fill="var(--qy-ink-3)">{day(series[series.length - 1].at)}</text>
        <path d={line} fill="none" stroke="var(--qy-ink)" strokeWidth="2" strokeLinejoin="round" />
        {point && <line x1={x(times[hover])} x2={x(times[hover])} y1={PAD.top} y2={HEIGHT - PAD.bottom} stroke="var(--qy-ink-3)" />}
        <circle cx={x(times[hover ?? times.length - 1])} cy={y(prices[hover ?? prices.length - 1])} r="5" fill="var(--qy-ink)" stroke="var(--qy-surface)" strokeWidth="2" />
      </svg>
      {point && (
        <div className="qy-chart__tip" style={{ left: `${(x(times[hover]) / WIDTH) * 100}%` }}>
          <span className="qy-price">{formatPrice(point.price)}</span> · {day(point.at)}
        </div>
      )}
    </div>
  )
}
