export type Easing = 'ease' | 'ease-in' | 'ease-out' | 'ease-in-out' | 'spring' | 'bounce'

export type MotionDuration = 50 | 100 | 150 | 200 | 250 | 300 | 400 | 500 | 700 | 1000

export interface MotionToken {
  duration: MotionDuration
  easing: Easing
  delay?: number
}

export const MOTION = {
  instant: { duration: 50, easing: 'ease-out' } as MotionToken,
  fast: { duration: 100, easing: 'ease-out' } as MotionToken,
  normal: { duration: 200, easing: 'ease-in-out' } as MotionToken,
  slow: { duration: 400, easing: 'ease' } as MotionToken,
  expressive: { duration: 700, easing: 'spring' } as MotionToken,

  transitions: {
    fade: 'opacity',
    slide: 'transform translateX',
    scale: 'transform scale',
    height: 'max-height',
    color: 'background-color color border-color',
  },

  presets: {
    modalEnter: { duration: 200, easing: 'ease-out' } as MotionToken,
    modalExit: { duration: 150, easing: 'ease-in' } as MotionToken,
    cardHover: { duration: 150, easing: 'ease-out' } as MotionToken,
    sidebarExpand: { duration: 250, easing: 'ease-in-out' } as MotionToken,
    notificationEnter: { duration: 300, easing: 'spring' } as MotionToken,
    pageTransition: { duration: 200, easing: 'ease-in-out' } as MotionToken,
    tooltipShow: { duration: 100, easing: 'ease-out' } as MotionToken,
    dropdownShow: { duration: 150, easing: 'ease-out' } as MotionToken,
  },
} as const
