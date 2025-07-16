# 🎨 AVA OLO Design System Guidelines

## Overview
This document defines the complete design system for AVA OLO monitoring dashboards. All UI components should follow these guidelines to ensure consistency across the platform.

## 🎯 Design Principles

1. **Agricultural Focus** - Design reflects farming and agricultural themes
2. **Clarity First** - Information should be immediately understandable
3. **Professional & Modern** - Clean, contemporary design with subtle gradients
4. **Responsive** - Works seamlessly across all device sizes
5. **Accessible** - High contrast, clear typography, keyboard navigation

## 🎨 Color System

### Primary Colors
- **Purple Gradient**: `#667eea` → `#764ba2` (Main brand gradient)
- **Primary**: `#667eea` (Interactive elements)
- **Agricultural Green**: `#2c5530` (Headers, titles)

### Status Colors
| Status | Primary | Light | Dark | Background |
|--------|---------|-------|------|------------|
| Success | `#16a34a` | `#22c55e` | `#15803d` | `#f0fdf4` |
| Warning | `#f59e0b` | `#fbbf24` | `#d97706` | `#fffbeb` |
| Danger | `#dc2626` | `#ef4444` | `#b91c1c` | `#fef2f2` |
| Info | `#3b82f6` | `#60a5fa` | `#2563eb` | `#eff6ff` |

### Neutral Colors
- Gray scale from `#f9fafb` (50) to `#111827` (900)
- Text: `#333333` (primary), `#666666` (secondary)
- Borders: `#e5e7eb` (light), `#d1d5db` (medium)

### Special Purpose
- Purple Accent: `#8b5cf6` (Special actions)
- Blue Accent: `#1a73e8` (Primary CTAs)

## 📐 Typography

### Font Stack
```css
font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
```

### Font Sizes
- `xs`: 0.75rem (12px) - Small labels
- `sm`: 0.875rem (14px) - Secondary text
- `base`: 1rem (16px) - Body text
- `lg`: 1.125rem (18px) - Emphasized text
- `xl`: 1.25rem (20px) - Section headers
- `2xl`: 1.5rem (24px) - Page titles
- `3xl`: 1.875rem (30px) - Dashboard headers
- `4xl`: 2.25rem (36px) - Hero text

### Font Weights
- Normal: 400
- Medium: 500
- Semibold: 600
- Bold: 700

## 📏 Spacing System

Use consistent spacing scale:
- `1`: 0.25rem (4px)
- `2`: 0.5rem (8px)
- `3`: 0.75rem (12px)
- `4`: 1rem (16px)
- `5`: 1.25rem (20px)
- `6`: 1.5rem (24px)
- `8`: 2rem (32px)
- `10`: 2.5rem (40px)
- `12`: 3rem (48px)

## 🔲 Border Radius

- Small: 4px (tags, badges)
- Base: 8px (inputs, small buttons)
- Medium: 10px (buttons)
- Large: 12px (cards)
- XL: 16px (modals)
- 2XL: 20px (main containers)

## 🎭 Shadows

### Elevation Levels
```css
/* Level 1 - Subtle */
box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);

/* Level 2 - Cards */
box-shadow: 0 8px 12px rgba(0, 0, 0, 0.08);

/* Level 3 - Dropdowns */
box-shadow: 0 12px 24px rgba(0, 0, 0, 0.1);

/* Level 4 - Modals */
box-shadow: 0 20px 40px rgba(0, 0, 0, 0.12);

/* Level 5 - Popovers */
box-shadow: 0 25px 50px rgba(0, 0, 0, 0.15);
```

### Colored Shadows
- Primary: `0 4px 15px rgba(102, 126, 234, 0.3)`
- Success: `0 4px 12px rgba(22, 163, 74, 0.3)`
- Warning: `0 4px 12px rgba(245, 158, 11, 0.3)`
- Danger: `0 4px 12px rgba(220, 38, 38, 0.3)`

## 🎬 Animations

### Transitions
- Fast: 150ms ease
- Base: 300ms ease
- Slow: 500ms ease

### Standard Animations
```css
/* Hover lift */
transform: translateY(-2px);
box-shadow: 0 6px 20px rgba(0, 0, 0, 0.1);

/* Focus ring */
box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);

/* Loading pulse */
animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
```

