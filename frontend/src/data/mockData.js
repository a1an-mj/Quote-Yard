// All data here is mock data for prototype purposes only.

export const categories = [
  { id: 'mobiles', name: 'Mobiles', emoji: '📱', count: 128 },
  { id: 'laptops', name: 'Laptops', emoji: '💻', count: 74 },
  { id: 'tvs', name: 'TVs', emoji: '📺', count: 52 },
  { id: 'fridges', name: 'Refrigerators', emoji: '🧊', count: 39 },
  { id: 'washing', name: 'Washing Machines', emoji: '🧺', count: 31 },
  { id: 'accessories', name: 'Accessories', emoji: '🎧', count: 96 },
]

export const retailerLogos = {
  myG: { color: '#C65A3A' },
  Oxygen: { color: '#5C6142' },
  Pittappillil: { color: '#4A3025' },
  Poorvika: { color: '#8C7E6D' },
  'Vijay Sales': { color: '#A84427' },
  Croma: { color: '#454A30' },
}

export const products = [
  {
    id: 'nothing-phone-4b',
    category: 'mobiles',
    name: 'Nothing Phone 4b',
    spec: '8 GB • 128 GB • Blue',
    image: '📱',
    retailers: [
      { name: 'myG', price: 39999, inStock: true },
      { name: 'Oxygen', price: 40499, inStock: true },
      { name: 'Pittappillil', price: 41200, inStock: true },
      { name: 'Poorvika', price: 41999, inStock: false },
    ],
  },
  {
    id: 'nothing-phone-3',
    category: 'mobiles',
    name: 'Nothing Phone (3)',
    spec: '12 GB • 256 GB • White',
    image: '📱',
    retailers: [
      { name: 'myG', price: 64999, inStock: true },
      { name: 'Vijay Sales', price: 65999, inStock: true },
      { name: 'Oxygen', price: 66499, inStock: true },
    ],
  },
  {
    id: 'samsung-s24-fe',
    category: 'mobiles',
    name: 'Samsung Galaxy S24 FE',
    spec: '8 GB • 256 GB • Graphite',
    image: '📱',
    retailers: [
      { name: 'Poorvika', price: 49999, inStock: true },
      { name: 'myG', price: 50499, inStock: true },
      { name: 'Croma', price: 51990, inStock: true },
    ],
  },
  {
    id: 'lenovo-ideapad-slim-3',
    category: 'laptops',
    name: 'Lenovo IdeaPad Slim 3',
    spec: 'Ryzen 5 • 16 GB • 512 GB SSD',
    image: '💻',
    retailers: [
      { name: 'myG', price: 71990, inStock: true },
      { name: 'Vijay Sales', price: 73490, inStock: true },
      { name: 'Croma', price: 74990, inStock: true },
      { name: 'Oxygen', price: 75490, inStock: false },
    ],
  },
  {
    id: 'hp-pavilion-15',
    category: 'laptops',
    name: 'HP Pavilion 15',
    spec: 'i5 13th Gen • 16 GB • 512 GB SSD',
    image: '💻',
    retailers: [
      { name: 'Croma', price: 82990, inStock: true },
      { name: 'Poorvika', price: 83990, inStock: true },
      { name: 'myG', price: 84490, inStock: true },
    ],
  },
  {
    id: 'lg-43-smart-tv',
    category: 'tvs',
    name: 'LG 43" 4K Smart TV',
    spec: 'UHD • WebOS • HDR10',
    image: '📺',
    retailers: [
      { name: 'Pittappillil', price: 33990, inStock: true },
      { name: 'myG', price: 34990, inStock: true },
      { name: 'Oxygen', price: 35490, inStock: true },
    ],
  },
  {
    id: 'samsung-55-crystal',
    category: 'tvs',
    name: 'Samsung 55" Crystal 4K',
    spec: 'UHD • Tizen • HDR10+',
    image: '📺',
    retailers: [
      { name: 'Vijay Sales', price: 47990, inStock: true },
      { name: 'Croma', price: 48990, inStock: true },
      { name: 'myG', price: 49490, inStock: true },
    ],
  },
  {
    id: 'lg-260l-fridge',
    category: 'fridges',
    name: 'LG 260L Double Door Fridge',
    spec: 'Frost Free • 3 Star',
    image: '🧊',
    retailers: [
      { name: 'Pittappillil', price: 26990, inStock: true },
      { name: 'Oxygen', price: 27490, inStock: true },
      { name: 'myG', price: 27990, inStock: true },
    ],
  },
  {
    id: 'samsung-198l-fridge',
    category: 'fridges',
    name: 'Samsung 198L Single Door Fridge',
    spec: 'Direct Cool • 4 Star',
    image: '🧊',
    retailers: [
      { name: 'myG', price: 18990, inStock: true },
      { name: 'Poorvika', price: 19490, inStock: true },
      { name: 'Croma', price: 19990, inStock: false },
    ],
  },
  {
    id: 'whirlpool-7kg-wm',
    category: 'washing',
    name: 'Whirlpool 7 kg Washing Machine',
    spec: 'Fully Automatic • Top Load',
    image: '🧺',
    retailers: [
      { name: 'Oxygen', price: 15990, inStock: true },
      { name: 'myG', price: 16490, inStock: true },
      { name: 'Pittappillil', price: 16990, inStock: true },
    ],
  },
  {
    id: 'lg-8kg-wm',
    category: 'washing',
    name: 'LG 8 kg Washing Machine',
    spec: 'Fully Automatic • Front Load',
    image: '🧺',
    retailers: [
      { name: 'Vijay Sales', price: 28990, inStock: true },
      { name: 'Croma', price: 29990, inStock: true },
      { name: 'myG', price: 30490, inStock: true },
    ],
  },
  {
    id: 'boat-airdopes',
    category: 'accessories',
    name: 'boAt Airdopes 141',
    spec: 'True Wireless • 42h Playback',
    image: '🎧',
    retailers: [
      { name: 'myG', price: 1299, inStock: true },
      { name: 'Poorvika', price: 1399, inStock: true },
      { name: 'Oxygen', price: 1449, inStock: true },
    ],
  },
  {
    id: 'noise-smartwatch',
    category: 'accessories',
    name: 'Noise ColorFit Pro 5',
    spec: 'AMOLED • Bluetooth Calling',
    image: '⌚',
    retailers: [
      { name: 'myG', price: 2799, inStock: true },
      { name: 'Croma', price: 2999, inStock: true },
      { name: 'Vijay Sales', price: 3099, inStock: false },
    ],
  },
]

export function getLowestPrice(product) {
  return Math.min(...product.retailers.map((r) => r.price))
}

export function getHighestPrice(product) {
  return Math.max(...product.retailers.map((r) => r.price))
}

export function formatINR(amount) {
  return '₹' + amount.toLocaleString('en-IN')
}

export const popularComparisons = [
  'nothing-phone-4b',
  'lenovo-ideapad-slim-3',
  'lg-43-smart-tv',
]

export const todaysDeals = [
  { productId: 'boat-airdopes', tag: 'Deal of the day' },
  { productId: 'samsung-198l-fridge', tag: 'Price drop' },
  { productId: 'whirlpool-7kg-wm', tag: 'Limited stock' },
]

export function searchProducts(query) {
  if (!query || !query.trim()) return []
  const q = query.trim().toLowerCase()
  return products.filter(
    (p) =>
      p.name.toLowerCase().includes(q) ||
      p.category.toLowerCase().includes(q) ||
      p.spec.toLowerCase().includes(q)
  )
}

export function getProductById(id) {
  return products.find((p) => p.id === id)
}
