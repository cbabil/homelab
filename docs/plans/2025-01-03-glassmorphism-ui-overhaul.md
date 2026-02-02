# Modern Glassmorphism UI Overhaul Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Transform the flat, static UI into a modern 2025 glassmorphic design with smooth animations, hover effects, and visual depth.

**Architecture:** Update CSS custom properties and Tailwind config to enable glass effects, re-enable all animations, add micro-interactions to all interactive elements. No React component structure changes needed - purely styling updates.

**Tech Stack:** TailwindCSS, CSS Custom Properties, CSS Keyframe Animations, backdrop-filter

---

## Phase 1: Foundation (Tasks 1-5)

### Task 1: Extend Tailwind Configuration

**Files:**
- Modify: `frontend/tailwind.config.js`

**Step 1: Add animation and blur extensions to Tailwind config**

```javascript
/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ["class"],
  content: [
    './pages/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './app/**/*.{ts,tsx}',
    './src/**/*.{ts,tsx}',
  ],
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: {
        "2xl": "1400px",
      },
    },
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      keyframes: {
        "fade-in": {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        "fade-out": {
          "0%": { opacity: "1" },
          "100%": { opacity: "0" },
        },
        "slide-up": {
          "0%": { opacity: "0", transform: "translateY(10px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "slide-down": {
          "0%": { opacity: "0", transform: "translateY(-10px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "scale-in": {
          "0%": { opacity: "0", transform: "scale(0.95)" },
          "100%": { opacity: "1", transform: "scale(1)" },
        },
        "pulse-glow": {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.7" },
        },
        "shimmer": {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
        "spin": {
          "0%": { transform: "rotate(0deg)" },
          "100%": { transform: "rotate(360deg)" },
        },
      },
      animation: {
        "fade-in": "fade-in 0.2s ease-out",
        "fade-out": "fade-out 0.2s ease-in",
        "slide-up": "slide-up 0.3s ease-out",
        "slide-down": "slide-down 0.3s ease-out",
        "scale-in": "scale-in 0.2s ease-out",
        "pulse-glow": "pulse-glow 2s ease-in-out infinite",
        "shimmer": "shimmer 2s linear infinite",
        "spin": "spin 1s linear infinite",
      },
      boxShadow: {
        "glass": "0 4px 30px rgba(0, 0, 0, 0.1)",
        "glass-lg": "0 8px 32px rgba(0, 0, 0, 0.12)",
        "glow": "0 0 20px hsl(var(--primary) / 0.3)",
        "glow-lg": "0 0 40px hsl(var(--primary) / 0.4)",
        "inner-glow": "inset 0 1px 0 0 rgba(255, 255, 255, 0.1)",
      },
      backdropBlur: {
        xs: "2px",
      },
    },
  },
  plugins: [],
}
```

**Step 2: Verify the config is valid**

Run: `cd frontend && yarn build 2>&1 | head -20`
Expected: No Tailwind config errors

**Step 3: Commit**

```bash
git add frontend/tailwind.config.js
git commit -m "feat(ui): extend tailwind config with animations and glass effects"
```

---

### Task 2: Add Glass Theme Variables

**Files:**
- Modify: `frontend/src/styles/theme.css`

**Step 1: Add glass-specific CSS variables to both light and dark themes**

Replace the entire file with:

```css
/**
 * Theme Variables and Design Tokens
 *
 * Centralized theme configuration including colors, spacing, animations, and design tokens.
 * This file contains all CSS custom properties for light and dark themes.
 */

@layer base {
  :root {
    /* Base colors */
    --background: 0 0% 100%;
    --foreground: 240 10% 3.9%;
    --card: 0 0% 100%;
    --card-foreground: 240 10% 3.9%;
    --popover: 0 0% 100%;
    --popover-foreground: 240 10% 3.9%;

    /* Primary colors - Professional Purple #8b5cf6 */
    --primary: 258 90% 66%;
    --primary-foreground: 0 0% 98%;

    /* Secondary colors - Purple-tinted grays */
    --secondary: 270 5% 96%;
    --secondary-foreground: 270 15% 15%;

    /* Muted colors */
    --muted: 270 5% 96%;
    --muted-foreground: 270 5% 45%;

    /* Accent colors */
    --accent: 270 10% 94%;
    --accent-foreground: 270 15% 15%;

    /* Status colors */
    --destructive: 0 84.2% 60.2%;
    --destructive-foreground: 0 0% 98%;
    --success: 142.1 76.2% 36.3%;
    --success-foreground: 355.7 100% 97.3%;
    --warning: 32.1 94.6% 43.7%;
    --warning-foreground: 313.4 96.2% 2.9%;

    /* UI elements */
    --border: 270 10% 90%;
    --input: 270 10% 90%;
    --ring: 258 90% 66%;
    --radius: 0.75rem;

    /* Purple gradient variables - #8b5cf6 */
    --purple-gradient-from: 258 90% 66%;
    --purple-gradient-to: 258 90% 66%;
    --purple-glow: 258 90% 76%;

    /* Glass effect variables - Light mode */
    --glass-bg: 0 0% 100% / 0.7;
    --glass-border: 0 0% 100% / 0.3;
    --glass-shadow: 0 0% 0% / 0.05;
    --glass-blur: 12px;
    --glass-highlight: 0 0% 100% / 0.5;
  }

  .dark {
    /* Base colors - Blue-tinted dark theme (projecthub style) */
    /* #0f172a background */
    --background: 222 47% 11%;
    --foreground: 214 32% 91%;
    /* Slightly lighter surface for cards */
    --card: 217 33% 14%;
    --card-foreground: 214 32% 91%;
    --popover: 217 33% 14%;
    --popover-foreground: 214 32% 91%;

    /* Primary colors - Indigo/Purple #6a5acd / #4f46e5 */
    --primary: 243 75% 59%;
    --primary-foreground: 0 0% 100%;

    /* Secondary colors */
    --secondary: 215 28% 17%;
    --secondary-foreground: 214 32% 91%;

    /* Muted colors */
    --muted: 215 28% 17%;
    --muted-foreground: 215 20% 65%;

    /* Accent colors */
    --accent: 217 33% 20%;
    --accent-foreground: 214 32% 91%;

    /* Status colors */
    --destructive: 0 84% 60%;
    --destructive-foreground: 0 0% 98%;
    --success: 152 69% 40%;
    --success-foreground: 0 0% 100%;
    --warning: 38 92% 50%;
    --warning-foreground: 0 0% 0%;

    /* UI elements */
    --border: 215 28% 20%;
    --input: 215 28% 20%;
    --ring: 243 75% 59%;

    /* Gradient variables */
    --purple-gradient-from: 243 75% 59%;
    --purple-gradient-to: 248 53% 58%;
    --purple-glow: 228 89% 63%;

    /* Glass effect variables - Dark mode */
    --glass-bg: 217 33% 14% / 0.8;
    --glass-border: 215 28% 30% / 0.3;
    --glass-shadow: 0 0% 0% / 0.3;
    --glass-blur: 16px;
    --glass-highlight: 215 28% 40% / 0.1;
  }
}
```