## 🧱 Component Patterns

### Buttons
```css
/* Primary Button */
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
padding: 0.75rem 1.5rem;
border-radius: 10px;
font-weight: 600;
transition: all 0.3s ease;
box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);

/* Hover State */
transform: translateY(-2px);
box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
```

### Cards
```css
background: white;
border-radius: 12px;
padding: 1.5rem;
box-shadow: 0 8px 12px rgba(0, 0, 0, 0.08);
transition: all 0.3s ease;
```

### Inputs
```css
padding: 0.75rem;
border: 2px solid #e5e7eb;
border-radius: 8px;
transition: all 0.3s ease;

/* Focus State */
border-color: #667eea;
box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
```

### Modals
```css
background: white;
border-radius: 20px;
padding: 2.5rem;
box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2);
animation: slideInUp 0.3s ease;
```

## 📱 Responsive Design

### Breakpoints
- Mobile: < 640px
- Tablet: < 768px
- Desktop: < 1024px
- Large: < 1280px
- XL: >= 1280px

### Mobile Adjustments
- Reduce base font size to 14px
- Decrease spacing by 25%
- Stack horizontal layouts vertically
- Simplify navigation

## ♿ Accessibility

### Focus States
- All interactive elements must have visible focus indicators
- Use 3px focus ring with primary color at 10% opacity
- Ensure 3:1 contrast ratio for focus indicators

### Color Contrast
- Normal text: 4.5:1 minimum
- Large text: 3:1 minimum
- Interactive elements: 3:1 minimum

### Keyboard Navigation
- All features accessible via keyboard
- Logical tab order
- Escape key closes modals
- Enter/Space activate buttons

## 🔄 State Definitions

### Loading States
- Use skeleton screens for content loading
- Pulse animation for active processes
- Spinner for actions in progress

### Disabled States
- 50% opacity
- No hover effects
- Cursor: not-allowed

### Empty States
- Centered content
- Helpful message
- Action button when applicable
- Icon or illustration

### Error States
- Red border/background
- Clear error message
- Suggested action

## 🚀 Implementation

### Using the Design System

1. **Import the CSS file**:
```html
<link rel="stylesheet" href="/static/css/design-system.css">
```

2. **Use CSS variables**:
```css
.my-button {
  background: var(--color-primary);
  padding: var(--spacing-3) var(--spacing-6);
  border-radius: var(--radius-md);
  transition: all var(--transition-base);
}
```

3. **Apply utility classes**:
```html
<button class="gradient-primary hover-lift">Click Me</button>
```

### Updating the Design System

To change any aspect of the design:

1. Edit `/static/css/design-system.css`
2. Update the CSS variable values
3. All dashboards using the variables will automatically update

Example:
```css
/* Change primary color */
--color-primary: #新颜色;

/* Change all spacing */
--spacing-4: 1.5rem; /* was 1rem */
```

## 📋 Checklist for New Components

- [ ] Uses design system colors via CSS variables
- [ ] Follows spacing scale
- [ ] Has proper hover states
- [ ] Has focus states for accessibility
- [ ] Includes loading state if async
- [ ] Has error state handling
- [ ] Responsive on all screen sizes
- [ ] Follows animation guidelines
- [ ] Matches border radius standards
- [ ] Uses appropriate shadow levels

## 🔍 Examples

### Well-Designed Button
```css
.cta-button {
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-dark) 100%);
  color: white;
  padding: var(--spacing-3) var(--spacing-6);
  border-radius: var(--radius-md);
  font-weight: var(--font-weight-semibold);
  transition: all var(--transition-base);
  box-shadow: var(--shadow-primary);
}

.cta-button:hover {
  transform: var(--transform-hover-up);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
}
```

### Status Badge
```css
.status-badge {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-2);
  padding: var(--spacing-1) var(--spacing-3);
  border-radius: var(--radius-full);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
}

.status-badge.success {
  background: var(--color-success-bg);
  color: var(--color-success-dark);
  border: 1px solid var(--color-success);
}
```

---

**Remember**: Consistency is key! When in doubt, refer to this guide or check existing implementations in the main dashboard.