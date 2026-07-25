# Auth Screens

## Login
1. Purpose: authenticate user. 2. Goals: fast secure entry. 3. IA: email/password, SSO, MFA continue. 4. Layout: split brand panel + form (desktop). 5. Wireframe: logo, fields, primary CTA, links. 6. Components: Input, Button, FormField. 7. Flow: submit → MFA or org select → shell. 8–10. Stacked form on mobile. 11. AI: none. 12–15. Validation empty/error; lockout message; loading button. 16. Minimize JS. 17. Labels, autocomplete, contrast. 18. Passkeys.

## Forgot Password
Purpose reset; email field; success empty-state; no user enumeration.

## MFA
TOTP/WebAuthn; trust device optional; error/retry.

## Invitation
Token landing; set password; accept workspace.

## Organization Selection
List workspaces; search; last-used; continue → shell.
