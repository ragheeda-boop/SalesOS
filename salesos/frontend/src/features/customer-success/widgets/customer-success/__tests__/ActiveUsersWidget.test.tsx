import { render, screen } from '@testing-library/react'
import { ActiveUsersWidget } from '../ActiveUsersWidget'

function renderView(dau = 25, wau = 120, mau = 450) {
  return render(<ActiveUsersWidget dau={dau} wau={wau} mau={mau} />)
}

describe('ActiveUsersWidget', () => {
  it('renders DAU value', () => {
    renderView()
    expect(screen.getByText('25')).toBeInTheDocument()
  })

  it('renders WAU value', () => {
    renderView()
    expect(screen.getByText('120')).toBeInTheDocument()
  })

  it('renders MAU value', () => {
    renderView()
    expect(screen.getByText('450')).toBeInTheDocument()
  })

  it('renders section title', () => {
    renderView()
    expect(screen.getByText('المستخدمون النشطون')).toBeInTheDocument()
  })

  it('renders Daily label', () => {
    renderView()
    expect(screen.getByText('يومي')).toBeInTheDocument()
  })

  it('renders Weekly label', () => {
    renderView()
    expect(screen.getByText('أسبوعي')).toBeInTheDocument()
  })

  it('renders Monthly label', () => {
    renderView()
    expect(screen.getByText('شهري')).toBeInTheDocument()
  })

  it('displays zero values correctly', () => {
    renderView(0, 0, 0)
    const zeros = screen.getAllByText('0')
    expect(zeros.length).toBeGreaterThanOrEqual(3)
  })

  it('displays large values correctly', () => {
    renderView(1000, 5000, 20000)
    expect(screen.getByText('1000')).toBeInTheDocument()
    expect(screen.getByText('5000')).toBeInTheDocument()
    expect(screen.getByText('20000')).toBeInTheDocument()
  })
})
