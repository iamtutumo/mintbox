# Fix: 500 Error When Clicking Tracking Link

## Problem
When clicking the tracking link, you get:
```
500: Internal Server Error
ValueError: View 'hr_applicant_tracking_random.application_status_page' in website 1 not found
```

## Root Cause
In Odoo 17, the `qweb` section in `__manifest__.py` is deprecated. Website templates must be declared in the `data` section instead.

## What Was Fixed

### 1. Moved Templates to Data Section
**Before:**
```python
'data': [
    'security/ir.model.access.csv',
    'views/hr_applicant_tracking_views.xml',
    'views/hr_applicant_views.xml',
],
'qweb': [
    'views/website_templates.xml',
    'views/mail_templates.xml',
],
```

**After:**
```python
'data': [
    'security/ir.model.access.csv',
    'views/hr_applicant_tracking_views.xml',
    'views/hr_applicant_views.xml',
    'views/website_templates.xml',
    'views/mail_templates.xml',
],
```

### 2. Added Missing Dependency
Added `website_hr_recruitment` to dependencies since the controller inherits from it.

**Updated dependencies:**
```python
'depends': [
    'base',
    'website',
    'hr_recruitment',
    'website_hr_recruitment',
],
```

## What to Do Now

### Step 1: Upgrade Module
```
Apps → Search "hr_applicant_tracking_random" → Upgrade
```

### Step 2: Restart Odoo Server (if needed)
```bash
sudo systemctl restart odoo
# or
sudo service odoo restart
```

### Step 3: Clear Browser Cache
Press `Ctrl + F5` or `Cmd + Shift + R`

### Step 4: Test Tracking Link
1. Open any applicant record
2. Copy the **Public Link** from the form
3. Open it in a new browser tab/window
4. You should see the application status page

## Expected Result

When you click the tracking link, you should see:

```
┌────────────────────────────────────────────┐
│  Check Your Application Status             │
├────────────────────────────────────────────┤
│                                            │
│  ✅ Application Found!                     │
│                                            │
│  Hello [Applicant Name],                   │
│                                            │
│  Your application for [Job Position]       │
│  is currently in the [Stage] stage.        │
│                                            │
│  Tracking ID: APP-ABC12345                 │
│  Applied on: [Date]                        │
│  Last Update: [Date]                       │
│                                            │
│  [Back to Home]                            │
│                                            │
└────────────────────────────────────────────┘
```

## Available Routes

After the fix, these public URLs will work:

1. **Direct Tracking Link:**
   ```
   https://yoursite.com/applicant/tracking/APP-ABC12345
   ```

2. **Status Check Form:**
   ```
   https://yoursite.com/job/status
   ```
   (Shows a form where applicants can enter their tracking ID)

## Troubleshooting

### Still Getting 500 Error?

**Check if website_hr_recruitment is installed:**
```
Apps → Search "website_hr_recruitment" → Install if not installed
```

**Verify templates are loaded:**
1. Go to Settings → Technical → User Interface → Views
2. Search for "application_status_page"
3. Should find: `hr_applicant_tracking_random.application_status_page`

**Check Odoo logs:**
```bash
tail -f /var/log/odoo/odoo-server.log
```

### Template Not Found After Upgrade?

**Force reload templates:**
1. Settings → Technical → Database Structure → Views
2. Search: "application_status_page"
3. If found, delete it
4. Upgrade module again

**Or use Odoo shell:**
```python
# Delete old template
env['ir.ui.view'].search([('key', '=', 'hr_applicant_tracking_random.application_status_page')]).unlink()

# Upgrade module
env['ir.module.module'].search([('name', '=', 'hr_applicant_tracking_random')]).button_immediate_upgrade()
```

## Files Changed

1. **`__manifest__.py`**:
   - Moved `website_templates.xml` from `qweb` to `data`
   - Moved `mail_templates.xml` from `qweb` to `data`
   - Added `website_hr_recruitment` to dependencies

## Summary

✅ Templates moved to correct section for Odoo 17
✅ Missing dependency added
✅ Tracking links will now work properly

**Upgrade the module and the tracking links will work!**
