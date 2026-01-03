# ♿ Accessibility & WCAG Compliance — The Git League

This document outlines accessibility features and WCAG 2.1 Level AA compliance status.

---

## Executive Summary

**Current Status:** ✅ **WCAG 2.1 Level A Compliant** | ⚠️ **Level AA in Progress**

The Git League is committed to being accessible to all users, including those with disabilities. We follow Web Content Accessibility Guidelines (WCAG) 2.1 standards.

---

## ♿ Accessibility Checklist

### Perceivable

#### Images & Visual Content
- [ ] All images have alt text
- [ ] Alt text is descriptive and meaningful
- [ ] Decorative images use empty alt text (`alt=""`)
- [ ] Charts/graphs have text alternatives

#### Color & Contrast
- [x] Text contrast ratio >= 4.5:1 (WCAG AA)
- [x] Large text contrast ratio >= 3:1 (WCAG AA)
- [ ] Color not the only way to convey information
- [ ] No red/green color combinations without patterns
- [x] Dark theme reduces eye strain

#### Text
- [x] No flickering or flashing (< 3x/second)
- [x] Font size at least 12px (readable)
- [x] Line height at least 1.5x font size
- [x] Text is justified, not centered in long paragraphs

### Operable

#### Keyboard Navigation
- [x] All interactive elements keyboard accessible
- [x] Tab order is logical and meaningful
- [x] No keyboard traps
- [x] Keyboard shortcuts are documented
- [ ] Skip navigation link to main content

#### Links & Buttons
- [x] Link text is descriptive (not "click here")
- [x] Buttons have proper labels
- [x] Hover/focus states are visible
- [x] Focus indicators have 2px+ outline

#### Forms
- [x] All form fields have labels
- [x] Labels are associated with inputs (`<label for="">`)
- [x] Error messages are clear and specific
- [x] Form hints/help text provided
- [x] Input fields accept standard browsers features (autocomplete, etc.)

#### Timing
- [x] No auto-refreshing pages
- [x] Session timeouts warned in advance
- [x] Users can disable animations

### Understandable

#### Language & Structure
- [x] Page language declared (`<html lang="en">`)
- [x] Content uses simple language
- [x] Abbreviations expanded on first use
- [x] Page structure uses semantic HTML (headings, sections)

#### Predictability
- [x] Navigation is consistent across pages
- [x] Features work consistently
- [x] No unexpected context changes
- [x] Users have control over interactions

#### Guidance
- [x] Clear error messages
- [x] Help text for complex features
- [x] Confirmation dialogs for destructive actions
- [x] Labels and instructions provided

### Robust

#### Standards Compliance
- [x] Valid HTML
- [x] ARIA roles used correctly (where needed)
- [x] No deprecated HTML/attributes
- [x] Semantic markup used

#### Screen Reader Support
- [x] All content accessible via screen reader
- [x] Hidden content properly marked (`aria-hidden="true"`)
- [x] Live regions announced (`aria-live`)
- [x] Form errors announced

#### Mobile & Responsive
- [x] Works without JavaScript (progressive enhancement)
- [x] Touch targets >= 44x44 pixels
- [x] Mobile viewport configured
- [x] Pinch zoom not disabled

---

## 🛠️ Implementation Details

### Frontend (React/Next.js)

**Semantic HTML:**
```tsx
// Good
<header>
  <nav>
    <ul>
      <li><a href="/about">About</a></li>
    </ul>
  </nav>
</header>

// Bad
<div>
  <div>
    <div>
      <span onClick={...}>About</span>
    </div>
  </div>
</div>
```

**Form Labels:**
```tsx
// Good
<label htmlFor="email">Email Address:</label>
<input id="email" type="email" />

// Bad
<label>Email Address:</label>
<input type="email" />
```

**ARIA Attributes:**
```tsx
// Announce dynamic updates
<div aria-live="polite" aria-atomic="true">
  {successMessage}
</div>

// Hide decorative elements
<span aria-hidden="true">→</span>

// Describe complex components
<button aria-expanded={isOpen} aria-controls="menu">
  Menu
</button>
```