**Step 2: Commit**

```bash
git add frontend/src/styles/theme.css
git commit -m "feat(ui): add glass effect CSS variables for light and dark modes"
```

---

### Task 3: Re-enable Animations in Globals

**Files:**
- Modify: `frontend/src/styles/globals.css`

**Step 1: Replace the globals.css with animations enabled**

Replace the entire file with:

```css
/* Import theme variables and design tokens */
@import './theme.css';

/* Import generic component styles */
@import './components/buttons.css';
@import './components/cards.css';
@import './components/forms.css';
@import './components/tables.css';
@import './components/navigation.css';
@import './components/dialogs.css';
@import './components/badges.css';

@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  * {
    @apply border-border;
  }

  body {
    @apply bg-background text-foreground;
    font-feature-settings: "rlig" 1, "calt" 1;
  }

  html {
    scroll-behavior: smooth;
  }

  /* Custom scrollbar styles */
  .scrollbar-thin {
    scrollbar-width: thin;
    scrollbar-color: transparent transparent;
  }

  .scrollbar-thin:hover {
    scrollbar-color: hsl(var(--border)) transparent;
  }

  .scrollbar-thin::-webkit-scrollbar {
    width: 4px;
    height: 4px;
  }

  .scrollbar-thin::-webkit-scrollbar-track {
    background: transparent;
  }

  .scrollbar-thin::-webkit-scrollbar-thumb {
    background: transparent;
    border-radius: 2px;
  }

  .scrollbar-thin:hover::-webkit-scrollbar-thumb {
    background: hsl(var(--border) / 0.3);
  }

  .scrollbar-thin::-webkit-scrollbar-thumb:hover {
    background: hsl(var(--border) / 0.5);
  }
}

@layer components {
  /* Glassmorphism base class */
  .glass {
    background: hsl(var(--glass-bg));
    backdrop-filter: blur(var(--glass-blur));
    -webkit-backdrop-filter: blur(var(--glass-blur));
    border: 1px solid hsl(var(--glass-border));
    box-shadow:
      0 4px 30px hsl(var(--glass-shadow)),
      inset 0 1px 0 0 hsl(var(--glass-highlight));
  }

  /* Glass card variant */
  .glass-card {
    @apply glass rounded-xl;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  }

  .glass-card:hover {
    transform: translateY(-2px);
    box-shadow:
      0 8px 40px hsl(var(--glass-shadow)),
      inset 0 1px 0 0 hsl(var(--glass-highlight)),
      0 0 20px hsl(var(--primary) / 0.1);
  }

  /* Card hover effect */
  .card-hover {
    @apply transition-all duration-300 ease-out;
  }

  .card-hover:hover {
    @apply shadow-lg -translate-y-0.5;
    border-color: hsl(var(--primary) / 0.3);
  }

  /* Gradient button */
  .btn-gradient {
    @apply bg-primary text-white;
    background: linear-gradient(
      135deg,
      hsl(var(--primary)) 0%,
      hsl(var(--primary) / 0.8) 100%
    );
    transition: all 0.2s ease-out;
  }

  .btn-gradient:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px hsl(var(--primary) / 0.4);
  }

  .btn-gradient:active {
    transform: translateY(0);
  }

  /* Enhanced purple button variant */
  .btn-purple {
    @apply bg-primary text-white relative overflow-hidden;
    transition: all 0.2s ease-out;
  }

  .btn-purple:hover {
    box-shadow: 0 0 20px hsl(var(--primary) / 0.5);
  }

  /* Purple header gradient with glass effect */
  .header-gradient {
    background: linear-gradient(
      135deg,
      hsl(var(--background)) 0%,
      hsl(var(--primary) / 0.05) 100%
    );
    backdrop-filter: blur(8px);
    -webkit-backdrop-filter: blur(8px);
    @apply border-b border-primary/10;
  }

  /* Loading animation */
  .loading-pulse {
    @apply animate-pulse;
  }

  /* Status indicators with glow */
  .status-online {
    @apply bg-green-500;
    box-shadow: 0 0 12px rgba(34, 197, 94, 0.5);
    animation: pulse-glow 2s ease-in-out infinite;
  }

  .status-offline {
    @apply bg-red-500;
    box-shadow: 0 0 12px rgba(239, 68, 68, 0.5);
  }

  /* Professional navigation active state */
  .nav-active {
    @apply bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100;
    @apply border-l-4 border-l-primary shadow-sm;
    background: linear-gradient(
      90deg,
      hsl(var(--primary) / 0.1) 0%,
      transparent 100%
    );
  }

  /* Skeleton loader with shimmer */
  .skeleton {
    @apply bg-muted rounded;
    background: linear-gradient(
      90deg,
      hsl(var(--muted)) 0%,
      hsl(var(--muted-foreground) / 0.1) 50%,
      hsl(var(--muted)) 100%
    );
    background-size: 200% 100%;
    animation: shimmer 1.5s ease-in-out infinite;
  }

  /* Glow effect for interactive elements */
  .glow-on-hover {
    @apply transition-shadow duration-300;
  }

  .glow-on-hover:hover {
    box-shadow: 0 0 20px hsl(var(--primary) / 0.3);
  }
}

@layer utilities {
  /* Animation utilities */
  .animate-fade-in {
    animation: fade-in 0.2s ease-out forwards;
  }

  .animate-slide-up {
    animation: slide-up 0.3s ease-out forwards;
  }

  .animate-scale-in {
    animation: scale-in 0.2s ease-out forwards;
  }

  .animate-spin-slow {
    animation: spin 2s linear infinite;
  }

  /* Text utilities */
  .line-clamp-2 {
    overflow: hidden;
    display: -webkit-box;
    -webkit-box-orient: vertical;
    -webkit-line-clamp: 2;
  }

  /* Transition utilities */
  .transition-gpu {
    transform: translateZ(0);
    will-change: transform;
  }
}

/* Keyframe animations */
@keyframes fade-in {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slide-up {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes scale-in {
  from {
    opacity: 0;
    transform: scale(0.95);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

@keyframes pulse-glow {
  0%, 100% {
    opacity: 1;
    box-shadow: 0 0 12px currentColor;
  }
  50% {
    opacity: 0.7;
    box-shadow: 0 0 20px currentColor;
  }
}

@keyframes shimmer {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
```

