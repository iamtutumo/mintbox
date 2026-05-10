# Troubleshooting: Tracking Fields Not Visible

## Current Status

✅ **Fixed Issues:**
- View priority set to 1 (highest priority)
- Tracking fields moved to top of right column
- Added explicit labels and placeholders
- Fields will show "Not generated yet" if empty

## Step-by-Step Fix

### Step 1: Upgrade Module
```
1. Go to Apps menu
2. Remove "Apps" filter
3. Search for "hr_applicant_tracking_random"
4. Click "Upgrade" button
5. Wait for upgrade to complete
```

### Step 2: Clear Odoo Cache
```
Settings → Technical → Database Structure → Views
Search for: "hr.applicant.form.tracking"
Select the view → Click "Action" → "Reset to Default"
```

### Step 3: Hard Refresh Browser
- **Windows/Linux**: `Ctrl + Shift + R` or `Ctrl + F5`
- **Mac**: `Cmd + Shift + R`

### Step 4: Verify View is Active
1. Go to Settings → Technical → User Interface → Views
2. Search for "hr.applicant.form.tracking"
3. Check that priority = 1
4. Verify the view contains tracking_id and public_application_url fields

### Step 5: Generate Tracking IDs for Existing Records

**Method 1: Using Odoo Shell (Recommended)**
```bash
# In terminal, navigate to Odoo directory
python odoo-bin shell -d YOUR_DATABASE_NAME

# Then run:
applicants = env['hr.applicant'].search([('tracking_id', '=', False)])
for applicant in applicants:
    tracking_id = applicant._generate_tracking_id()
    applicant.write({'tracking_id': tracking_id})
print(f"Generated {len(applicants)} tracking IDs")
```

**Method 2: Using Action Menu**
1. Go to Recruitment → Applicants
2. Select all applicants (checkbox at top)
3. Click Action menu (⚙️)
4. Select "Generate Tracking IDs"

**Method 3: Using Python Script**
Use the `generate_tracking_ids.py` file provided

### Step 6: Test with New Applicant
1. Create a new applicant
2. Fill in required fields
3. Save
4. Check if Tracking ID appears in the right column

## What You Should See

After upgrading, when you open an applicant form, the **right column** should show:

```
┌─────────────────────────────┐
│ Tracking ID                 │
│ APP-ABC12345                │  ← Bold, blue text
│                             │
│ Public Link                 │
│ https://yoursite.com/...    │  ← Clickable link
│                             │
│ Job Position                │
│ [field]                     │
│                             │
│ Department                  │
│ [field]                     │
│                             │
│ Company                     │
│ [field]                     │
└─────────────────────────────┘
```

## Common Issues & Solutions

### Issue 1: Fields Show "Not generated yet"
**Cause**: Applicant doesn't have a tracking ID
**Solution**: 
- For existing applicants: Run one of the generation methods above
- For new applicants: This shouldn't happen - check if create() method is working

### Issue 2: View Doesn't Update After Upgrade
**Cause**: Browser cache or Odoo view cache
**Solution**:
1. Clear browser cache (Ctrl + Shift + R)
2. Reset view: Settings → Technical → Views → Find view → Reset to Default
3. Restart Odoo server if needed

### Issue 3: Wrong Form View is Displayed
**Cause**: Another view has higher priority
**Solution**:
1. Check view priority: Settings → Technical → Views
2. Search for all "hr.applicant" form views
3. Ensure "hr.applicant.form.tracking" has priority = 1 (lowest number = highest priority)
4. Other views should have priority > 1

### Issue 4: Tracking ID is Empty for All Applicants
**Cause**: Post-install hook didn't run or create() method not working
**Solution**:
```python
# Run in Odoo shell
# Check if any applicants have tracking IDs
with_tracking = env['hr.applicant'].search([('tracking_id', '!=', False)])
print(f"Applicants with tracking: {len(with_tracking)}")

# Generate for all
all_applicants = env['hr.applicant'].search([])
for app in all_applicants:
    if not app.tracking_id:
        app.tracking_id = app._generate_tracking_id()
        
print("Done!")
```

### Issue 5: Public Link is Empty
**Cause**: tracking_id is empty (computed field depends on it)
**Solution**: Generate tracking IDs first (see Issue 4)

## Verification Checklist

After completing all steps, verify:

- [ ] Module upgraded successfully
- [ ] Browser cache cleared
- [ ] Can see "Tracking ID" label in form (right column, top)
- [ ] Can see "Public Link" label below Tracking ID
- [ ] Existing applicants show tracking IDs (not "Not generated yet")
- [ ] New applicants get tracking IDs automatically when saved
- [ ] Public link is clickable and formatted as URL
- [ ] "Send Tracking Link" button works without errors

## Debug Mode

To see more details:

1. **Enable Developer Mode**:
   - Settings → Activate Developer Mode

2. **Check Field Values**:
   - Open applicant
   - Click "Edit" in developer menu
   - Look for tracking_id and public_application_url in the form

3. **Check View XML**:
   - Settings → Technical → Views
   - Search: hr.applicant.form.tracking
   - Click "Edit" → Check XML contains tracking fields

## Still Not Working?

If fields are still not visible after all steps:

1. **Check if fields exist in database**:
```sql
-- Run in database
SELECT column_name 
FROM information_schema.columns 
WHERE table_name = 'hr_applicant' 
AND column_name IN ('tracking_id', 'public_application_url');
```

2. **Check model inheritance**:
```python
# In Odoo shell
model = env['hr.applicant']
print(model._fields.keys())
# Should include 'tracking_id' and 'public_application_url'
```

3. **Restart Odoo server**:
```bash
sudo systemctl restart odoo
# or
sudo service odoo restart
```

4. **Check logs** for any errors:
```bash
tail -f /var/log/odoo/odoo-server.log
```

## Contact Information

If issue persists, provide:
- Odoo version
- Screenshot of the form
- Output of: `env['hr.applicant']._fields.keys()` from shell
- Any error messages in logs
