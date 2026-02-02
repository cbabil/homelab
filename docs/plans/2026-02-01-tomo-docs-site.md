# Tomo Documentation Site

**Date:** 2026-02-01
**Status:** Approved
**Location:** `~/source/tomo`

## Overview

Create a documentation website for Tomo. The site will showcase the application and provide user documentation.

## Technology Stack

- **Framework:** VitePress (Vue-powered static site generator)
- **Hosting:** Vercel (automatic deployments from GitHub)
- **Features:** Dark/light mode, built-in search, responsive design

## Content Structure

### Homepage (Showcase)
- Hero section with tagline
- Feature highlights with icons
- Screenshots/demo images
- Quick links to get started

### Documentation Sections

```
├── Guide
│   ├── Introduction
│   ├── Getting Started
│   ├── Installation
│   └── Configuration
├── Servers
│   ├── Adding Servers
│   ├── Health Monitoring
│   ├── Provisioning
│   └── Troubleshooting
├── Applications
│   ├── Marketplace Overview
│   ├── Deploying Apps
│   ├── Managing Containers
│   ├── Custom Repositories
│   └── Creating Custom Apps
├── Dashboard & Monitoring
│   ├── Understanding Metrics
│   ├── Activity Logs
│   └── Performance Tips
├── Administration
│   ├── User Management
│   ├── Sessions & Permissions
│   ├── Backup & Recovery
│   └── Data Retention
├── CLI
│   ├── Installation
│   ├── Commands Reference
│   └── Examples
└── Reference
    └── Common Issues
```

## Project Structure

```
~/source/tomo/
├── .vitepress/
│   ├── config.ts           # Main configuration
│   └── theme/
│       ├── index.ts        # Theme customization
│       └── style.css       # Custom styles
├── public/
│   ├── logo.svg            # Site logo
│   └── screenshots/        # App screenshots
├── index.md                # Homepage (showcase)
├── guide/
├── servers/
├── applications/
├── dashboard/
├── administration/
├── cli/
├── reference/
├── package.json
├── vercel.json             # Vercel configuration
├── .gitignore
└── README.md
```

## Implementation Phases

### Phase 1: Project Scaffolding
- Create `~/source/tomo` directory
- Initialize package.json with VitePress
- Create basic VitePress config
- Set up folder structure
- Add `.gitignore` and `vercel.json`
- Initialize git repository

### Phase 2: Theme & Branding
- Configure site title, description, logo
- Set up navigation (top nav + sidebars)
- Customize colors to match tomo project
- Verify dark/light mode toggle works

### Phase 3: Homepage (Showcase)
- Create hero section with tagline
- Add feature cards highlighting key capabilities
- Include placeholder for screenshots
- Add "Get Started" call-to-action

### Phase 4: Documentation Structure
- Create all section folders and index files
- Set up sidebar navigation for each section
- Add placeholder content for each page
- Configure cross-linking between pages

### Phase 5: Content Migration
- Pull relevant content from existing `docs/` in tomo project
- Adapt technical docs to user-friendly format
- Add missing user guides

### Phase 6: Vercel Deployment
- Create GitHub repository
- Connect repository to Vercel
- Verify automatic deployments work
- Test preview URLs

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Content takes time to write | Start with structure, fill content incrementally |
| Screenshots need updating | Use placeholder images initially |
| Name might change | Easy to update in config later |

## Notes

- VitePress auto-detects by Vercel, minimal config needed
- Build command: `vitepress build`
- Output directory: `.vitepress/dist`