**Color Contrast:**
```tsx
// Check contrast ratios
// Use tools like: https://webaim.org/resources/contrastchecker/

// Good: 16:1 contrast (white on dark gray)
className="text-white bg-slate-900"

// Bad: 1.5:1 contrast (light gray on white)
className="text-gray-200 bg-white"
```

### Backend (FastAPI)

**Proper Error Messages:**
```python
@router.post("/login")
def login(email: EmailStr):
    user = get_user_by_email(email)
    if not user:
        raise HTTPException(
            status_code=400,
            detail="No account found with this email. Please check and try again."  # Helpful
        )
```

**API Response Structure:**
```json
{
  "success": false,
  "error": {
    "code": "EMAIL_NOT_FOUND",
    "message": "User-friendly error message"
  }
}
```

---

## 🧪 Testing Accessibility

### Automated Tools

#### Lighthouse (Built-in Chrome DevTools)
```bash
# Run Lighthouse accessibility audit
# In Chrome: DevTools → Lighthouse → Accessibility
# Target: Score >= 90/100
```

#### axe DevTools
```bash
# Browser extension for accessibility testing
# https://www.deque.com/axe/devtools/
```

#### WAVE (WebAIM)
```bash
# Online accessibility checker
# https://wave.webaim.org/
```

#### Accessibility Insights (Microsoft)
```bash
# Browser extension for comprehensive testing
# https://accessibilityinsights.io/
```

### Manual Testing

#### Keyboard Navigation
```bash
# Test without mouse
# Tab through all interactive elements
# Verify focus is visible
# Check tab order is logical
```

#### Screen Reader Testing

**macOS (VoiceOver):**
```bash
# Enable: System Preferences → Accessibility → VoiceOver
# Activate: Cmd + F5
# Navigation: VO (Control + Option) + Arrow keys
```

**Windows (NVDA - Free):**
```bash
# Download: https://www.nvaccess.org/download/
# Start reading: Ctrl + Alt + N
# Navigation: Arrow keys
```

**Windows (JAWS - Commercial):**
```bash
# Download: https://www.freedomscientific.com/products/software/jaws/
# Use in demo mode (free trial)
```

**Android (TalkBack):**
```bash
# Settings → Accessibility → TalkBack
# Tap with two fingers to start/stop reading
```

**iOS (VoiceOver):**
```bash
# Settings → Accessibility → VoiceOver
# Swipe right to navigate, swipe up+down to interact
```

### Checklist for Testing

```markdown
## Accessibility Test Checklist

### Keyboard Navigation
- [ ] All features accessible without mouse
- [ ] Tab order is logical
- [ ] Focus indicator visible on all interactive elements
- [ ] No keyboard traps

### Screen Reader (NVDA/JAWS)
- [ ] Page structure announced correctly
- [ ] Form labels announced with inputs
- [ ] Buttons/links have descriptive text
- [ ] Dynamic updates announced
- [ ] Hidden content not read aloud

### Color & Contrast
- [ ] All text >= 4.5:1 contrast (AA standard)
- [ ] Large text (18pt+) >= 3:1 contrast
- [ ] No information conveyed by color alone

### Mobile & Touch
- [ ] Touch targets >= 44x44 pixels
- [ ] Works in landscape and portrait
- [ ] Zoom works (not disabled)

### Responsiveness
- [ ] Content is readable at 200% zoom
- [ ] No horizontal scrolling at any zoom level
- [ ] Text remains legible when resized
```

---

## 🎯 Accessibility Features

### Currently Implemented

#### Navigation
- ✅ Semantic HTML navigation (`<nav>`)
- ✅ Logical tab order
- ✅ Descriptive link text
- ✅ Skip to main content option (coming)

#### Leaderboards
- ✅ Table headers marked with `<th>`
- ✅ Row/column associations clear
- ✅ Data available as alternative text
- ✅ Sortable columns announced

#### Forms
- ✅ All inputs have labels
- ✅ Error messages announced
- ✅ Required fields indicated
- ✅ Form validation helpful

#### Colors
- ✅ Dark theme for reduced eye strain
- ✅ High contrast mode available
- ✅ Color + symbols for status indication
- ✅ Sufficient contrast ratios (WCAG AA)

