export interface TourStep {
  target: string
  title: string
  description: string
  position: 'top' | 'bottom' | 'left' | 'right' | 'center'
  image?: string
  beforeStep?: () => void
  afterStep?: () => void
}
