const rupees = new Intl.NumberFormat('en-IN', {
  style: 'currency',
  currency: 'INR',
  maximumFractionDigits: 0,
})

export const formatPrice = (value) => rupees.format(value).replace(/^₹/, '₹ ')

export const formatCount = (value) => new Intl.NumberFormat('en-IN').format(value)

export function timeAgo(iso, now = Date.now()) {
  const minutes = Math.max(0, Math.round((now - new Date(iso).getTime()) / 60000))
  if (minutes < 60) return `${minutes} min ago`
  const hours = Math.round(minutes / 60)
  if (hours < 24) return `${hours} h ago`
  const days = Math.round(hours / 24)
  return `${days} day${days === 1 ? '' : 's'} ago`
}

export function formatSize(gb) {
  return gb >= 1024 && gb % 1024 === 0 ? `${gb / 1024} TB` : `${gb} GB`
}

export function specLine({ network, ram_gb, storage_gb, ta_code }) {
  const parts = []
  if (ram_gb) parts.push(`${ram_gb} GB RAM`)
  if (storage_gb) parts.push(formatSize(storage_gb))
  if (network) parts.push(network)
  if (ta_code) parts.push(ta_code)
  return parts.join(' · ')
}

// After this long a price may have changed; shown as a warning (the API stops
// counting an offer as current after 3 days).
export const isOutdated = (iso, now = Date.now()) => now - new Date(iso).getTime() > 48 * 3600 * 1000