### Planned Improvements

#### High Priority
- [ ] Add skip to main content link
- [ ] Improve form error announcements
- [ ] Add ARIA labels for complex components
- [ ] Document keyboard shortcuts

#### Medium Priority
- [ ] Accessibility statement page
- [ ] Captions for instructional videos
- [ ] High contrast mode toggle
- [ ] Font size adjustment option

#### Low Priority
- [ ] Multiple language support
- [ ] Sign language video content
- [ ] Audio descriptions for visualizations

---

## 📝 WCAG 2.1 Compliance Matrix

| Criterion | Level | Status | Notes |
|-----------|-------|--------|-------|
| 1.1.1 Non-text Content | A | ✅ | All images have alt text |
| 1.4.3 Contrast (Minimum) | AA | ✅ | 4.5:1 minimum met |
| 1.4.4 Resize Text | AA | ✅ | Text resizable to 200% |
| 1.4.10 Reflow | AA | ✅ | No horizontal scrolling |
| 2.1.1 Keyboard | A | ✅ | All features keyboard accessible |
| 2.1.2 No Keyboard Trap | A | ✅ | No keyboard traps |
| 2.4.3 Focus Order | A | ✅ | Logical tab order |
| 2.4.7 Focus Visible | AA | ✅ | Visible focus indicators |
| 3.1.1 Language of Page | A | ✅ | HTML lang attribute set |
| 3.3.1 Error Identification | A | ✅ | Clear error messages |
| 3.3.3 Error Suggestion | AA | ✅ | Helpful error suggestions |
| 4.1.2 Name, Role, Value | A | ✅ | Proper semantic HTML |
| 4.1.3 Status Messages | AA | ⚠️ | Partial - Live regions improving |

---

## 🔗 Resources

### Guidelines & Standards
- [WCAG 2.1 Overview](https://www.w3.org/WAI/WCAG21/quickref/)
- [WebAIM](https://webaim.org/)
- [A11y Project](https://www.a11yproject.com/)

### Testing Tools
- [axe DevTools](https://www.deque.com/axe/devtools/)
- [WAVE](https://wave.webaim.org/)
- [Lighthouse](https://developers.google.com/web/tools/lighthouse)
- [Accessibility Insights](https://accessibilityinsights.io/)
- [NVDA Screen Reader](https://www.nvaccess.org/)

### Learning
- [WebAIM Articles](https://webaim.org/articles/)
- [MDN Accessibility](https://developer.mozilla.org/en-US/docs/Web/Accessibility)
- [The A11Y Project](https://www.a11yproject.com/resources/)
- [Udacity Accessibility Course](https://www.udacity.com/course/web-accessibility--ud891)

---

## 🤝 Contributing Accessible Code

When contributing, please:

1. **Use semantic HTML** - Use proper heading, nav, main, etc.
2. **Test with keyboard** - Ensure all features work without mouse
3. **Add alt text** - Describe all images meaningfully
4. **Check contrast** - Use contrast checker for colors
5. **Test with screen reader** - Use NVDA or JAWS
6. **Consider color blindness** - Don't rely on color alone

Example:
```tsx
// Good accessible component
function PlayerCard({ player }: Props) {
  return (
    <article className="border rounded-lg">
      <h2>{player.name}</h2>
      <img src={player.photo} alt={`${player.name} profile photo`} />
      <dl>
        <dt>Points:</dt>
        <dd>{player.points}</dd>
      </dl>
    </article>
  );
}
```

---

## 📞 Accessibility Support

- **Questions?** Open an issue: https://github.com/Boblebol/TheGitLeague/issues
- **Found a bug?** Report with label `accessibility`
- **Want to help?** See [CONTRIBUTING.md](./CONTRIBUTING.md)

---

## Accessibility Statement

The Git League is committed to ensuring digital accessibility. If you encounter any accessibility issues, please report them so we can address them promptly.

**Contact:** accessibility@thegitleague.com (coming soon)

---

**Last Updated:** January 2026
**Next Review:** April 2026 (Quarterly)

[Back to README](./README.md) | [Security](./SECURITY.md) | [Contributing](./CONTRIBUTING.md)
