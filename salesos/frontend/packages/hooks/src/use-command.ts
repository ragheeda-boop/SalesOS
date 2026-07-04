import { useState, useEffect, useCallback } from 'react'
import { useRuntime } from './use-runtime'

export interface Command {
  id: string
  label: string
  description?: string
  shortcut?: string
  category?: string
  icon?: string
  handler: () => void
}

let globalCommands: Command[] = []
let globalListeners = new Set<() => void>()

export function registerCommand(command: Command): () => void {
  globalCommands = globalCommands.filter((c) => c.id !== command.id)
  globalCommands.push(command)
  globalListeners.forEach((fn) => fn())
  return () => {
    globalCommands = globalCommands.filter((c) => c.id !== command.id)
    globalListeners.forEach((fn) => fn())
  }
}

export function useCommands() {
  const [commands, setCommands] = useState<Command[]>(globalCommands)

  useEffect(() => {
    const listener = () => setCommands([...globalCommands])
    globalListeners.add(listener)
    return () => { globalListeners.delete(listener) }
  }, [])

  const execute = useCallback((commandId: string) => {
    const cmd = globalCommands.find((c) => c.id === commandId)
    cmd?.handler()
  }, [])

  return { commands, execute }
}