**Step 2: Verify styles compile**

Run: `cd frontend && yarn build 2>&1 | head -20`
Expected: No CSS errors

**Step 3: Commit**

```bash
git add frontend/src/styles/globals.css
git commit -m "feat(ui): re-enable animations and add glassmorphism utilities"
```

---

### Task 4: Update Card Styles with Glass Effect

**Files:**
- Modify: `frontend/src/styles/components/cards.css`

**Step 1: Update cards.css with glass variants and hover effects**

Replace the entire file with:

```css
/**
 * Card Components
 *
 * Generic card styles for all card-based components including app cards, server cards,
 * dashboard status cards, and settings cards. Includes glass effect variants.
 */

/* Base card styles with subtle glass effect */
.card-base {
  @apply bg-card rounded-xl border;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

/* Glass card variant */
.card-glass {
  background: hsl(var(--glass-bg));
  backdrop-filter: blur(var(--glass-blur));
  -webkit-backdrop-filter: blur(var(--glass-blur));
  border: 1px solid hsl(var(--glass-border));
  box-shadow:
    0 4px 30px hsl(var(--glass-shadow)),
    inset 0 1px 0 0 hsl(var(--glass-highlight));
  @apply rounded-xl;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.card-glass:hover {
  transform: translateY(-2px);
  box-shadow:
    0 8px 40px hsl(var(--glass-shadow)),
    inset 0 1px 0 0 hsl(var(--glass-highlight)),
    0 0 20px hsl(var(--primary) / 0.1);
}

/* Card with hover effects */
.card-hover {
  @apply card-base;
}

.card-hover:hover {
  @apply shadow-lg -translate-y-0.5;
  border-color: hsl(var(--primary) / 0.3);
}

/* Card padding variants */
.card-sm {
  @apply p-3;
}

.card-md {
  @apply p-4;
}

.card-lg {
  @apply p-6;
}

/* Card layouts */
.card-flex-col {
  @apply flex flex-col h-full;
}

.card-grid {
  @apply grid gap-4;
}

/* App card specific styles */
.card-app {
  @apply card-base p-3 flex flex-col relative;
  height: 160px;
}

.card-app:hover {
  @apply border-primary/50 shadow-md -translate-y-0.5;
}

.card-app-header {
  @apply flex items-start justify-between gap-2 mb-2;
}

.card-app-icon-wrapper {
  @apply p-1.5 rounded-lg shrink-0;
  background: hsl(var(--primary) / 0.1);
  transition: all 0.2s ease-out;
}

.card-app:hover .card-app-icon-wrapper {
  background: hsl(var(--primary) / 0.15);
  box-shadow: 0 0 12px hsl(var(--primary) / 0.2);
}

.card-app-icon {
  @apply h-4 w-4;
}

.card-app-content {
  @apply flex items-start space-x-2 min-w-0 flex-1;
}

.card-app-info {
  @apply space-y-0.5 min-w-0 flex-1;
}

.card-app-title {
  @apply font-semibold text-sm leading-tight truncate;
}

.card-app-description {
  @apply text-xs text-muted-foreground line-clamp-2 overflow-hidden;
}

.card-app-meta {
  @apply flex items-center justify-between text-xs text-muted-foreground;
}

.card-app-stats {
  @apply flex items-center space-x-2;
}

.card-app-stat {
  @apply flex items-center space-x-0.5;
}

.card-app-version {
  @apply px-1.5 py-0.5 rounded bg-accent text-xs font-medium;
  transition: all 0.2s ease-out;
}

.card-app:hover .card-app-version {
  background: hsl(var(--primary) / 0.15);
  color: hsl(var(--primary));
}

.card-app-tags {
  @apply flex flex-wrap gap-1;
}

.card-app-actions {
  @apply flex items-center space-x-1.5 pt-2;
}

/* Server card specific styles */
.card-server {
  @apply card-base p-6 h-full flex flex-col;
}

.card-server:hover {
  @apply shadow-lg -translate-y-0.5;
  border-color: hsl(var(--primary) / 0.3);
}

.card-server-header {
  @apply flex items-start justify-between mb-4;
}

.card-server-info {
  @apply flex-1;
}

.card-server-title-row {
  @apply flex items-center space-x-3 mb-2;
}

.card-server-title {
  @apply text-lg font-semibold;
}

.card-server-connection {
  @apply text-sm text-muted-foreground;
}

.card-server-actions {
  @apply flex items-center space-x-1;
}

.card-server-system-info {
  @apply flex-1 space-y-3;
}

.card-server-system-grid {
  @apply grid grid-cols-2 gap-3 text-sm;
}

.card-server-system-item {
  /* Use with nested spans for label and value */
}

.card-server-system-label {
  @apply text-muted-foreground;
}

.card-server-system-value {
  @apply font-medium;
}

.card-server-footer {
  @apply pt-4 mt-auto border-t border-border/50;
}

.card-server-footer-meta {
  @apply flex items-center justify-between text-xs text-muted-foreground;
}

/* Dashboard status card styles with glass effect */
.card-status {
  background: hsl(var(--glass-bg));
  backdrop-filter: blur(var(--glass-blur));
  -webkit-backdrop-filter: blur(var(--glass-blur));
  border: 1px solid hsl(var(--glass-border));
  box-shadow:
    0 4px 30px hsl(var(--glass-shadow)),
    inset 0 1px 0 0 hsl(var(--glass-highlight));
  @apply p-6 rounded-xl;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.card-status:hover {
  transform: translateY(-2px);
  box-shadow:
    0 8px 40px hsl(var(--glass-shadow)),
    inset 0 1px 0 0 hsl(var(--glass-highlight)),
    0 0 20px hsl(var(--primary) / 0.1);
}

.card-status-header {
  @apply flex items-center justify-between mb-4;
}

.card-status-icon-wrapper {
  @apply p-2.5 rounded-xl;
  background: hsl(var(--primary) / 0.1);
  transition: all 0.3s ease-out;
}

.card-status:hover .card-status-icon-wrapper {
  background: hsl(var(--primary) / 0.15);
  box-shadow: 0 0 20px hsl(var(--primary) / 0.2);
}

.card-status-icon {
  @apply w-5 h-5;
}

.card-status-content {
  @apply space-y-1;
}

.card-status-value {
  @apply text-3xl font-bold;
}

.card-status-label {
  @apply text-sm text-muted-foreground;
}

/* Settings card styles */
.card-setting {
  @apply card-base rounded-lg border p-3;
}

.card-setting:hover {
  @apply shadow-sm;
  border-color: hsl(var(--border) / 0.8);
}

.card-setting-header {
  @apply text-sm font-semibold mb-3 text-primary;
}

.card-setting-content {
  @apply space-y-0;
}

/* Large feature cards (Dashboard Quick Actions, System Health) */
.card-feature {
  background: hsl(var(--glass-bg));
  backdrop-filter: blur(var(--glass-blur));
  -webkit-backdrop-filter: blur(var(--glass-blur));
  border: 1px solid hsl(var(--glass-border));
  box-shadow:
    0 4px 30px hsl(var(--glass-shadow)),
    inset 0 1px 0 0 hsl(var(--glass-highlight));
  @apply p-6 rounded-xl;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.card-feature-header {
  @apply flex items-center space-x-3 mb-6;
}

.card-feature-icon-wrapper {
  @apply p-2.5 rounded-xl;
  background: hsl(var(--primary) / 0.1);
}

.card-feature-icon {
  @apply w-5 h-5;
}

.card-feature-title {
  @apply text-xl font-semibold;
}

.card-feature-content {
  @apply space-y-3;
}

/* System health specific card */
.card-health-status {
  @apply flex items-center justify-between p-3 rounded-lg;
  background: hsl(var(--accent) / 0.5);
  transition: all 0.2s ease-out;
}

.card-health-status:hover {
  background: hsl(var(--accent) / 0.7);
}

.card-health-status-label {
  @apply text-sm font-medium;
}

.card-health-status-indicator {
  @apply flex items-center space-x-2;
}

.card-health-status-dot {
  @apply w-2 h-2 rounded-full;
}

.card-health-status-text {
  @apply text-sm capitalize;
}

/* Loading card skeleton with shimmer */
.card-loading {
  @apply card-base p-6 rounded-xl border;
}

.card-loading-content {
  @apply space-y-3;
}

.card-loading-icon {
  @apply w-12 h-12 rounded-lg;
  background: linear-gradient(
    90deg,
    hsl(var(--muted)) 0%,
    hsl(var(--muted-foreground) / 0.1) 50%,
    hsl(var(--muted)) 100%
  );
  background-size: 200% 100%;
  animation: shimmer 1.5s ease-in-out infinite;
}

.card-loading-title {
  @apply h-6 rounded w-20;
  background: linear-gradient(
    90deg,
    hsl(var(--muted)) 0%,
    hsl(var(--muted-foreground) / 0.1) 50%,
    hsl(var(--muted)) 100%
  );
  background-size: 200% 100%;
  animation: shimmer 1.5s ease-in-out infinite;
}

.card-loading-description {
  @apply h-4 rounded w-32;
  background: linear-gradient(
    90deg,
    hsl(var(--muted)) 0%,
    hsl(var(--muted-foreground) / 0.1) 50%,
    hsl(var(--muted)) 100%
  );
  background-size: 200% 100%;
  animation: shimmer 1.5s ease-in-out infinite;
  animation-delay: 0.1s;
}

/* Dialog card styles */
.card-dialog {
  @apply card-base p-6 rounded-xl border max-w-md w-full mx-4 max-h-[90vh] overflow-y-auto;
  box-shadow: 0 25px 50px -12px hsl(var(--glass-shadow));
}

.card-dialog-header {
  @apply flex items-center justify-between mb-6;
}

.card-dialog-title {
  @apply text-xl font-semibold;
}

.card-dialog-content {
  @apply space-y-4;
}

/* Table card wrapper */
.card-table {
  @apply card-base rounded-lg border p-0 overflow-hidden;
}

.card-table-header {
  @apply p-3 border-b border-border;
}

.card-table-title {
  @apply text-sm font-semibold text-primary;
}

.card-table-content {
  @apply overflow-x-auto;
}

/* Shimmer keyframe for this file scope */
@keyframes shimmer {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}
```

