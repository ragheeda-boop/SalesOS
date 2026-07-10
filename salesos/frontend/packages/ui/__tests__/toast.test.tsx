import { render, screen, fireEvent } from '@testing-library/react'
import { Toast, ToastProvider, ToastViewport, useToast } from '../src/toast'

describe('Toast', () => {
  it('renders with title and description', () => {
    render(
      <ToastProvider>
        <ToastViewport>
          <Toast title="Success" description="Operation completed" />
        </ToastViewport>
      </ToastProvider>
    )
    expect(screen.getByText('Success')).toBeInTheDocument()
    expect(screen.getByText('Operation completed')).toBeInTheDocument()
  })
})
