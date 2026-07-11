export interface MeetingBrief {
  companyName: string
  meetingTitle: string
  date: string
  attendees: { name: string; role: string; influence: string }[]
  recentSignals: string[]
  risks: string[]
  opportunities: string[]
  talkingPoints: string[]
  recommendedAction: string
}
