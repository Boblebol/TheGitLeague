# 🎨 UX & UI Guidelines

This document defines the user experience and user interface standards for **The Git League**.

---

## 📋 Table of Contents

- [Design Principles](#design-principles)
- [Visual Design System](#visual-design-system)
- [Component Library](#component-library)
- [User Flows](#user-flows)
- [Keyboard Shortcuts](#keyboard-shortcuts)
- [Responsive Design](#responsive-design)
- [Accessibility](#accessibility)
- [Animation & Microinteractions](#animation--microinteractions)
- [Error Handling](#error-handling)
- [Loading States](#loading-states)

---

## 🎯 Design Principles

### 1. Speed First ⚡
**Every action must feel instant.**

- Interactions provide feedback < 200ms
- Use optimistic updates (TanStack Query)
- Skeleton loaders for content loading
- No blocking operations in UI thread

**Examples:**
- Sorting leaderboard: instant visual feedback
- Filtering: results update as you type
- Navigation: pre-fetch on hover

### 2. Explainability 🧠
**Users should understand how everything works.**

- Every NBA score is clickable → breakdown modal
- Awards show calculation methodology
- Tooltips explain metrics and abbreviations
- "How it works" sections on complex pages

**Examples:**
- Click PTS score → shows additions, commits, caps applied
- Hover "REB" → tooltip: "Rebounds = Deletions (cleanup work)"
- Awards page has "Scoring Rules" link

### 3. Keyboard-Centric ⌨️
**Power users can navigate without mouse.**

- Command Palette (⌘K) everywhere
- Vim-style navigation (g + l for leaderboard)
- Arrow keys for list navigation
- Shortcuts help (⌘/)

**Examples:**
- ⌘K → quick jump to any page
- g then l → leaderboard
- / → focus search

### 4. Storytelling 👀
**Data tells a story, not just numbers.**

- "Play of the Day" highlights great work
- Weekly/monthly awards create rhythm
- Player profiles show progression (trends)
- Season narratives (recap at end)

**Examples:**
- Dashboard shows "This week's highlights"
- Player cards have "Rising Star" badges
- Awards page has storylines

### 5. Enterprise-Safe 🔒
**Clear permissions, no data leaks.**

- Role badges visible (Commissioner, Player, Spectator)
- Protected actions require confirmation
- Audit trail for sensitive operations
- No code/secrets exposed in UI

**Examples:**
- Spectators see read-only UI
- Delete repo → confirmation modal
- Commissioner settings clearly separated

---

## 🎨 Visual Design System

### Color Palette

**Primary Colors (Basketball Theme):**
```css
--primary-orange: #FF6B35;      /* NBA basketball orange */
--primary-blue: #004E89;        /* Deep blue (court) */
--primary-gold: #FFD700;        /* Championship gold */
```

**Semantic Colors:**
```css
--success: #10B981;             /* Green (positive) */
--warning: #F59E0B;             /* Amber (caution) */
--error: #EF4444;               /* Red (error) */
--info: #3B82F6;                /* Blue (info) */
```

**Neutral Colors:**
```css
--background: #FFFFFF;          /* Light mode background */
--surface: #F9FAFB;             /* Card background */
--border: #E5E7EB;              /* Borders */
--text-primary: #111827;        /* Main text */
--text-secondary: #6B7280;      /* Secondary text */
--text-muted: #9CA3AF;          /* Muted text */
```

**Dark Mode:**
```css
--dark-background: #0F172A;     /* Dark background */
--dark-surface: #1E293B;        /* Dark card */
--dark-border: #334155;         /* Dark borders */
--dark-text-primary: #F1F5F9;   /* Dark text */
--dark-text-secondary: #94A3B8; /* Dark secondary */
```

### Typography

**Font Stack:**
```css
--font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
--font-mono: 'JetBrains Mono', 'Fira Code', 'Courier New', monospace;
```

**Type Scale:**
```css
--text-xs: 0.75rem;     /* 12px - Small labels */
--text-sm: 0.875rem;    /* 14px - Body small */
--text-base: 1rem;      /* 16px - Body */
--text-lg: 1.125rem;    /* 18px - Subheading */
--text-xl: 1.25rem;     /* 20px - Heading */
--text-2xl: 1.5rem;     /* 24px - Page title */
--text-3xl: 1.875rem;   /* 30px - Hero */
--text-4xl: 2.25rem;    /* 36px - Display */
```

**Font Weights:**
- Regular: 400 (body text)
- Medium: 500 (emphasis)
- Semibold: 600 (headings)
- Bold: 700 (highlights)

### Spacing Scale

**Consistent spacing using 4px base:**
```css
--space-1: 0.25rem;  /* 4px */
--space-2: 0.5rem;   /* 8px */
--space-3: 0.75rem;  /* 12px */
--space-4: 1rem;     /* 16px */
--space-6: 1.5rem;   /* 24px */
--space-8: 2rem;     /* 32px */
--space-12: 3rem;    /* 48px */
--space-16: 4rem;    /* 64px */
```

### Elevation (Shadows)

```css
--shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
--shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1);
--shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1);
--shadow-xl: 0 20px 25px -5px rgb(0 0 0 / 0.1);
```

### Border Radius

```css
--radius-sm: 0.25rem;  /* 4px */
--radius-md: 0.375rem; /* 6px */
--radius-lg: 0.5rem;   /* 8px */
--radius-xl: 0.75rem;  /* 12px */
--radius-full: 9999px; /* Pill shape */
```

---

## 🧩 Component Library

### 1. Global Shell

**Top Navigation Bar**

```
┌────────────────────────────────────────────────────────────┐
│ 🏀 The Git League  [Project ▼] [Season ▼]  🔍  [User ▼]   │
└────────────────────────────────────────────────────────────┘
```

**Elements:**
- Logo (clickable → home)
- Project switcher (dropdown)
- Season switcher (dropdown)
- Global search (⌘K trigger)
- User menu (profile, settings, logout)

**Responsive:**
- Mobile: Hamburger menu + condensed nav

---

### 2. Leaderboard Component

**Desktop Layout:**
```
┌──────────────────────────────────────────────────────────────┐
│ 🏆 Leaderboard                     Metric: [PTS ▼]           │
│ Filters: [All Repos ▼] [This Week ▼]     Search: [____]     │
├──────────────────────────────────────────────────────────────┤
│ #  Player              PTS   REB   AST   BLK   TOV  Trend    │
│ 1  🥇 Alice            124↗  52    31    4     9    ↗ +15%   │
│ 2  🥈 Bob              118→  70    18    2     5    → 0%     │
│ 3  🥉 Chloé            111↘  40    45    1     7    ↘ -5%    │
│ 4     David            98    35    28    6     12   ↗ +8%    │
└──────────────────────────────────────────────────────────────┘
```

**Features:**
- Top 3 with medal icons
- Sortable columns (click header)
- Trend arrows (up/down/neutral)
- Clickable rows → player profile
- Infinite scroll or pagination

**States:**
- Empty: "No commits ingested yet" + CTA
- Loading: Skeleton rows
- Error: Error message + "Retry" button

---

### 3. Player Card Component

**Compact Card (for lists):**
```
┌────────────────────────────────┐
│ Alice "The Builder" 🌟         │
│ PTS: 124  REB: 52  AST: 31     │
│ Rank: #3  ↗ Rising             │
└────────────────────────────────┘
```

**Full Profile Page:**
```
┌──────────────────────────────────────────────────────────────┐
│ Alice "The Builder" — SG               [Follow ☆]  Active    │
│ Season: 2024 S1   [Season] [Career] [Awards] [Repos]         │
├──────────────────────────────────────────────────────────────┤
│ PTS: 124 (click for breakdown)  REB: 52  AST: 31  Impact: 78 │
│                                                                │
│ [Weekly trend graph - last 12 weeks]                          │
│                                                                │
│ 🏅 Awards                                                      │
│ • Player of the Week x2                                       │
│ • MVP x1                                                       │
│                                                                │
│ 📌 Best Plays                                                  │
│ [Commit cards...]                                              │
└──────────────────────────────────────────────────────────────┘
```

**Interactions:**
- Click metric → score breakdown modal
- Tabs: 1 (Season), 2 (Career), 3 (Awards), 4 (Repos)
- Follow button → add to favorites

---

### 4. Award Card

```
┌────────────────────────────────────┐
│ 🏆 Player of the Week              │
│ Week of Jan 15, 2024               │
│                                    │
│ [Avatar] Alice "The Builder"       │
│ Score: 1,234                       │
│                                    │
│ Breakdown:                         │
│ • 45 commits                       │
│ • 1,234 additions                  │
│ • 15 multi-file commits            │
│                                    │
│ [View Details →]                   │
└────────────────────────────────────┘
```

---

### 5. Play of the Day Card

```
┌────────────────────────────────────────────────┐
│ 🎯 Play of the Day — Jan 20, 2024              │
│                                                │
│ "Implement caching layer for API"             │
│ Alice • backend • 15:30                        │
│                                                │
│ +234 -45 • 8 files changed                     │
│ Score: 892 (PTS: 244, REB: 27, AST: 10)        │
│                                                │
│ [View Commit →]                                │
└────────────────────────────────────────────────┘
```

---

### 6. Commissioner Console

```
┌──────────────────────────────────────────────────────────────┐
│ ⚙️ Commissioner Console                                       │
├──────────────────────────────────────────────────────────────┤
│ [Projects] [Repos] [Seasons] [Rules] [Access] [Sync Logs]   │
├──────────────────────────────────────────────────────────────┤
│ Repositories                                                 │
│                                                              │
│ ✅ backend       Last sync: 10:32  [Sync Now] [Edit]         │
│ ❌ frontend      Error: Auth failed [View Logs] [Edit]       │
│ ⏳ api-gateway   Syncing... 45%                              │
│                                                              │
│ [Add Repository]  [Sync All]  [Recompute Season]            │
└──────────────────────────────────────────────────────────────┘
```

---

### 7. Fantasy Draft Interface

```
┌──────────────────────────────────────────────────────────────┐
│ 🎮 Fantasy Draft — Engineering League 2024                   │
│ Roster: 3/5 picks   Lock Date: Jan 31, 2024   [Lock Roster] │
├──────────────────────────────────────────────────────────────┤
│ Your Picks                    │  Available Players           │
│ 1. Alice (PTS: 124)          │  [Search: ____]              │
│ 2. Bob (PTS: 118)            │                              │
│ 3. Chloé (PTS: 111)          │  David (PTS: 98) [+ Add]     │
│ 4. [Empty] [+ Add Pick]      │  Eve (PTS: 95) [+ Add]       │
│ 5. [Empty] [+ Add Pick]      │  Frank (PTS: 89) [+ Add]     │
│                              │  ...                         │
│ Current Score: 353           │                              │
└──────────────────────────────────────────────────────────────┘
```

---

## 🔄 User Flows

### Flow 1: Commissioner Setup (First Time)

```
1. Land on homepage (not authenticated)
   → [Get Started] button

2. Enter email
   → Magic link sent confirmation

3. Click magic link in email
   → Redirected to app, authenticated

4. Onboarding wizard:
   Step 1: Create Project
   → Enter name, slug
   → [Next]

   Step 2: Add First Repo
   → Choose type (SSH/HTTPS/Local)
   → Enter URL, credentials
   → [Test Connection] → [Add Repo]

   Step 3: Sync Now
   → Progress bar: "Ingesting commits..."
   → Success: "1,234 commits ingested"

   Step 4: Create Season
   → Enter name, start/end dates
   → [Activate Season]

   Step 5: Configure Scoring
   → Adjust coefficients (defaults shown)
   → Preview score changes
   → [Save & Continue]

5. Dashboard appears
   → Shows first leaderboard
   → Prompt to invite players
```

---

### Flow 2: Player Login & View Stats

```
1. Click magic link from invitation
   → Authenticated, redirected to leaderboard

2. See leaderboard with own rank highlighted
   → Click own name

3. Player profile opens
   → Current season stats shown
   → Awards (if any)
   → Recent commits

4. Click "Career" tab
   → All-time stats, graph
   → Historical awards

5. Click PTS score (e.g., "124")
   → Modal opens with breakdown:
     - 45 commits × 10 base = 450
     - 1,234 additions (capped 1,000) × 1.0 = 1,000
     - Total PTS = 1,450
   → [Close modal]
```

---

### Flow 3: Join Fantasy League

```
1. Navigate to Fantasy page
   → See available leagues

2. Click league card
   → League details + participants
   → [Join League] button

3. Draft page opens
   → See draftable pool
   → Search/filter players

4. Add picks (click [+ Add])
   → Player added to roster
   → Score updates in real-time

5. Lock roster
   → Confirmation: "Lock roster? Cannot undo."
   → [Confirm Lock]
   → Roster locked, changes disabled

6. View fantasy leaderboard
   → See rank vs other participants
   → Check weekly score updates
```

---

### Flow 4: View Play of the Day

```
1. Navigate to Highlights page
   → See list of recent "Plays of the Day"

2. Click a play card
   → Commit detail modal opens
     - Full message
     - Stats breakdown
     - Score explanation
     - Author profile link

3. Click author name
   → Redirected to player profile

4. Click repo name
   → Filter leaderboard by that repo
```

---

## ⌨️ Keyboard Shortcuts

### Global Shortcuts (work anywhere in app)

| Shortcut | Action |
|----------|--------|
| `⌘K` / `Ctrl+K` | Open Command Palette |
| `⌘/` / `Ctrl+/` | Show keyboard shortcuts help |
| `Esc` | Close modals / drawers |
| `⌘Enter` | Confirm primary action in modal |

### Navigation (g + letter)

| Shortcut | Action |
|----------|--------|
| `g` then `l` | Go to **Leaderboard** |
| `g` then `p` | Go to **My Profile** |
| `g` then `a` | Go to **Awards** |
| `g` then `f` | Go to **Fantasy** |
| `g` then `h` | Go to **Highlights** (Plays) |
| `g` then `s` | Go to **Settings** (Commissioner only) |
| `⌥←` / `⌥→` | Navigate period (previous/next week/month) |

### Search & Filters

| Shortcut | Action |
|----------|--------|
| `/` | Focus search input (if present) |
| `⌥1` to `⌥5` | Switch metric (PTS, REB, AST, BLK, Impact) |
| `⌥R` | Open repo filter dropdown |
| `⌥T` | Open period filter (week/month/season) |

### Leaderboard

| Shortcut | Action |
|----------|--------|
| `↑` / `↓` | Navigate player list |
| `Enter` | Open selected player profile |
| `Space` | Follow/unfollow player (favorite) |
| `⌘D` | Open score breakdown for selected player |

### Player Profile

| Shortcut | Action |
|----------|--------|
| `1` | Switch to "Season" tab |
| `2` | Switch to "Career" tab |
| `3` | Switch to "Awards" tab |
| `4` | Switch to "Repos" tab |

### Fantasy

| Shortcut | Action |
|----------|--------|
| `⌘N` | New roster / modify picks |
| `⌘S` | Save roster |
| `⌘L` | Lock roster (if authorized) |
| `⌥↑` / `⌥↓` | Reorder picks |

### Commissioner Console

| Shortcut | Action |
|----------|--------|
| `⌘N` | New project/repo/season (context-aware) |
| `⌘S` | Save configuration |
| `⌘B` | Sync now (refresh repos) |
| `⌘⇧L` | Open sync logs |

---

## 📱 Responsive Design

### Breakpoints

```css
--screen-sm: 640px;   /* Mobile landscape */
--screen-md: 768px;   /* Tablet */
--screen-lg: 1024px;  /* Desktop */
--screen-xl: 1280px;  /* Large desktop */
--screen-2xl: 1536px; /* Ultra-wide */
```

### Mobile Adaptations

**Navigation:**
- Top nav → Hamburger menu
- Tabs → Horizontal scroll

**Leaderboard:**
- Hide less important columns (BLK, STL, TOV)
- Swipe left/right to reveal more columns
- Tap row → player profile (no hover states)

**Player Profile:**
- Tabs become horizontal scrollable pills
- Graph: touch to see values

**Fantasy Draft:**
- Stack "Your Picks" and "Available Players" vertically
- Fullscreen modal on mobile

---

## ♿ Accessibility

### WCAG AA Compliance

**Contrast:**
- Text on background: 4.5:1 minimum
- Large text (18px+): 3:1 minimum
- UI components: 3:1 minimum

**Keyboard Navigation:**
- All interactive elements are focusable
- Focus visible (ring outline)
- Tab order is logical (top to bottom, left to right)
- Roving tabindex on lists

**Screen Readers:**
- Semantic HTML (`<nav>`, `<main>`, `<article>`)
- ARIA labels on icons and buttons
- `aria-describedby` for tooltips
- `aria-live` regions for dynamic updates

**Forms:**
- Labels associated with inputs
- Error messages linked with `aria-describedby`
- Required fields marked with `aria-required`

### Focus Management

**Visible focus states:**
```css
:focus-visible {
  outline: 2px solid var(--primary-blue);
  outline-offset: 2px;
}
```

**Skip links:**
```html
<a href="#main-content" class="skip-link">
  Skip to main content
</a>
```

---

## 🎬 Animation & Microinteractions

### Principles

1. **Purposeful:** Animations guide attention
2. **Fast:** Keep under 300ms for most animations
3. **Respectful:** Honor `prefers-reduced-motion`

### Standard Animations

**Page transitions:**
```css
.page-enter {
  opacity: 0;
  transform: translateY(10px);
}
.page-enter-active {
  opacity: 1;
  transform: translateY(0);
  transition: all 200ms ease-out;
}
```

**Hover effects (buttons, cards):**
```css
.card {
  transition: transform 150ms, box-shadow 150ms;
}
.card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
}
```

**Loading spinners:**
- Use CSS animations (not GIFs)
- Smooth, 1-2 second loop

**Success states:**
- Green checkmark fade-in + scale
- Confetti for major achievements (awards)

**Error shake:**
```css
@keyframes shake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-5px); }
  75% { transform: translateX(5px); }
}
```

### Reduced Motion

```css
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

---

## 🚨 Error Handling

### Error Types & UI

**1. Validation Errors (400)**
```
┌──────────────────────────────────────┐
│ ⚠️ Invalid Input                     │
│ Email format is invalid.             │
│ [Dismiss]                            │
└──────────────────────────────────────┘
```
- Inline form errors (below field)
- Red border on invalid field
- Clear error message

**2. Authentication Errors (401)**
```
Session expired. Please log in again.
[Re-authenticate]
```
- Redirect to login after timeout
- Preserve return URL

**3. Permission Errors (403)**
```
┌──────────────────────────────────────┐
│ 🔒 Access Denied                     │
│ You need Commissioner role to        │
│ perform this action.                 │
│ [Go Back]                            │
└──────────────────────────────────────┘
```

**4. Not Found (404)**
```
┌──────────────────────────────────────┐
│ 😕 Player Not Found                  │
│ This player may have been retired    │
│ or removed.                          │
│ [Back to Leaderboard]                │
└──────────────────────────────────────┘
```

**5. Server Errors (500)**
```
┌──────────────────────────────────────┐
│ 💥 Something Went Wrong              │
│ We're working on it. Try again in    │
│ a few moments.                       │
│ [Retry] [Report Issue]               │
└──────────────────────────────────────┘
```

**6. Network Errors**
```
┌──────────────────────────────────────┐
│ 📡 Connection Lost                   │
│ Check your internet connection.      │
│ [Retry]                              │
└──────────────────────────────────────┘
```

### Toast Notifications

**Success:**
```
✅ Repo synced successfully (1,234 commits)
```

**Error:**
```
❌ Failed to sync repo: Invalid credentials
```

**Info:**
```
ℹ️ Season "2024 Q1" is now active
```

**Warning:**
```
⚠️ Lock date is in 2 hours — finalize your roster!
```

**Position:** Bottom-right, auto-dismiss after 5s

---

## ⏳ Loading States

### Skeleton Loaders

**Leaderboard skeleton:**
```
┌──────────────────────────────────────┐
│ ▓▓▓ ▓▓▓▓▓▓▓  ▓▓▓  ▓▓▓  ▓▓▓  ▓▓▓     │
│ ▓▓▓ ▓▓▓▓▓▓▓  ▓▓▓  ▓▓▓  ▓▓▓  ▓▓▓     │
│ ▓▓▓ ▓▓▓▓▓▓▓  ▓▓▓  ▓▓▓  ▓▓▓  ▓▓▓     │
└──────────────────────────────────────┘
```
- Pulsing gray rectangles
- Matches layout of loaded content

### Progress Indicators

**Sync progress:**
```
Syncing backend repo...
[████████████░░░░░░░░] 60% (6,000 / 10,000 commits)
```

**Upload/processing:**
```
Processing configuration...
[Spinner animation] Please wait
```

### Optimistic Updates

- Fantasy roster changes: Update UI immediately, rollback on error
- Follow/unfollow: Instant visual feedback
- Leaderboard sorting: Client-side instant sort

---

## 🎨 Design Tokens (Summary)

```javascript
// tokens.js
export const tokens = {
  colors: {
    primary: { orange: '#FF6B35', blue: '#004E89', gold: '#FFD700' },
    semantic: { success: '#10B981', warning: '#F59E0B', error: '#EF4444' },
  },
  spacing: { 1: '4px', 2: '8px', 4: '16px', 6: '24px', 8: '32px' },
  typography: {
    fontFamily: { sans: 'Inter, sans-serif', mono: 'JetBrains Mono, monospace' },
    fontSize: { xs: '12px', sm: '14px', base: '16px', lg: '18px', xl: '20px' },
  },
  animation: {
    duration: { fast: '150ms', normal: '200ms', slow: '300ms' },
    easing: { easeOut: 'cubic-bezier(0, 0, 0.2, 1)' },
  },
};
```

---

## ✅ UX Checklist (per feature)

Before shipping any feature, verify:

- [ ] **Speed:** Interactions feel < 200ms
- [ ] **Keyboard:** All actions accessible via keyboard
- [ ] **Responsive:** Works on mobile, tablet, desktop
- [ ] **Accessible:** WCAG AA compliant
- [ ] **Error handling:** Clear error messages, recovery options
- [ ] **Loading states:** Skeletons/spinners for async operations
- [ ] **Empty states:** Helpful guidance when no data
- [ ] **Help:** Tooltips, explainers, or links to docs
- [ ] **Consistency:** Follows established patterns

---

**For implementation details, see [DEVELOPMENT.md](./DEVELOPMENT.md)**

**For component examples, see the Storybook** (coming soon)
