# Marketplace User Guide

## Overview

The Marketplace is a Git-based app discovery system that lets you browse, import, and rate applications from community repositories. Think of it like an app store for your tomo - you can subscribe to official and community repositories, discover new apps, and import them into your local catalog for deployment.

## Concepts

### App Repositories

Repositories are Git-based sources containing YAML app definitions:

| Type | Description |
|------|-------------|
| **Official** | Curated apps maintained by the tomo team |
| **Community** | Third-party repositories from the community |
| **Personal** | Your own forked or custom repositories |

### App Definitions

Apps are defined in YAML files within repositories:

```yaml
# apps/pihole/app.yaml
id: pihole
name: Pi-hole
description: Network-wide ad blocking via your own DNS server
version: "2024.07.0"
category: networking
author: Pi-hole Project
license: EUPL-1.2
repository: https://github.com/pi-hole/pi-hole

docker:
  image: pihole/pihole:latest
  ports:
    - host: 53
      container: 53
      protocol: tcp
    - host: 80
      container: 80
      protocol: tcp
  volumes:
    - host: /opt/pihole/etc
      container: /etc/pihole
    - host: /opt/pihole/dnsmasq
      container: /etc/dnsmasq.d
  environment:
    - name: TZ
      default: UTC
    - name: WEBPASSWORD
      required: true
      secret: true

requirements:
  min_ram: 512MB
  min_storage: 1GB
  architectures:
    - amd64
    - arm64
```

### Local Catalog vs Marketplace

- **Marketplace**: External repositories you can browse and import from
- **Local Catalog**: Apps imported into your tomo, ready to deploy

## Managing Repositories

### Adding a Repository

1. Navigate to **Settings** > **Marketplace**
2. Click **Add Repository**
3. Enter repository details:
   - **Name**: Display name for the repo
   - **URL**: Git repository URL (HTTPS or SSH)
   - **Branch**: Branch to sync (default: `main`)
   - **Type**: Official, Community, or Personal
4. Click **Add**
5. Repository syncs automatically

### Syncing Repositories

Repositories sync automatically on a schedule. To manually sync:

1. Go to **Settings** > **Marketplace**
2. Find the repository
3. Click **Sync Now**

Sync process:
1. Git pull latest changes
2. Parse all YAML app definitions
3. Update local metadata index
4. Report new/updated/removed apps

### Removing a Repository

1. Go to **Settings** > **Marketplace**
2. Find the repository
3. Click **Remove**

**Note:** Removing a repository does not remove apps already imported to your local catalog.

## Discovering Apps

### Browse by Category

Categories organize apps by function:

- **Networking** - DNS, VPN, reverse proxy
- **Media** - Streaming, photos, music
- **Automation** - Home automation, workflows
- **Monitoring** - Metrics, logging, dashboards
- **Storage** - File sync, backup, NAS
- **Development** - CI/CD, code hosting
- **Security** - Authentication, secrets management

### Featured Apps

Curated apps highlighted by the tomo team appear in the **Featured** section.

### Trending Apps

Apps ranked by:
- Recent imports across all users
- Star ratings
- Update activity

### Search

Search apps by:
- Name
- Description
- Tags
- Author

### Filters

Filter results by:
- Category
- Repository source
- Minimum rating
- Architecture compatibility

## Importing Apps

### Import Single App

1. Find an app in the marketplace
2. Click **Import to Catalog**
3. App is added to your local catalog
4. Ready to deploy from **Applications** page

### Bulk Import

1. Select multiple apps using checkboxes
2. Click **Import Selected**
3. All selected apps added to catalog

## Rating Apps

Rate apps to help the community discover quality software.

### Star Ratings

- Click stars (1-5) on any app
- Ratings stored locally
- Aggregate ratings shared with community (optional)

### Rating Guidelines

- **5 stars**: Works perfectly, well documented
- **4 stars**: Works well with minor issues
- **3 stars**: Functional but needs improvement
- **2 stars**: Significant issues
- **1 star**: Does not work or security concerns

## Submitting Apps

### Via Pull Request

1. Fork the official or community repository
2. Create app YAML in `apps/<app-name>/app.yaml`
3. Add icon to `apps/<app-name>/icon.png`
4. Submit pull request

### Via YAML Upload

1. Go to **Marketplace** > **Submit App**
2. Upload your `app.yaml` file
3. Provide repository URL for review
4. Submit for approval

### App Submission Requirements

- Valid YAML syntax
- Required fields: id, name, description, version, category, docker.image
- Working Docker image
- No security vulnerabilities
- Clear documentation

## Architecture

### Repository Sync Flow

```
Git Repository (GitHub/GitLab)
       │
       ▼
  Git Clone/Pull
       │
       ▼
  Parse YAML Files
       │
       ▼
  Update SQLite Index
       │
       ▼
  Available in Marketplace UI
```

### Import Flow

```
Marketplace App
       │
       ▼
  Click "Import"
       │
       ▼
  Copy to Local Catalog
       │
       ▼
  Available in Applications Page
       │
       ▼
  Ready to Deploy
```

## MCP Tools Reference

| Tool | Description |
|------|-------------|
| `list_marketplace_repos` | List configured repositories |
| `add_marketplace_repo` | Add a new repository |
| `remove_marketplace_repo` | Remove a repository |
| `sync_marketplace_repo` | Manually sync a repository |
| `search_marketplace` | Search marketplace apps |
| `import_app` | Import app to local catalog |
| `rate_app` | Set star rating for an app |
| `get_trending_apps` | Get trending apps list |
| `get_featured_apps` | Get featured apps list |

## Troubleshooting

### Repository won't sync

- Check Git URL is correct and accessible
- Verify branch name exists
- Check network connectivity
- Look for sync error message in Settings

### App import fails

- Verify YAML syntax is valid
- Check all required fields present
- Ensure Docker image exists and is accessible

### Ratings not saving

- Check you're logged in
- Verify app exists in catalog
- Check browser console for errors

## Best Practices

1. **Verify sources** - Only add repositories you trust
2. **Check ratings** - Look at community ratings before importing
3. **Review YAML** - Inspect app definitions before deploying
4. **Keep synced** - Regularly sync repos for updates
5. **Contribute back** - Rate apps and submit improvements
