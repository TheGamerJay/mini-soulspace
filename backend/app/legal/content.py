"""Versioned legal content for the mandatory signup agreement.

A single combined agreement covers the User Acknowledgment, Terms of Service
and Privacy Policy. Bump ``LEGAL_VERSION`` whenever the wording changes — every
acceptance is audited against the version the user actually saw.
"""

from __future__ import annotations

# ISO date version string. Increment when any document below changes.
LEGAL_VERSION = "2026-06-30"

USER_ACKNOWLEDGMENT = """\
# Mini SoulSpace User Acknowledgment

Mini SoulSpace is a personal SoulDiary — a private space to reflect, and a diary
that talks back. Before you create an account, please understand:

- **Mini SoulSpace is not a medical, crisis, or mental-health service.** It does
  not provide diagnosis, treatment, or professional advice. If you are in crisis
  or may harm yourself or others, contact your local emergency services or a
  crisis line immediately.
- **It is a supportive companion, not a substitute for human care.** Reflections
  are generated to help you feel understood and encouraged, not to make decisions
  for you.
- **Your writing is personal.** You are responsible for what you choose to write
  and share.
- You must be old enough to use the service under our policies and your local law.

By continuing, you acknowledge that you have read and understood the above.
"""

TERMS_OF_SERVICE = """\
# Terms of Service (Summary)

- You agree to use Mini SoulSpace lawfully and for your own personal reflection.
- You will not misuse, disrupt, or attempt to gain unauthorized access to the
  service.
- The service is provided "as is" during early development; features may change.
- We may suspend accounts that violate these terms.

This is a Phase 1 summary; a full Terms of Service will be provided as the
product matures.
"""

PRIVACY_POLICY = """\
# Privacy Policy (Summary)

- We store the account information you provide (display name, email, date of
  birth, country, region, timezone, language) to operate your account.
- Passwords are stored only as secure Argon2id hashes — never in plain text.
- Your acceptance of this agreement is recorded (with timestamp) for compliance.
- We do not sell your personal data.

This is a Phase 1 summary; a full Privacy Policy will be provided as the product
matures.
"""

# Combined document shown in the single acknowledgment modal.
COMBINED_AGREEMENT = "\n\n---\n\n".join(
    [USER_ACKNOWLEDGMENT, TERMS_OF_SERVICE, PRIVACY_POLICY]
)

CHECKBOX_LABEL = (
    "I have read and agree to the Mini SoulSpace User Acknowledgment, "
    "Terms of Service and Privacy Policy."
)
