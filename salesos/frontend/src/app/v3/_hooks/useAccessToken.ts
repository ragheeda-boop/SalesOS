'use client'

import { useEffect, useState } from 'react'

/**
 * Detects legacy-compatible auth (localStorage access_token).
 * Avoids firing company API calls until we know whether to show a login CTA.
 */
export function useAccessToken(): { ready: boolean; hasToken: boolean } {
 const [ready, setReady] = useState(false)
 const [hasToken, setHasToken] = useState(false)

 useEffect(() => {
 setHasToken(!!localStorage.getItem('access_token'))
 setReady(true)
 }, [])

 return { ready, hasToken }
}
