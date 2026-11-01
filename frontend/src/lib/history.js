// Turns per-listing price points into one series: the lowest buyable price
// known at each moment a price was recorded.
export function lowestOverTime(listings) {
  const events = listings
    .flatMap((listing) => listing.points.map((point) => ({ ...point, id: listing.listing_id })))
    .sort((a, b) => new Date(a.recorded_at) - new Date(b.recorded_at))
  const latest = new Map()
  const series = []
  for (const event of events) {
    latest.set(event.id, event)
    const buyable = [...latest.values()].filter((p) => p.availability !== 'Out of stock').map((p) => p.price)
    if (!buyable.length) continue
    const price = Math.min(...buyable)
    const at = event.recorded_at
    const last = series[series.length - 1]
    // Prices recorded in one load share a moment; keep the settled value.
    if (last && last.at.slice(0, 10) === at.slice(0, 10)) {
      last.price = price
      last.at = at
    } else if (!last || last.price !== price) {
      series.push({ at, price })
    }
  }
  return series
}
