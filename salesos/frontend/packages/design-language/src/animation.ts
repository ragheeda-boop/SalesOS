export type AnimationPattern =
  | 'fade-in'
  | 'fade-in-up'
  | 'fade-in-down'
  | 'fade-in-left'
  | 'fade-in-right'
  | 'scale-in'
  | 'slide-in-left'
  | 'slide-in-right'
  | 'slide-in-up'
  | 'slide-in-down'
  | 'expand-in'
  | 'stagger'
  | 'pulse'
  | 'skeleton'

export interface AnimationConfig {
  pattern: AnimationPattern
  duration: number
  delay?: number
  staggerDelay?: number
  easing?: string
}

export const ANIMATIONS: Record<string, AnimationConfig> = {
  pageEnter: { pattern: 'fade-in-up', duration: 250, easing: 'ease-out' },
  pageExit: { pattern: 'fade-in-down', duration: 200, easing: 'ease-in' },
  cardEnter: { pattern: 'fade-in-up', duration: 200, delay: 50, easing: 'ease-out' },
  cardHover: { pattern: 'scale-in', duration: 150, easing: 'ease-out' },
  modalEnter: { pattern: 'scale-in', duration: 200, easing: 'ease-out' },
  modalExit: { pattern: 'fade-in', duration: 150, easing: 'ease-in' },
  sidebarOpen: { pattern: 'slide-in-left', duration: 250, easing: 'ease-in-out' },
  sidebarClose: { pattern: 'slide-in-left', duration: 200, easing: 'ease-in-out' },
  dropdownOpen: { pattern: 'fade-in-up', duration: 150, easing: 'ease-out' },
  tooltipShow: { pattern: 'fade-in-up', duration: 100, easing: 'ease-out' },
  skeleton: { pattern: 'skeleton', duration: 1500, easing: 'linear' },
  stagger: { pattern: 'stagger', duration: 200, staggerDelay: 50, easing: 'ease-out' },
  notificationEnter: { pattern: 'slide-in-right', duration: 300, easing: 'spring' },
  listItemEnter: { pattern: 'fade-in-left', duration: 200, staggerDelay: 30, easing: 'ease-out' },
  tabSwitch: { pattern: 'fade-in', duration: 150, easing: 'ease-out' },
  progressFill: { pattern: 'expand-in', duration: 600, easing: 'ease-in-out' },
  pulse: { pattern: 'pulse', duration: 2000 },
}

export function animationCSS(pattern: AnimationPattern): string {
  const config = Object.values(ANIMATIONS).find((a) => a.pattern === pattern) || ANIMATIONS.pageEnter
  const delay = config.delay ? `${config.delay}ms` : '0ms'
  const easing = config.easing || 'ease-out'
  return `opacity: 0; animation: ${pattern} ${config.duration}ms ${easing} ${delay} forwards;`
}

export const REDUCED_MOTION_FALLBACK: Record<AnimationPattern, string> = {
  'fade-in': 'opacity: 0; animation: fade-in 100ms ease-out forwards;',
  'fade-in-up': 'opacity: 0; animation: fade-in 100ms ease-out forwards;',
  'fade-in-down': 'opacity: 0; animation: fade-in 100ms ease-out forwards;',
  'fade-in-left': 'opacity: 0; animation: fade-in 100ms ease-out forwards;',
  'fade-in-right': 'opacity: 0; animation: fade-in 100ms ease-out forwards;',
  'scale-in': 'opacity: 0; animation: fade-in 100ms ease-out forwards;',
  'slide-in-left': 'opacity: 0; animation: fade-in 100ms ease-out forwards;',
  'slide-in-right': 'opacity: 0; animation: fade-in 100ms ease-out forwards;',
  'slide-in-up': 'opacity: 0; animation: fade-in 100ms ease-out forwards;',
  'slide-in-down': 'opacity: 0; animation: fade-in 100ms ease-out forwards;',
  'expand-in': 'animation: expand-in 150ms ease-out forwards;',
  stagger: 'opacity: 1;',
  pulse: 'animation: pulse 3000ms ease-in-out infinite;',
  skeleton: 'animation: skeleton 1500ms linear infinite;',
}
