const variants = {
  primary:
    'bg-terracotta text-ivory border-ink hover:bg-terracotta-dark',
  dark: 'bg-ink text-ivory border-ink hover:bg-walnut',
  secondary: 'bg-ivory text-ink border-ink hover:bg-taupe/20',
  olive: 'bg-olive text-ivory border-ink hover:bg-olive-dark',
  ghost: 'bg-transparent text-ink border-transparent shadow-none hover:bg-ink/5',
}

const sizes = {
  md: 'px-5 py-3 text-sm',
  lg: 'px-7 py-4 text-base',
}

export default function Button({
  as: Component = 'button',
  variant = 'primary',
  size = 'lg',
  className = '',
  children,
  ...props
}) {
  const isGhost = variant === 'ghost'
  return (
    <Component
      className={`
        inline-flex items-center justify-center gap-2 rounded-full font-display font-semibold
        border-2 transition-all duration-150 ease-out
        ${!isGhost ? 'shadow-brutal-sm hover:-translate-y-0.5 active:shadow-none active:translate-x-[4px] active:translate-y-[4px]' : ''}
        disabled:opacity-50 disabled:pointer-events-none
        ${variants[variant]} ${sizes[size]} ${className}
      `}
      {...props}
    >
      {children}
    </Component>
  )
}
