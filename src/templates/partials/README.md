# Universal Navigation System

## Overview
The ForgeData application now uses a universal navigation component that ensures consistent navigation across all pages.

## Structure

### Navigation Component
- **Location**: `src/templates/partials/nav.html`
- **Type**: Jinja2 template partial
- **Purpose**: Provides consistent navigation UI and links across all pages

### Features
- Unified branding (logo and app name)
- Version display
- Consistent link styling
- Active page highlighting
- Responsive design with Tailwind CSS

## Usage

### In Templates
To include the navigation in any template:

```html
</head>
<body class="bg-gray-50">
    {% set active_page = 'page_name' %}
    {% include 'partials/nav.html' %}
    
    <!-- Your page content -->
```

### Active Page Values
Set `active_page` to one of these values to highlight the current page:
- `'home'` - Home/Dashboard page
- `'etl'` - ETL Management page
- `'visualizations'` - Data Visualizations page
- `'configuration'` - Configuration page

### Example
```html
{% set active_page = 'etl' %}
{% include 'partials/nav.html' %}
```

## Navigation Links

The universal navigation includes these links:

| Link | URL | Icon | Description |
|------|-----|------|-------------|
| Home | `/` | 🏠 | Main dashboard |
| ETL | `/etl` | 🔄 | ETL pipeline management |
| Visualizations | `/visualizations` | 📊 | Data visualization tools |
| Configuration | `/configuration` | ⚙️ | System configuration |
| API Docs | `/api/docs` | 📚 | Interactive API documentation |

## Styling

The navigation uses Tailwind CSS classes:
- **Active state**: `bg-gray-100` background
- **Hover state**: `hover:text-gray-900`
- **API Docs**: Special styling with blue background (`bg-blue-50`)

## Current Implementation

All templates now use the universal navigation:
- ✅ `index.html` (active_page: 'home')
- ✅ `etl.html` (active_page: 'etl')
- ✅ `visualizations.html` (active_page: 'visualizations')
- ✅ `configuration.html` (active_page: 'configuration')

## Benefits

1. **Consistency**: All pages have identical navigation structure
2. **Maintainability**: Updates to navigation only need to be made in one file
3. **Branding**: Consistent logo and brand identity across all pages
4. **User Experience**: Users always know where they are and how to navigate
5. **Active State**: Current page is visually highlighted

## Customization

To customize the navigation:

1. Edit `src/templates/partials/nav.html`
2. Changes will automatically apply to all pages
3. No need to update each template individually

### Adding New Links
Add new navigation items in the main navigation div:

```html
<a href="/new-page" 
   class="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium {{ 'bg-gray-100' if active_page == 'new-page' else '' }}">
    🆕 New Page
</a>
```

### Changing Logo
Update the logo path in `nav.html`:
```html
<img src="/static/your-logo.png" alt="Your Logo" class="h-8 w-auto mr-3">
```

## Technical Notes

- Uses Jinja2 template inheritance
- Conditionally applies active state using Jinja2 template variables
- Fully responsive design
- Compatible with all modern browsers
- No JavaScript required for basic functionality