**Step 2: Commit**

```bash
git add frontend/src/styles/components/cards.css
git commit -m "feat(ui): add glass effect to cards with hover animations"
```

---

### Task 5: Update Button Styles with Micro-interactions

**Files:**
- Modify: `frontend/src/styles/components/buttons.css`

**Step 1: Add hover/active states and transitions to buttons**

Find and replace the `.btn-base` class (around line 9-12):

**Before:**
```css
.btn-base {
  @apply inline-flex items-center justify-center gap-2 rounded-lg font-medium;
  @apply focus:outline-none disabled:opacity-50 disabled:pointer-events-none;
  @apply transition-all duration-200;
}
```

**After:**
```css
.btn-base {
  @apply inline-flex items-center justify-center gap-2 rounded-lg font-medium;
  @apply focus:outline-none focus:ring-2 focus:ring-primary/20 focus:ring-offset-2;
  @apply disabled:opacity-50 disabled:pointer-events-none;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  transform: translateZ(0);
}

.btn-base:hover:not(:disabled) {
  transform: translateY(-1px);
}

.btn-base:active:not(:disabled) {
  transform: translateY(0) scale(0.98);
}
```

**Step 2: Update .btn-primary class (around line 29-31)**

**Before:**
```css
.btn-primary {
  @apply btn-base bg-primary text-white hover:opacity-90;
}
```

