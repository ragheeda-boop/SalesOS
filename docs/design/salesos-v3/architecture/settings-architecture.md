# Settings Architecture

Settings are a **domain**, not a single scroll page.

## IA

| Section | Audience | Contents |
|---------|----------|----------|
| Workspace | Admins | Name, branding, defaults, modules |
| Personal | All | Profile, preferences |
| Security | Admins + self | MFA, sessions, SSO |
| Billing | Billing admins | Plan, invoices |
| Notifications | All | Channels, digests, quiet hours |
| API | Admins | API keys, webhooks |
| Integrations | Admins | Connected apps |
| AI | Admins + users | Model prefs, Preview flags, retention |
| Appearance | All | Theme, density |
| Language | All | Locale, RTL |
| Accessibility | All | Reduced motion, contrast |

## UX rules

- Left subnav within Settings domain.
- Dangerous actions confirm + audit.
- AI section links honesty policy; cannot enable GA without evaluation gate.
