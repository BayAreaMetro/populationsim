# GitHub Pages Setup Instructions

This directory contains the GitHub Pages documentation site for TM2 PopulationSim.

## Site Structure

```
docs/
├── _config.yml              # Jekyll configuration
├── index.md                 # Home page
├── getting-started/         # Setup and running guides
│   ├── index.md
│   ├── environment-setup.md
│   └── how-to-run.md
├── process/                 # Process overview docs
│   ├── index.md
│   ├── overview.md
│   └── file-flow.md
├── guides/                  # Component guides
│   ├── index.md
│   ├── geo-crosswalk.md
│   ├── seed-population.md
│   ├── control-generation.md
│   ├── population-synthesis.md
│   ├── income.md
│   └── group-quarters.md
├── outputs/                 # Output documentation
│   ├── index.md
│   ├── input-fields.md
│   ├── summaries.md
│   └── taz-summaries.md
├── reference/               # Detailed technical docs
│   ├── index.md
│   ├── TM2_FULL_REFERENCE.md
│   ├── DETAILED_OUTPUT_GUIDE.md
│   ├── DETAILED_SYNTHESIS_GUIDE.md
│   ├── DETAILED_INPUT_DATA_GUIDE.md
│   ├── DETAILED_CROSSWALK_GUIDE.md
│   └── DETAILED_CONTROL_GENERATION_GUIDE.md
├── images/                  # Images and diagrams
└── visualizations/          # Visualization outputs
```

## Enabling GitHub Pages

### Option 1: GitHub Web Interface

1. Go to repository Settings → Pages
2. Under "Build and deployment":
   - Source: Deploy from a branch
   - Branch: `tm2`
   - Folder: `/docs`
3. Click Save
4. Site will be published at: `https://bayareametro.github.io/populationsim/`

### Option 2: Using GitHub CLI

```bash
# Enable GitHub Pages from docs folder on tm2 branch
gh repo edit --enable-pages --pages-branch tm2 --pages-path /docs
```

## Local Testing

To test the site locally before publishing:

### Install Jekyll

```bash
# macOS/Linux
gem install bundler jekyll

# Windows (use RubyInstaller)
# Download from: https://rubyinstaller.org/
# Then run:
gem install bundler jekyll
```

### Create Gemfile

Create a `Gemfile` in the `docs/` directory:

```ruby
source "https://rubygems.org"

gem "github-pages", group: :jekyll_plugins
gem "jekyll-theme-cayman"
```

### Run Local Server

```bash
cd docs
bundle install
bundle exec jekyll serve
```

Then open: `http://localhost:4000/populationsim/`

## Customization

### Theme

The site uses the Cayman theme. To change:

1. Edit `_config.yml`
2. Change `theme:` to another [supported theme](https://pages.github.com/themes/)

### Navigation

Navigation structure is defined in:
- `_config.yml` - Top-level navigation
- Each section's `index.md` - Section navigation

### Styling

Custom CSS can be added by creating:
- `assets/css/style.scss`

### Layouts

Custom layouts can be added in:
- `_layouts/default.html` (overrides theme default)

## Adding New Pages

### 1. Create Markdown File

```markdown
---
layout: default
title: Page Title
parent: Section Name
nav_order: 1
---

# Page Content

Your content here...
```

### 2. Update Section Index

Add link to the section's `index.md` file.

### 3. Add Cross-Links

Link to related pages using relative paths:
```markdown
[Related Page](../other-section/page.html)
```

## Cross-Linking Strategy

All pages include:
- Navigation breadcrumbs (via YAML frontmatter)
- "Related Documentation" section at bottom
- Contextual inline links to related topics
- Back-to-home links

## Maintenance

### Updating Documentation

1. Edit files in `bay_area/docs/` (source files)
2. Copy updated files to `docs/` structure
3. Update cross-links as needed
4. Commit and push to `tm2` branch
5. GitHub Pages auto-rebuilds

### Checking Links

Use a link checker to find broken links:
```bash
bundle exec jekyll build
bundle exec htmlproofer ./_site --disable-external
```

## URL Structure

- Home: `/populationsim/`
- Getting Started: `/populationsim/getting-started/`
- Process: `/populationsim/process/`
- Guides: `/populationsim/guides/`
- Outputs: `/populationsim/outputs/`
- Reference: `/populationsim/reference/`

## Troubleshooting

### "Page not found" errors

- Check `baseurl` in `_config.yml` matches repo name
- Verify file paths are correct
- Ensure files have `.md` or `.html` extension

### Broken links

- Use relative paths: `../section/page.html`
- Don't use absolute paths starting with `/`
- Remember: markdown files become `.html` in URLs

### Theme not loading

- Verify theme name in `_config.yml`
- Check theme is [supported by GitHub Pages](https://pages.github.com/themes/)
- Try clearing browser cache

### Changes not appearing

- Wait 1-2 minutes for GitHub Pages to rebuild
- Check Actions tab for build errors
- Force refresh browser (Ctrl+F5)

## Resources

- [GitHub Pages Documentation](https://docs.github.com/en/pages)
- [Jekyll Documentation](https://jekyllrb.com/docs/)
- [Supported Themes](https://pages.github.com/themes/)
- [GitHub Pages Troubleshooting](https://docs.github.com/en/pages/setting-up-a-github-pages-site-with-jekyll/troubleshooting-jekyll-build-errors-for-github-pages-sites)