**After:**
```css
.btn-primary {
  @apply btn-base bg-primary text-white;
}

.btn-primary:hover:not(:disabled) {
  box-shadow: 0 4px 12px hsl(var(--primary) / 0.4);
}
```

**Step 3: Update .btn-quick-action class (around line 129-131)**

**Before:**
```css
.btn-quick-action {
  @apply w-full text-left p-3 rounded-lg hover:bg-accent transition-colors duration-200;
}
```

**After:**
```css
.btn-quick-action {
  @apply w-full text-left p-3 rounded-lg;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.btn-quick-action:hover {
  @apply bg-accent;
  transform: translateX(4px);
}
```

**Step 4: Commit**

```bash
git add frontend/src/styles/components/buttons.css
git commit -m "feat(ui): add micro-interactions to buttons"
```

---

## Phase 2: Components (Tasks 6-9)

### Task 6: Update Dialog Styles with Glass Effect

**Files:**
- Modify: `frontend/src/styles/components/dialogs.css`

**Step 1: Update the dialog backdrop and container (lines 9-21)**

**Before:**
```css
/* Dialog backdrop/overlay */
.dialog-backdrop {
  @apply fixed inset-0 bg-black/50 flex items-center justify-center z-50;
}

.dialog-backdrop-blur {
  @apply backdrop-blur-sm;
}

/* Dialog container */
.dialog-container {
  @apply bg-background rounded-xl border shadow-xl;
  @apply max-w-md w-full mx-4 max-h-[90vh] overflow-y-auto;
}
```

