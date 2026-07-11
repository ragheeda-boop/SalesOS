"use client"

import { useCoachMark } from "./CoachMarkProvider"
import { CoachMarkBubble } from "./CoachMarkBubble"

export function CoachMarkRenderer() {
  const { hints } = useCoachMark()

  if (hints.length === 0) return null

  return (
    <>
      {hints.map((hint) => (
        <CoachMarkBubble
          key={hint.hintId}
          hintId={hint.hintId}
          target={hint.target}
          message={hint.message}
          tourId={hint.tourId}
        />
      ))}
    </>
  )
}
