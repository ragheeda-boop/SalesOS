import { render, screen, fireEvent } from '@testing-library/react'
import { ColumnDef } from '@tanstack/react-table'
import { Table } from '../src/table'

interface TestData {
  id: number
  name: string
}

const columns: ColumnDef<TestData>[] = [
  { header: 'ID', accessorKey: 'id' },
  { header: 'Name', accessorKey: 'name' },
]

const data: TestData[] = [
  { id: 1, name: 'Alice' },
  { id: 2, name: 'Bob' },
]

describe('Table', () => {
  it('renders headers', () => {
    render(<Table columns={columns} data={data} />)
    expect(screen.getByText('ID')).toBeInTheDocument()
    expect(screen.getByText('Name')).toBeInTheDocument()
  })

  it('renders data rows', () => {
    render(<Table columns={columns} data={data} />)
    expect(screen.getByText('Alice')).toBeInTheDocument()
    expect(screen.getByText('Bob')).toBeInTheDocument()
  })

  it('calls onRowClick when row clicked', () => {
    const onRowClick = jest.fn()
    render(<Table columns={columns} data={data} onRowClick={onRowClick} />)
    fireEvent.click(screen.getByText('Alice'))
    expect(onRowClick).toHaveBeenCalledWith(data[0])
  })

  it('shows loading skeleton when loading', () => {
    const { container } = render(<Table columns={columns} data={[]} loading />)
    expect(container.querySelector('.animate-pulse')).toBeInTheDocument()
  })

  it('shows empty state when no data', () => {
    render(<Table columns={columns} data={[]} />)
    expect(screen.getByText('لا توجد بيانات')).toBeInTheDocument()
  })
})