**After:**
```css
/* Dialog backdrop/overlay with blur */
.dialog-backdrop {
  @apply fixed inset-0 flex items-center justify-center z-50;
  background: hsl(0 0% 0% / 0.5);
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
  animation: fade-in 0.2s ease-out;
}

.dialog-backdrop-blur {
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
}

/* Dialog container with glass effect */
.dialog-container {
  background: hsl(var(--glass-bg));
  backdrop-filter: blur(var(--glass-blur));
  -webkit-backdrop-filter: blur(var(--glass-blur));
  border: 1px solid hsl(var(--glass-border));
  box-shadow:
    0 25px 50px -12px hsl(var(--glass-shadow)),
    inset 0 1px 0 0 hsl(var(--glass-highlight));
  @apply rounded-xl max-w-md w-full mx-4 max-h-[90vh] overflow-y-auto;
  animation: scale-in 0.2s ease-out;
}

@keyframes fade-in {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes scale-in {
  from { opacity: 0; transform: scale(0.95); }
  to { opacity: 1; transform: scale(1); }
}
```

**Step 2: Update .dialog-toast class (around line 276-279)**

**Before:**
```css
.dialog-toast {
  @apply fixed top-4 right-4 z-50 max-w-sm;
  @apply bg-background border rounded-lg shadow-lg p-4;
}
```

**After:**
```css
.dialog-toast {
  @apply fixed top-4 right-4 z-50 max-w-sm rounded-lg p-4;
  background: hsl(var(--glass-bg));
  backdrop-filter: blur(var(--glass-blur));
  -webkit-backdrop-filter: blur(var(--glass-blur));
  border: 1px solid hsl(var(--glass-border));
  box-shadow: 0 8px 32px hsl(var(--glass-shadow));
  animation: slide-down 0.3s ease-out;
}

@keyframes slide-down {
  from { opacity: 0; transform: translateY(-10px); }
  to { opacity: 1; transform: translateY(0); }
}
```

**Step 3: Commit**

```bash
git add frontend/src/styles/components/dialogs.css
git commit -m "feat(ui): add glass effect to dialogs and modals"
```

---

### Task 7: Update Navigation with Glass Header

**Files:**
- Modify: `frontend/src/styles/components/navigation.css`

**Step 1: Update the nav-active class (lines 8-12)**

**Before:**
```css
.nav-active {
  @apply bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 border-l-4 border-l-primary;
  @apply shadow-sm;
}
```

**After:**
```css
.nav-active {
  @apply text-foreground border-l-4 border-l-primary;
  background: linear-gradient(
    90deg,
    hsl(var(--primary) / 0.15) 0%,
    hsl(var(--primary) / 0.05) 50%,
    transparent 100%
  );
  box-shadow:
    0 1px 3px hsl(var(--glass-shadow)),
    inset 0 1px 0 0 hsl(var(--glass-highlight));
}
```

**Step 2: Update .nav-dropdown-content class (around line 132-134)**

**Before:**
```css
.nav-dropdown-content {
  @apply absolute top-full left-0 mt-1 bg-background border border-border rounded-md shadow-lg min-w-48 z-50;
}
```

**After:**
```css
.nav-dropdown-content {
  @apply absolute top-full left-0 mt-1 rounded-lg min-w-48 z-50;
  background: hsl(var(--glass-bg));
  backdrop-filter: blur(var(--glass-blur));
  -webkit-backdrop-filter: blur(var(--glass-blur));
  border: 1px solid hsl(var(--glass-border));
  box-shadow: 0 8px 32px hsl(var(--glass-shadow));
  animation: fade-in 0.15s ease-out;
}

@keyframes fade-in {
  from { opacity: 0; transform: translateY(-4px); }
  to { opacity: 1; transform: translateY(0); }
}
```

**Step 3: Commit**

```bash
git add frontend/src/styles/components/navigation.css
git commit -m "feat(ui): add glass effect to navigation dropdowns"
```

---

### Task 8: Create Skeleton Loader Component

**Files:**
- Create: `frontend/src/components/ui/Skeleton.tsx`

**Step 1: Create the skeleton component**

```tsx
import { cn } from '@/utils/cn'

interface SkeletonProps {
  className?: string
  variant?: 'text' | 'circular' | 'rectangular'
  width?: string | number
  height?: string | number
  animation?: 'pulse' | 'shimmer' | 'none'
}

export function Skeleton({
  className,
  variant = 'rectangular',
  width,
  height,
  animation = 'shimmer',
}: SkeletonProps) {
  const baseClasses = 'bg-muted rounded'

  const variantClasses = {
    text: 'h-4 w-full rounded',
    circular: 'rounded-full',
    rectangular: 'rounded-lg',
  }

  const animationClasses = {
    pulse: 'animate-pulse',
    shimmer: 'skeleton',
    none: '',
  }

  const style: React.CSSProperties = {}
  if (width) style.width = typeof width === 'number' ? `${width}px` : width
  if (height) style.height = typeof height === 'number' ? `${height}px` : height

  return (
    <div
      className={cn(
        baseClasses,
        variantClasses[variant],
        animationClasses[animation],
        className
      )}
      style={style}
    />
  )
}

export function SkeletonCard() {
  return (
    <div className="card-base p-6 space-y-4">
      <div className="flex items-center space-x-4">
        <Skeleton variant="circular" width={48} height={48} />
        <div className="space-y-2 flex-1">
          <Skeleton height={20} width="60%" />
          <Skeleton height={16} width="40%" />
        </div>
      </div>
      <Skeleton height={16} />
      <Skeleton height={16} width="80%" />
    </div>
  )
}

export function SkeletonStats() {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      {[...Array(4)].map((_, i) => (
        <div key={i} className="card-status p-6 space-y-3">
          <div className="flex items-center justify-between">
            <Skeleton variant="circular" width={40} height={40} />
            <Skeleton width={24} height={24} />
          </div>
          <Skeleton height={32} width="50%" />
          <Skeleton height={16} width="70%" />
        </div>
      ))}
    </div>
  )
}
```

