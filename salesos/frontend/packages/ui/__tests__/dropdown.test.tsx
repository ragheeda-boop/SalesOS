import { render, screen } from '@testing-library/react'
import { Dropdown, DropdownTrigger, DropdownContent, DropdownItem } from '../src/dropdown'

describe('Dropdown', () => {
  it('renders trigger', () => {
    render(
      <Dropdown>
        <DropdownTrigger>Menu</DropdownTrigger>
        <DropdownContent>
          <DropdownItem>Item 1</DropdownItem>
        </DropdownContent>
      </Dropdown>
    )
    expect(screen.getByText('Menu')).toBeInTheDocument()
  })
})
