export interface YourWidgetViewProps {
  count: number
  items: YourWidgetItem[]
  isLoading: boolean
}

export interface YourWidgetItem {
  id: string
  label: string
  value: number
}

export interface YourWidgetData {
  count: number
  items: YourWidgetItem[]
}
