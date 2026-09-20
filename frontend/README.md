# Quote Yard — Investor Prototype

A frontend-only prototype for **Quote Yard**, a price-comparison platform for Indian
shoppers. Built with React, Vite, Tailwind CSS and React Router. There is no backend —
all data, auth and pricing are mocked (see `src/data/mockData.js` and
`src/context/AuthContext.jsx`).

## Getting started

```bash
npm install
npm run dev
```

Then open the printed local URL (usually `http://localhost:5173`).

To build a static production bundle:

```bash
npm run build
npm run preview
```

## Demo flow

1. Landing page (`/`) — brand, hero, and a live price-comparison showcase.
2. **Get Started** → Signup (`/signup`) — fill the form (client-side validation only)
   or use **Continue with Google** to skip straight in.
3. Lands on the Dashboard (`/dashboard`) — greeting, search, categories, popular
   comparisons and today's deals.
4. Search any product name (try "phone", "laptop", or "tv") → results page
   (`/search`) with category filters and sorting.
5. Tap **Compare** on any product → comparison page (`/compare/:productId`) showing
   every retailer's price, with the lowest price highlighted and total savings shown.
6. Use the navbar/bottom nav to move between Home, Search, Deals and Profile.
7. **Logout** from the navbar or Profile page returns to the landing page.
8. **Login** (`/login`) — any valid-looking email + password logs you back in
   (mock authentication only, matching the prototype brief).

## Project structure

```
src/
  components/   Reusable UI: Navbar, Footer, Button, SearchBar, ProductCard,
                CategoryCard, RetailerCard, GoogleButton, BottomNav, FormField
  pages/        Landing, Signup, Login, Dashboard, SearchResults, Comparison,
                Profile, NotFound
  context/      AuthContext — mock session stored in localStorage
  data/         mockData.js — categories, products, retailers, prices (INR)
```

## Notes

- No real backend, database, authentication, or payments — this is a demo shell only.
- "Continue with Google" simulates a successful login; no real OAuth occurs.
- Mock session persists in `localStorage` so a refresh keeps you logged in.
