# AVA OLO Agricultural Core - Testing Checklist v4.7.1

## Feature Testing Checklist

### 1. Authentication & Access
- [ ] Sign in page loads correctly
- [ ] Registration works with WhatsApp number
- [ ] Login redirects to farmer dashboard
- [ ] Logout functionality works
- [ ] Session persistence works

### 2. Language Detection (Task #1 & #2)
- [ ] Dashboard detects language based on farmer's country
- [ ] Slovenian farmers see Slovenian interface
- [ ] Italian farmers see Italian interface
- [ ] Chat responses are in farmer's language
- [ ] All translations display correctly

### 3. Dashboard Layout
- [ ] Three-panel layout displays correctly
- [ ] Weather panel shows location-based data
- [ ] Chat panel shows AVA (not CAVA) branding
- [ ] Farm panel shows fields or empty state

### 4. Field Management (Tasks #7-11)
- [ ] "Add Field" button is visible and clickable
- [ ] Add Field modal opens correctly
- [ ] Field name and area can be entered
- [ ] Crop type dropdown works
- [ ] "Draw Field on Map" button opens map interface
- [ ] Google Maps loads with satellite view
- [ ] Field drawing works (click to add points, double-click to close)
- [ ] Field area is calculated correctly
- [ ] Field saves successfully
- [ ] New fields appear in dashboard
- [ ] Field coordinates are stored in database

### 5. Task Management System (Tasks #12-16)
- [ ] "Tasks" button is visible in farm panel header
- [ ] Tasks modal opens with 4 tabs
- [ ] **Upcoming Tasks Tab**:
  - [ ] Shows planned tasks
  - [ ] Task details display correctly
  - [ ] "Mark Complete" button works
- [ ] **Completed Tasks Tab**:
  - [ ] Shows completed tasks
  - [ ] No action buttons on completed tasks
- [ ] **Create Task Tab**:
  - [ ] All form fields work
  - [ ] Field selection shows farmer's fields
  - [ ] Materials checkbox reveals material selection
  - [ ] Dose rate inputs work
  - [ ] Task creates successfully
  - [ ] Bulk assignment works (multiple fields)
- [ ] **Field History Tab**:
  - [ ] Field dropdown populates
  - [ ] Year filter works
  - [ ] History timeline displays correctly
  - [ ] Materials used shows in history

### 6. Edi Kante Debug (Task #4)
- [ ] Debug endpoint at `/api/debug/edi-kante-fields` works (admin only)
- [ ] Shows if Edi Kante exists in database
- [ ] Shows field count and details
- [ ] Shows auth user connection
- [ ] Provides troubleshooting recommendations

### 7. Chat Functionality
- [ ] Chat input works
- [ ] Messages send and receive
- [ ] Language detection works in responses
- [ ] Error messages display appropriately

### 8. Weather Display
- [ ] Weather location shows correctly
- [ ] 24-hour forecast displays (or unavailable message)
- [ ] 5-day forecast displays (or unavailable message)

### 9. Mobile Responsiveness
- [ ] Dashboard adapts to mobile screens
- [ ] Panels stack vertically on mobile
- [ ] All modals work on mobile
- [ ] Touch interactions work for map drawing

### 10. Database Migrations
- [ ] All new tables created successfully:
  - [ ] materials
  - [ ] task_templates
  - [ ] tasks
  - [ ] task_fields
  - [ ] task_materials
  - [ ] field_history
  - [ ] crop_varieties
- [ ] Sample data inserted correctly
- [ ] Foreign keys work properly
- [ ] Triggers function correctly

## API Endpoints to Test

1. **Authentication**:
   - POST `/auth/login`
   - POST `/auth/register`
   - GET `/auth/logout`

2. **Dashboard**:
   - GET `/farmer/dashboard`
   - GET `/api/fields`
   - GET `/api/weather/farmer`
   - GET `/api/messages`

3. **Field Management**:
   - POST `/api/fields/add`
   - GET `/farmer/draw-field` (if implemented)

4. **Task Management**:
   - GET `/api/tasks/templates`
   - GET `/api/tasks/materials`
   - GET `/api/tasks/list`
   - POST `/api/tasks/create`
   - POST `/api/tasks/bulk-create`
   - PUT `/api/tasks/{id}/complete`
   - GET `/api/tasks/field-history/{field_id}`
   - GET `/api/tasks/upcoming`

5. **Debug**:
   - GET `/api/debug/edi-kante-fields` (admin auth required)

## Test Users

1. **Edi Kante** (Slovenia):
   - Phone: +38640187648
   - Should see Slovenian interface
   - Check if fields display

2. **Test Italian Farmer**:
   - Create with Italy as country
   - Should see Italian interface

3. **Test English Farmer**:
   - Create with USA/UK as country
   - Should see English interface

## Performance Checks

- [ ] Page load time < 3 seconds
- [ ] API responses < 1 second
- [ ] No JavaScript errors in console
- [ ] No 500 errors in server logs

## Security Checks

- [ ] Unauthorized users cannot access dashboard
- [ ] Farmers can only see their own data
- [ ] SQL injection not possible in forms
- [ ] XSS protection working
- [ ] Debug endpoints require admin auth

## Regression Tests (Task #19)

- [ ] Existing WhatsApp integration still works
- [ ] Existing farmers can still login
- [ ] Old field data still displays
- [ ] Chat history preserved
- [ ] No data loss from migrations

## Deployment Verification

- [ ] Build succeeds in AWS CodeBuild
- [ ] Docker image pushed to ECR
- [ ] ECS service updates successfully
- [ ] Health checks pass
- [ ] No errors in CloudWatch logs
- [ ] Database migrations run successfully
- [ ] All features work on production URL

## Known Issues / Notes

- Database is not accessible from local machine (AWS RDS private subnet)
- Weather API may show "unavailable" if not configured
- Google Maps requires valid API key with proper permissions
- Chat requires OpenAI API key configuration

## Testing Complete

- [ ] All critical features tested
- [ ] No blocking issues found
- [ ] Performance acceptable
- [ ] Security verified
- [ ] Ready for production use

---

Last tested: _________________
Tested by: _________________
Version: v4.7.1