# Tomo UI Style Guide

This document outlines the visual design system for the Tomo application.

## Brand Colors

### Primary - Tomo Purple

The primary color is derived from the Tomo logo (`assets/tomo_logo_minimal.png`).

| Token | HSL | Usage |
|-------|-----|-------|
| `--primary` | `250 76% 72%` | Default purple |
| `--primary-hover` | `250 76% 62%` | Darker (for filled backgrounds) |
| `--primary-bright` | `250 76% 82%` | Brighter variant |
| `--primary-foreground` | `0 0% 100%` | Text on filled purple |
| Text hover | `250 85% 80%` | Brighter text on hover (hardcoded) |

### Single Source of Truth

**All colors are defined in ONE place:** `frontend/src/styles/theme.css`

Both Tailwind CSS and MUI theme read from these CSS variables:
- `frontend/src/styles/theme.css` - CSS variable definitions
- `frontend/src/theme/muiTheme.ts` - MUI theme (uses same HSL values)

**Never hardcode colors** - always reference the CSS variables or use the same HSL values.

## Buttons

### Primary Button (Outline Style)

Primary buttons use an **outline style** to match the logo aesthetic.

**CSS Class:** `btn-primary-outline`

| State | Style |
|-------|-------|
| Default | Purple border + Purple text (`250 76% 72%`) |
| Hover | Border unchanged + Text brightens (`250 85% 80%`) |
| Disabled | 50% opacity |

**Implementation:**
```tsx
import { Button } from '@/components/ui/Button'

<Button variant="primary">Sign In</Button>
```

**Tailwind Classes Applied:**
```
border-2 border-primary bg-transparent text-primary
```

### Button Variants

| Variant | Style | Use Case |
|---------|-------|----------|
| `primary` | Purple outline | Main actions (Sign In, Add, Save) |
| `outline` | Gray border | Secondary actions (Cancel, Export) |
| `ghost` | No border/bg | Tertiary actions (Refresh) |
| `destructive` | Red filled | Dangerous actions (Delete, Purge) |
| `secondary` | Gray filled | Alternative actions |

### Button Sizes

| Size | Class | Height |
|------|-------|--------|
| `sm` | `h-8 px-3 text-xs` | 32px |
| `md` | `h-10 px-4 text-sm` | 40px |
| `lg` | `h-12 px-6 text-base` | 48px |
| `icon` | `h-9 w-9 p-0` | 36px square |

## Links

### Primary Link

Links that should match the brand purple use the `link-primary` class.

**CSS Class:** `link-primary`

| State | Style |
|-------|-------|
| Default | Purple text (`250 76% 72%`) |
| Hover | Brightens (`250 85% 80%`) |

**No underline** - links rely on color change for hover feedback.

**Implementation:**
```tsx
import Link from '@mui/material/Link'

<Link
  component={RouterLink}
  to="/forgot-password"
  underline="none"
  className="link-primary"
>
  Forgot Password?
</Link>
```

### CSS Definition

```css
/* frontend/src/styles/components/buttons.css */

/* Primary outline button hover - brighten text only */
.btn-primary-outline:hover {
  color: hsl(250 85% 80%);
}

/* Primary link with hover brighten effect */
.link-primary {
  color: hsl(var(--primary)) !important;
  text-decoration: none !important;
  transition: color 0.15s ease;
}

.link-primary:hover {
  color: hsl(250 85% 80%) !important;
  text-decoration: none !important;
}
```

## Checkboxes

Checkboxes use an **outline style** to match the overall design language.

| State | Style |
|-------|-------|
| Unchecked | Purple outline box (`250 76% 72%`) |
| Checked | Purple outline box + purple checkmark (no fill) |
| Hover | No background change |

**Key rules:**
- No filled background when checked
- No ripple effect (`disableRipple`)
- No hover background change
- Border and checkmark use the same purple (`250 76% 72%`)

**Implementation:**
```tsx
<Checkbox
  size="small"
  disableRipple
  sx={{
    '&:hover': { backgroundColor: 'transparent' }
  }}
  icon={<span style={{
    width: 16,
    height: 16,
    border: '2px solid hsl(250 76% 72%)',
    borderRadius: 3
  }} />}
  checkedIcon={<span style={{
    width: 16,
    height: 16,
    border: '2px solid hsl(250 76% 72%)',
    borderRadius: 3,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    color: 'hsl(250 76% 72%)',
    fontSize: 14,
    fontWeight: 'bold'
  }}>✓</span>}
/>
```

## Icon Buttons

Icon buttons (like the password visibility toggle) use the brand purple with the same hover behavior as links.

| State | Style |
|-------|-------|
| Default | Purple outlined icon (`250 76% 72%`) |
| Hover | Brightens (`250 85% 80%`) + No background |

**Key rules:**
- Use **outlined** icon variants (e.g., `VisibilityOutlined`, not `Visibility`)
- No filled icons - outline only to match the design language
- No ripple effect (`disableRipple`)
- No hover background (`backgroundColor: 'transparent'`)
- Icon color brightens on hover, matching link behavior

**Implementation:**
```tsx
import { VisibilityOutlined, VisibilityOffOutlined } from '@mui/icons-material'

<IconButton
  disableRipple
  sx={{
    color: 'hsl(250 76% 72%)',
    '&:hover': {
      backgroundColor: 'transparent',
      color: 'hsl(250 85% 80%)'
    }
  }}
>
  <VisibilityOutlined />
</IconButton>
```

## Logo

### Logo File

**Location:** `tomo/assets/tomo_logo_minimal.png`

The logo uses the same purple color (`#8B7CF6`) as the brand.

### Usage in Components

```tsx
// Import from the shared assets folder
import TomoLogo from '../../../../assets/tomo_logo_minimal.png'

// Or with alias (if configured)
import TomoLogo from '@assets/tomo_logo_minimal.png'
```

### Logo Locations

| Page | Component |
|------|-----------|
| Header/Sidebar | `Header.tsx` |
| Login | `LoginPage.tsx` |
| Registration | `RegistrationPage.tsx` |
| Forgot Password | `ForgotPasswordPage.tsx` |
| Setup | `SetupPage.tsx` |

## File Structure

```
frontend/src/styles/
├── theme.css              # Color variables (light/dark)
├── globals.css            # Global styles, imports
└── components/
    ├── buttons.css        # Button & link styles
    ├── cards.css
    ├── forms.css
    └── ...

frontend/src/components/ui/
└── Button.tsx             # Button component

tomo/assets/
└── tomo_logo_minimal.png  # Brand logo
```

## Dark Mode

All colors automatically adapt to dark mode via CSS variables in `theme.css`.

The primary purple remains consistent across both modes:
- Light mode: `#8B7CF6`
- Dark mode: `#8B7CF6`

## Design Principles

1. **Outline over filled** - Primary buttons use outline style to match the logo
2. **Subtle hover** - Hover effects brighten text rather than filling backgrounds
3. **No underlines** - Links use color change for hover feedback
4. **Consistent purple** - All primary interactive elements use the brand purple
5. **Minimal transitions** - 0.15s ease transitions for hover states
