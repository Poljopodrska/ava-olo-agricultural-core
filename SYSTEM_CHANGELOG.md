# AVA OLO System Changelog

## [v2.5.0-constitutional] - 2025-07-20

### Added - Constitutional Design System Implementation

#### Design System
- Created comprehensive constitutional design rules documentation
- Implemented AVA OLO brand identity with atomic/molecular logo structure
- Created logo variations (white and dark) in SVG format
- Established brand color palette:
  - Primary: Black (#1a1a1a), White (#ffffff), Olive Green (#6B7D46)
  - Secondary: Earth tones for agricultural theme
- Implemented typography system with 18px minimum font size for farmer accessibility
- Created reusable CSS design system with:
  - Core design tokens (colors, spacing, typography)
  - Component styles (buttons, forms, cards, headers)
  - Responsive utilities
- Added universal Enter key handler for all form inputs
- Implemented accessibility features:
  - Skip navigation links
  - Enhanced focus indicators
  - ARIA label improvements
  - Minimum font size enforcement

#### Service Updates
- **Agricultural Core Service** (`agricultural_core_constitutional.py`):
  - Integrated constitutional design system
  - Added real-time database connection for farmer statistics
  - Implemented business dashboard with dynamic metrics
  - Added monitoring and database dashboard pages
  - Version display on all pages (top right)
  
- **Monitoring API Service** (`monitoring_api_constitutional.py`):
  - Integrated constitutional design system
  - Updated to use correct database table names (`farmers` not `ava_farmers`)
  - Added real-time monitoring dashboard
  - Maintained development database endpoints with security
  - Version display on all pages

#### Infrastructure
- Created Dockerfiles for both services with constitutional design
- Prepared for ECS deployment with design system assets
- Configured static file serving for shared design resources

### Fixed
- Corrected database table references (using `farmers` instead of `ava_farmers`)
- Fixed hardcoded "16 farmers" issue - now shows real database count (4 farmers)

### Technical Details
- Design system location: `/shared/design-system/`
- CSS framework: Custom constitutional design tokens
- JavaScript: Vanilla JS for maximum compatibility
- Font: Inter (with fallbacks)
- Minimum font size: 18px (constitutional requirement)
- Mobile breakpoint: 768px
- Version format: vX.X.X displayed top-right on all pages

### Mango Test Status
✅ **PASSED**: Bulgarian mango farmer can instantly recognize AVA OLO brand across:
- Business dashboard
- Monitoring dashboards  
- All internal tools
- Consistent olive green branding
- Professional agricultural appearance
- Clear 18px+ text for older farmers

### Deployment Notes
- Agricultural Core: Port 8080 (ECS)
- Monitoring API: Port 8080 (ECS)
- Both services include full design system
- Static assets served from `/shared/` mount

### Migration Guide
1. Deploy new Docker images to ECS
2. Update ALB routing to new services
3. Verify design system assets are accessible
4. Test Enter key functionality on all forms
5. Verify version display on all pages

---

## [Previous Versions]

### [v2.4.0] - Previous Release
- Multi-dashboard implementation
- Basic business metrics
- No unified design system