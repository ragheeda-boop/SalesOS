export type EasingName = 'ease-standard' | 'ease-out' | 'ease-in'

export type MotionDuration = 120 | 200 | 400 | 600

export interface MotionToken {
  duration: MotionDuration
  easing: string
  delay?: number
}

export const EASING = {
  standard: 'cubic-bezier(0.2, 0, 0, 1)',
  out: 'cubic-bezier(0, 0, 0.2, 1)',
  in: 'cubic-bezier(0.4, 0, 1, 1)',
} as const

export const MOTION = {
  fast: { duration: 120, easing: EASING.out } as MotionToken,
  base: { duration: 200, easing: EASING.standard } as MotionToken,
  slow: { duration: 400, easing: EASING.standard } as MotionToken,
  xslow: { duration: 600, easing: EASING.standard } as MotionToken,

  transitions: {
    fade: 'opacity',
    slide: 'transform translateX',
    scale: 'transform scale',
    height: 'max-height',
    color: 'background-color color border-color',
  },

  presets: {
    modalEnter: { duration: 200, easing: EASING.out } as MotionToken,
    modalExit: { duration: 120, easing: EASING.in } as MotionToken,
    cardHover: { duration: 120, easing: EASING.out } as MotionToken,
    sidebarExpand: { duration: 200, easing: EASING.standard } as MotionToken,
    notificationEnter: { duration: 400, easing: EASING.out } as MotionToken,
    pageTransition: { duration: 200, easing: EASING.standard } as MotionToken,
    tooltipShow: { duration: 120, easing: EASING.out } as MotionToken,
    dropdownShow: { duration: 200, easing: EASING.out } as MotionToken,
  },
} as const