**Step 2: Export from index (if exists) or verify import works**

Run: `ls frontend/src/components/ui/`

**Step 3: Commit**

```bash
git add frontend/src/components/ui/Skeleton.tsx
git commit -m "feat(ui): add Skeleton loader component with shimmer animation"
```

---

### Task 9: Update Toast Component with Glass Effect

**Files:**
- Modify: `frontend/src/components/ui/Toast.tsx`

**Step 1: Read current Toast component**

Run: `head -100 frontend/src/components/ui/Toast.tsx`

**Step 2: Update the toast container styles**

Find the main toast container div and update its className to include glass effect:

Look for something like:
```tsx
className="... bg-background border ..."
```

Replace with:
```tsx
className="... glass-card ..."
```

Or if using inline styles, add:
```tsx
className={cn(
  "fixed top-4 right-4 z-50 max-w-sm rounded-lg p-4",
  "bg-[hsl(var(--glass-bg))] backdrop-blur-[var(--glass-blur)]",
  "border border-[hsl(var(--glass-border))]",
  "shadow-[0_8px_32px_hsl(var(--glass-shadow))]",
  "animate-slide-up",
  // ... rest of classes
)}
```

**Step 3: Commit**

```bash
git add frontend/src/components/ui/Toast.tsx
git commit -m "feat(ui): add glass effect to Toast component"
```

---

## Phase 3: Pages (Tasks 10-13)

### Task 10: Update Dashboard Stats Cards

**Files:**
- Modify: `frontend/src/pages/dashboard/DashboardStats.tsx`

**Step 1: Read current component**

Run: `head -80 frontend/src/pages/dashboard/DashboardStats.tsx`

**Step 2: Update card className to use glass effect**

Find the stat card wrapper div and ensure it uses `.card-status` class which now has glass effect.

Look for patterns like:
```tsx
<div className="bg-card rounded-xl border p-6">
```

Update to:
```tsx
<div className="card-status">
```

The `.card-status` class in cards.css now includes the glass effect.

**Step 3: Commit**

```bash
git add frontend/src/pages/dashboard/DashboardStats.tsx
git commit -m "feat(ui): apply glass effect to dashboard stat cards"
```

---

### Task 11: Update Dashboard Resource Usage

**Files:**
- Modify: `frontend/src/pages/dashboard/DashboardResourceUsage.tsx`

**Step 1: Read current component**

Run: `head -100 frontend/src/pages/dashboard/DashboardResourceUsage.tsx`

**Step 2: Update the main card wrapper**

Ensure the component uses `.card-feature` class for the main container:

```tsx
<div className="card-feature">
```

**Step 3: Commit**

```bash
git add frontend/src/pages/dashboard/DashboardResourceUsage.tsx
git commit -m "feat(ui): apply glass effect to resource usage card"
```

---

### Task 12: Update Header Component

**Files:**
- Modify: `frontend/src/components/layout/Header.tsx`

**Step 1: Read current Header**

Run: `head -80 frontend/src/components/layout/Header.tsx`

**Step 2: Update the header element classes**

Find the main `<header>` element and update its className:

**Before (example):**
```tsx
<header className="sticky top-0 z-50 bg-background border-b">
```

**After:**
```tsx
<header className="sticky top-0 z-50 header-gradient">
```

The `.header-gradient` class now includes glass effect with backdrop blur.

**Step 3: Commit**

```bash
git add frontend/src/components/layout/Header.tsx
git commit -m "feat(ui): apply glass effect to header"
```

---

### Task 13: Update App Cards Size

**Files:**
- Modify: `frontend/src/styles/components/cards.css`

**Step 1: Increase app card size for better readability**

Find `.card-app` class and update the height:

**Before:**
```css
.card-app {
  @apply card-base p-3 flex flex-col relative;
  height: 160px;
}
```

**After:**
```css
.card-app {
  @apply card-base p-4 flex flex-col relative;
  height: 180px;
}
```

**Step 2: Update icon size**

Find `.card-app-icon` and update:

**Before:**
```css
.card-app-icon {
  @apply h-4 w-4;
}
```

**After:**
```css
.card-app-icon {
  @apply h-5 w-5;
}
```

**Step 3: Commit**

```bash
git add frontend/src/styles/components/cards.css
git commit -m "feat(ui): increase app card size for better readability"
```

---

## Phase 4: Finishing (Tasks 14-17)

### Task 14: Add Gradient Accents for Dark Mode

**Files:**
- Modify: `frontend/src/styles/theme.css`

**Step 1: Enhance dark mode with subtle gradient accents**

Add these new variables inside the `.dark` block (after `--purple-glow`):

