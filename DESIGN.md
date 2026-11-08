# DESIGN DIRECTION: ThreadScope

> Visual and interaction design direction for ThreadScope: Threads Sentiment & Public Discourse Intelligence Dashboard.
> Follows antislop principles: no generic AI slop, purposeful aesthetics, high readability, light theme.

---

## 1. Product Identity & Purpose
- **Product**: ThreadScope (Social Sentiment & Discourse Intelligence Desk)
- **Audience**: Data analysts, researchers, journalists, and public policy observers.
- **Purpose**: Track, monitor, and analyze public conversation, discourse trends, and sentiment distribution on Threads across diverse topics (environmental issues, regional news, public policy, economic discourse, and viral events).

---

## 2. Mood & Aesthetic Persona
- **Persona**: *Editorial Light Analytics Workspace*: clean, authoritative, objective, and sharp.
- **Atmosphere**: Off-white slate canvas with pure white elevated surface panels, hairline borders, and deep charcoal high-contrast typography. Accents are restrained to semantic indicators (negative, neutral, positive).

---

## 3. Color Palette & Hierarchy
- **Neutrals (Light Theme)**:
  - Canvas Background: `#f8fafc` (Slate 50)
  - Surface Panel / Cards: `#ffffff` (Pure White)
  - Surface Border: `#e2e8f0` (Slate 200, 1px hairline border)
  - Text Primary: `#0f172a` (Slate 900, 15.5:1 contrast against white)
  - Text Secondary: `#475569` (Slate 600, 5.8:1 contrast)
  - Text Muted / Metadata: `#64748b` (Slate 500, 4.6:1 contrast)
- **Semantic Accents (Functional Only)**:
  - **Negative Sentiment (Kritik / Keluhan)**: Text `#b91c1c` (Red 700), background pill `#fef2f2`, border `#fecaca`
  - **Neutral Sentiment (Fakta / Berita)**: Text `#334155` (Slate 700), background pill `#f1f5f9`, border `#e2e8f0`
  - **Positive Sentiment (Apresiasi / Solusi)**: Text `#15803d` (Green 700), background pill `#f0fdf4`, border `#bbf7d0`
  - **Primary Action**: `#0f172a` (Slate 900 solid with white text)

---

## 4. Typography System
- **Interface & Body**: Sans-serif (system-ui, Inter, Geist) for clean readability at all sizes.
- **Data & Metrics**: Monospace tabular numbers (`num-mono`) for totals, percentages, timestamps, and post IDs.

---

## 5. Dials & Antislop Constraints
- **ENERGY**: 1 (Calm, structured, typography-first, no pendar/glow)
- **RHYTHM**: 2 (Consistent grid with balanced metric cards, chart, and feed)
- **MOTION**: 1 (Subtle 120-150ms transitions on interactive states only)
- **Strict Antislop Rules**:
  - NO purple-to-blue gradients
  - NO frosted glassmorphism across multiple layers
  - NO emojis anywhere in the interface
  - NO excessive decorative icons: cards and section headers rely on clear typography
  - NO em dashes in text copy
