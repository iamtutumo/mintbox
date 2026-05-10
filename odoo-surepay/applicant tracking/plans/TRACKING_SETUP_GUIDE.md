# Applicant Tracking Setup Guide

## What Was Fixed

1. **Removed duplicate form views** - There were two views with the same ID causing conflicts
2. **Added tracking fields to the main form** - Tracking ID and Public Link are now in a "Tracking" tab
3. **Added "Send Tracking Link" button** - Visible in the form view when applicant has an email
4. **Added method to generate tracking IDs for existing applicants**
5. **Fixed validation error** - Changed from onchange to write method to prevent creating status history for unsaved records
6. **Added post-install hook** - Automatically generates tracking IDs for existing applicants when module is upgraded

## Where to Find Tracking Information

### In the Applicant Form View

When you open an applicant record, you'll see:

1. **Top right button box**: "Send Tracking Link" button (only visible if email exists)
2. **"Tracking" tab** (in the notebook at the bottom):
   - **Tracking ID**: Unique ID like `APP-ABC12345`
   - **Public Link**: URL that applicants can use to check their status
   - **Last Status Update**: When the status was last changed
   - **Status History**: Table showing all status changes

### In the Tree/List View

The tree view shows the Tracking ID column for all applicants.

## How to Use

### For New Applicants

New applicants created after module installation will automatically get:
- A unique tracking ID (format: `APP-XXXXXXXX`)
- A public application URL
- Initial status history entry

### For Existing Applicants (Before Module Installation)

**Automatic Method (Recommended):**
- When you upgrade the module, the post-install hook will automatically generate tracking IDs for all existing applicants
- Just upgrade the module and refresh - tracking IDs will appear!

**Manual Method (if needed):**
If some applicants still don't have tracking IDs:

1. Go to **Recruitment > Applicants Tracking**
2. Select the applicants that need tracking IDs (or select all)
3. Click **Action** menu (⚙️ gear icon)
4. Select **"Generate Tracking IDs"**
5. All selected applicants without tracking IDs will get one

### Sending Tracking Links to Applicants

1. Open an applicant record
2. Make sure the applicant has an email address
3. Click the **"Send Tracking Link"** button in the top right
4. The applicant will receive an email with their tracking link

## Troubleshooting

### "I don't see the tracking fields"

**Solution**: 
1. Upgrade the module: Apps > Search for "hr_applicant_tracking_random" > Upgrade
2. Refresh your browser (Ctrl+F5)
3. Clear browser cache if needed

### "Existing applicants don't have tracking IDs"

**Solution**: Use the "Generate Tracking IDs" action from the list view (see above)

### "The public link doesn't work"

**Check**:
1. The tracking ID exists
2. The web.base.url is configured correctly in Settings > Technical > System Parameters
3. The controller route is accessible

## Technical Details

### Files Modified

1. `models/hr_applicant.py` - Added tracking fields and methods
2. `views/hr_applicant_views.xml` - Main form view with tracking tab
3. `views/hr_applicant_tracking_views.xml` - Tree view and actions
4. `controllers/main.py` - Public tracking page controller

### Database Fields Added

- `tracking_id` (Char) - Unique tracking identifier
- `public_application_url` (Char, computed) - Public URL for status checking
- `status_history` (One2many) - Relationship to status history records
- `last_status_update` (Datetime) - Last status change timestamp

### Views Available

1. **Form View** (`view_applicant_form_tracking`) - Priority 20, includes tracking tab
2. **Tree View** (`view_applicant_tree_tracking`) - Shows tracking ID column
3. **Search View** (inherited) - Can search by tracking ID

## Next Steps

1. **Upgrade the module** in Odoo
2. **Generate tracking IDs** for existing applicants
3. **Test** by creating a new applicant and checking the tracking fields
4. **Send a tracking link** to verify email functionality