```css
    /* Gradient accent for dark mode */
    --gradient-accent: linear-gradient(
      135deg,
      hsl(243 75% 59% / 0.1) 0%,
      hsl(248 53% 58% / 0.05) 100%
    );

    /* Neon glow for status indicators */
    --neon-green: 0 0 20px rgba(34, 197, 94, 0.6);
    --neon-red: 0 0 20px rgba(239, 68, 68, 0.6);
    --neon-blue: 0 0 20px rgba(59, 130, 246, 0.6);
    --neon-purple: 0 0 20px hsl(243 75% 59% / 0.6);
```

**Step 2: Commit**

```bash
git add frontend/src/styles/theme.css
git commit -m "feat(ui): add gradient accents and neon glow for dark mode"
```

---

### Task 15: Add Empty State Styling

**Files:**
- Modify: `frontend/src/styles/globals.css`

**Step 1: Add empty state utility classes**

Add these at the end of the `@layer components` section (before the closing brace):

```css
  /* Empty state styling */
  .empty-state {
    @apply flex flex-col items-center justify-center py-12 px-4 text-center;
  }

  .empty-state-icon {
    @apply w-16 h-16 mb-4 text-muted-foreground/50;
  }

  .empty-state-title {
    @apply text-lg font-semibold mb-2;
  }

  .empty-state-description {
    @apply text-sm text-muted-foreground max-w-sm;
  }

  .empty-state-action {
    @apply mt-6;
  }

  /* Page transition wrapper */
  .page-enter {
    @apply animate-fade-in;
  }

  /* Content sections with subtle animation */
  .content-section {
    @apply animate-slide-up;
  }

  .content-section:nth-child(2) {
    animation-delay: 0.05s;
  }

  .content-section:nth-child(3) {
    animation-delay: 0.1s;
  }

  .content-section:nth-child(4) {
    animation-delay: 0.15s;
  }
```

**Step 2: Commit**

```bash
git add frontend/src/styles/globals.css
git commit -m "feat(ui): add empty state and page transition utilities"
```

---

### Task 16: Final Consistency Pass

**Files:**
- Modify: `frontend/src/styles/components/badges.css`

**Step 1: Read current badges**

Run: `cat frontend/src/styles/components/badges.css`

**Step 2: Add transitions to badge hover states**

Find any badge classes and ensure they have transitions. Add at the end of the file:

```css
/* Badge transitions */
.badge-base {
  transition: all 0.2s ease-out;
}

.badge-base:hover {
  transform: scale(1.05);
}

/* Status badges with glow */
.badge-success {
  @apply bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400;
}

.badge-success.badge-glow {
  box-shadow: 0 0 12px rgba(34, 197, 94, 0.3);
}

.badge-error {
  @apply bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400;
}

.badge-error.badge-glow {
  box-shadow: 0 0 12px rgba(239, 68, 68, 0.3);
}

.badge-warning {
  @apply bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400;
}

.badge-warning.badge-glow {
  box-shadow: 0 0 12px rgba(234, 179, 8, 0.3);
}
```

**Step 3: Commit**

```bash
git add frontend/src/styles/components/badges.css
git commit -m "feat(ui): add transitions and glow effects to badges"
```

---

### Task 17: Build and Verify

**Files:**
- None (verification only)

**Step 1: Run the build**

Run: `cd frontend && yarn build`

Expected: Build completes successfully with no errors

**Step 2: Run linter**

Run: `cd frontend && yarn lint`

Expected: No linting errors related to CSS

**Step 3: Start dev server and visual check**

Run: `cd frontend && yarn dev`

Expected: Application starts, visual inspection shows:
- Glass effect on cards
- Hover animations working
- Smooth transitions
- Dark mode gradients
- Status indicators with glow

**Step 4: Final commit**

```bash
git add -A
git commit -m "feat(ui): complete glassmorphism UI overhaul

- Re-enabled all animations (fade, slide, scale, shimmer)
- Added glass effect to cards, dialogs, and navigation
- Added micro-interactions to buttons and interactive elements
- Enhanced dark mode with gradient accents and neon glow
- Increased app card size for better readability
- Added skeleton loader component with shimmer
- Added empty state and page transition utilities"
```

---

## Summary

**Total Tasks:** 17
**Estimated Time:** 4-6 hours of focused work

**Key Files Modified:**
1. `frontend/tailwind.config.js` - Animation keyframes and shadows
2. `frontend/src/styles/theme.css` - Glass CSS variables
3. `frontend/src/styles/globals.css` - Animation utilities and glass classes
4. `frontend/src/styles/components/cards.css` - Glass card variants
5. `frontend/src/styles/components/buttons.css` - Button micro-interactions
6. `frontend/src/styles/components/dialogs.css` - Glass modals
7. `frontend/src/styles/components/navigation.css` - Glass navigation
8. `frontend/src/styles/components/badges.css` - Badge transitions
9. `frontend/src/components/ui/Skeleton.tsx` - New skeleton component
10. `frontend/src/components/ui/Toast.tsx` - Glass toast
11. `frontend/src/pages/dashboard/DashboardStats.tsx` - Glass stat cards
12. `frontend/src/pages/dashboard/DashboardResourceUsage.tsx` - Glass feature card
13. `frontend/src/components/layout/Header.tsx` - Glass header

**Visual Changes:**
- Frosted glass cards with backdrop blur
- Smooth hover animations on all cards
- Button press feedback with scale
- Shimmer skeleton loaders
- Glow effects on status indicators
- Dark mode gradient accents
- Page entrance animations
