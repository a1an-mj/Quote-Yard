import { Tag } from 'lucide-react'

export default function Footer() {
  return (
    <footer className="bg-ink text-ivory">
      <div className="mx-auto max-w-6xl px-4 py-12 sm:px-6 lg:px-8">
        <div className="flex flex-col gap-8 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <div className="flex items-center gap-2">
              <span className="flex h-8 w-8 items-center justify-center rounded-full border-2 border-ivory bg-terracotta">
                <Tag size={16} strokeWidth={2.5} />
              </span>
              <span className="font-display text-lg font-bold">Quote Yard</span>
            </div>
            <p className="mt-3 max-w-xs font-body text-sm text-ivory/60">
              Comparing prices across your local electronics retailers, so you never overpay.
            </p>
          </div>

          <div className="flex gap-12 font-body text-sm">
            <div>
              <p className="mb-3 font-display text-xs font-semibold uppercase tracking-wide text-ivory/40">Product</p>
              <ul className="space-y-2 text-ivory/70">
                <li>How it works</li>
                <li>Categories</li>
                <li>Today's deals</li>
              </ul>
            </div>
            <div>
              <p className="mb-3 font-display text-xs font-semibold uppercase tracking-wide text-ivory/40">Company</p>
              <ul className="space-y-2 text-ivory/70">
                <li>About</li>
                <li>Retailers</li>
                <li>Contact</li>
              </ul>
            </div>
          </div>
        </div>

        <div className="mt-10 flex flex-col gap-2 border-t border-ivory/15 pt-6 font-body text-xs text-ivory/40 sm:flex-row sm:items-center sm:justify-between">
          <p>© {new Date().getFullYear()} Quote Yard. A prototype for demo purposes.</p>
          <p>Made for Indian shoppers, one comparison at a time.</p>
        </div>
      </div>
    </footer>
  )
}
