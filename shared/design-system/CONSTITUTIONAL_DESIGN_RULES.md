# AVA OLO Constitutional Design Rules

## Brand Identity
AVA OLO represents the intersection of scientific precision and agricultural tradition. Our design system reflects professionalism, trustworthiness, and accessibility for Croatian farmers.

## Core Principles

### 1. Accessibility First
- **Minimum Font Size**: 18px for all text (farmer accessibility)
- **Touch Targets**: Minimum 44x44px for mobile
- **Color Contrast**: WCAG AA compliance minimum
- **Enter Key**: Must work on ALL input fields

### 2. Brand Colors
```css
/* Primary Palette */
--ava-black: #1a1a1a;        /* Primary background */
--ava-white: #ffffff;        /* Primary text on dark */
--ava-olive: #6B7D46;        /* Primary accent (from jacket) */
--ava-olive-dark: #4a5632;   /* Hover states */

/* Secondary Palette */
--ava-brown: #8B4513;        /* Earth tone accent */
--ava-soil: #654321;         /* Dark earth */
--ava-wheat: #F5DEB3;        /* Light accent */
--ava-leaf: #7CB342;         /* Success/growth */
```

### 3. Typography
```css
/* Font Stack */
--font-primary: 'Inter', 'Segoe UI', Arial, sans-serif;
--font-mono: 'Courier New', monospace;

/* Font Sizes */
--font-size-min: 18px;       /* Absolute minimum */
--font-size-body: 20px;      /* Standard body text */
--font-size-heading-3: 24px; /* Small headings */
--font-size-heading-2: 28px; /* Section headings */
--font-size-heading-1: 36px; /* Page titles */

/* Font Weights */
--font-weight-normal: 400;
--font-weight-medium: 500;
--font-weight-bold: 700;
```

### 4. Spacing System
```css
/* 8px base unit */
--space-xs: 4px;
--space-sm: 8px;
--space-md: 16px;
--space-lg: 32px;
--space-xl: 48px;
--space-xxl: 64px;
```

### 5. Component Standards

#### Headers
- Black background with white logo and text
- Height: 64px desktop, 56px mobile
- Logo: 40px height desktop, 30px mobile
- Version display: Top right, always visible

#### Buttons
```css
/* Primary Button */
background: var(--ava-olive);
color: var(--ava-white);
padding: 12px 24px;
font-size: var(--font-size-body);
border-radius: 8px;
min-height: 48px;

/* Hover */
background: var(--ava-olive-dark);
```

#### Forms
```css
/* Input Fields */
font-size: var(--font-size-min);
padding: 16px;
border: 2px solid #e0e0e0;
border-radius: 8px;
min-height: 56px;

/* Focus */
border-color: var(--ava-olive);
outline: 3px solid rgba(107, 125, 70, 0.2);
```

#### Cards
```css
background: var(--ava-white);
border-radius: 12px;
padding: 24px;
box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
```

### 6. Logo Usage
- **Placement**: Always top left in header
- **Clear Space**: Minimum 16px on all sides
- **Versions**: 
  - White for dark backgrounds
  - Dark for light backgrounds
- **Minimum Size**: 120px width

### 7. Mobile Responsiveness
```css
/* Breakpoints */
--mobile: 320px;
--tablet: 768px;
--desktop: 1024px;
--wide: 1440px;

/* Mobile Adjustments */
@media (max-width: 768px) {
  /* Maintain readability */
  --font-size-body: 18px;
  --font-size-heading-2: 24px;
  --font-size-heading-1: 28px;
}
```

### 8. Version Display
- Position: Fixed, top right
- Format: "v{major}.{minor}.{patch}"
- Style: 14px, medium weight, olive color
- Always visible on all pages

### 9. Accessibility Requirements
- All interactive elements keyboard accessible
- Focus indicators clearly visible
- ARIA labels for icon-only buttons
- Skip navigation links
- Proper heading hierarchy

### 10. Agricultural Theme Elements
- Earth tone color usage in data visualizations
- Agricultural icons (wheat, leaf, sun, water)
- Natural imagery with proper contrast
- Professional yet approachable tone

## Implementation Checklist
- [ ] Logo implemented (SVG format)
- [ ] Color variables defined
- [ ] Typography system applied
- [ ] All text ≥ 18px
- [ ] Enter key functionality
- [ ] Mobile responsive
- [ ] Version display
- [ ] Accessibility tested
- [ ] Brand consistency verified

## Mango Test
"A Bulgarian mango farmer instantly recognizes AVA OLO's professional agricultural brand across all touchpoints."