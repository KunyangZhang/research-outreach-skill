# Third-party sources

## Academic Research Skills for Codex

- Repository: https://github.com/Imbad0202/academic-research-skills-codex
- Skill: `skills/academic-research-suite`
- Integration tested with: v3.22.0 (Git tag object `3d7285a752695552c6173a3c455175e22c586e84`)
- License: CC BY-NC 4.0; see the dependency repository's LICENSE.
- Relationship: runtime skill composition only; no upstream workflows, role prompts or code are copied into this package.

## OpenAI PDF skill

- Repository: https://github.com/openai/skills
- Path: `skills/.curated/pdf`
- Relationship: optional runtime skill composition only; not vendored or required for SMTP.
- License: see upstream `LICENSE.txt`. No version-specific runtime integration is claimed.

## Minimalist LaTeX CV

- Repository: https://github.com/pmichaillat/latex-cv
- Source commit: `b75426d777cf9f93c968619d0de1f1d1a4444e49`
- Copyright: Pascal Michaillat, 2025–present.
- License: MIT, reproduced at `assets/cv/LICENSE.upstream.md`.
- Vendored: `cv.sty`, `onepage.sty`, upstream license.
- Changes: `cv.sty` adds a XeLaTeX fontspec branch; a new content template and generator supply escaped personal data and optional Chinese ctex/Fandol support. Upstream fictional example CV content is not included.
