import type { Meta, StoryObj } from '@storybook/react'
import { BarChart, LineChart, PieChart, MetricCard } from './index'

const meta = { title: 'Charts' } satisfies Meta
export default meta

export const BarChartStory: StoryObj = {
  render: () => (
    <BarChart
      data={[
        { label: 'Q1', value: 400 },
        { label: 'Q2', value: 300 },
        { label: 'Q3', value: 600 },
        { label: 'Q4', value: 200 },
      ]}
      title="Quarterly Revenue"
      height={250}
    />
  ),
}

export const LineChartStory: StoryObj = {
  render: () => (
    <LineChart
      series={[
        { name: 'Actual', color: '#3B82F6', data: [400, 300, 600, 800] },
        { name: 'Forecast', color: '#10B981', data: [350, 400, 550, 750] },
      ]}
      title="Revenue vs Forecast"
      height={250}
    />
  ),
}

export const PieChartStory: StoryObj = {
  render: () => (
    <PieChart
      data={[
        { label: 'Enterprise', value: 45 },
        { label: 'SMB', value: 30 },
        { label: 'Government', value: 15 },
        { label: 'Startup', value: 10 },
      ]}
      title="Revenue by Segment"
    />
  ),
}

export const MetricCardStory: StoryObj = {
  render: () => (
    <div className="grid grid-cols-3 gap-4 max-w-2xl">
      <MetricCard label="Total Revenue" value="$1.2M" trend={{ direction: 'up', percentage: 12 }} />
      <MetricCard label="Active Deals" value="48" trend={{ direction: 'up', percentage: 8 }} />
      <MetricCard label="Win Rate" value="34%" trend={{ direction: 'down', percentage: 3 }} />
    </div>
  ),
}
