import { render, screen } from '@testing-library/react'
import { Modal, ModalTrigger, ModalContent, ModalHeader, ModalBody, ModalFooter } from '../src/modal'

describe('Modal', () => {
  it('renders trigger', () => {
    render(
      <Modal>
        <ModalTrigger>Open</ModalTrigger>
        <ModalContent>
          <ModalHeader>Title</ModalHeader>
          <ModalBody>Body</ModalBody>
          <ModalFooter>Footer</ModalFooter>
        </ModalContent>
      </Modal>
    )
    expect(screen.getByText('Open')).toBeInTheDocument()
  })

  it('components have displayNames', () => {
    expect(ModalTrigger.displayName).toBe('ModalTrigger')
    expect(ModalContent.displayName).toBe('ModalContent')
    expect(ModalHeader.displayName).toBe('ModalHeader')
    expect(ModalBody.displayName).toBe('ModalBody')
    expect(ModalFooter.displayName).toBe('ModalFooter')
  })
})
