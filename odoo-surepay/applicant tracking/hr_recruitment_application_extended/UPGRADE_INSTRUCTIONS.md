# Module Upgrade Instructions

## Issue Resolution: mail.thread Inheritance

### Problem
The module was experiencing a ParseError during upgrade because the models (`hr.applicant.education`, `hr.applicant.experience`, `hr.applicant.referee`) inherit from `mail.thread` and `mail.activity.mixin`, but the view validation was happening before the inheritance was fully processed.

### Solution Implemented
1. **Restored mail.thread inheritance** - Essential for audit tracking
2. **Simplified chatter configuration** - Only essential fields in views
3. **Version bump** - Updated to 17.0.1.0.1 to trigger proper upgrade
4. **Added migration script** - Ensures smooth upgrade process

### Why Keep mail.thread?

**Audit Trail Benefits:**
- ✅ **Track who changed what** - Every field change is logged with user and timestamp
- ✅ **Change history** - Complete audit trail of all modifications
- ✅ **Compliance** - Required for HR data integrity and compliance
- ✅ **Accountability** - Know exactly who modified education, experience, or referee data

**What Gets Tracked:**
- Degree/certification changes
- Institution changes  
- Position/company changes
- All field modifications with before/after values
- User who made the change
- Exact timestamp of change

### Upgrade Steps

#### Option 1: Clean Upgrade (Recommended if data is not critical)
```bash
# 1. Uninstall the module
# Go to Apps → Search "HR Recruitment - Extended Application Form" → Uninstall

# 2. Update the module list
# Apps → Update Apps List

# 3. Reinstall the module
# Apps → Search "HR Recruitment - Extended Application Form" → Install
```

#### Option 2: In-Place Upgrade (Preserves existing data)
```bash
# 1. Restart Odoo server to load new code
sudo systemctl restart odoo

# 2. Upgrade the module via UI
# Apps → Search "HR Recruitment - Extended Application Form" → Upgrade

# OR via command line:
odoo-bin -c /etc/odoo/odoo.conf -d your_database -u hr_recruitment_application_extended --stop-after-init
```

#### Option 3: Force Upgrade (If Option 2 fails)
```bash
# 1. Update module in database directly
psql your_database -c "UPDATE ir_module_module SET state='to upgrade' WHERE name='hr_recruitment_application_extended';"

# 2. Restart Odoo in upgrade mode
odoo-bin -c /etc/odoo/odoo.conf -d your_database -u hr_recruitment_application_extended --stop-after-init

# 3. Restart Odoo normally
sudo systemctl restart odoo
```

### Verification

After upgrade, verify the following:

1. **Check Models Load Correctly:**
   - Go to Settings → Technical → Database Structure → Models
   - Search for: `hr.applicant.education`, `hr.applicant.experience`, `hr.applicant.referee`
   - Verify they exist and have `message_ids`, `message_follower_ids`, `activity_ids` fields

2. **Test Chatter Functionality:**
   - Open any applicant
   - Add/edit an education record
   - Check the chatter shows "Degree changed from X to Y by [User] on [Date]"

3. **Test Views:**
   - Education form should open without errors
   - Experience form should open without errors
   - Referee form should open without errors
   - Chatter section should be visible at bottom of each form

### Troubleshooting

**If you still get the ParseError:**

1. **Clear Odoo cache:**
   ```bash
   # Remove pyc files
   find /mnt/extra-addons/hr_recruitment_application_extended -name "*.pyc" -delete
   
   # Restart Odoo
   sudo systemctl restart odoo
   ```

2. **Check mail module is installed:**
   ```bash
   # In Odoo shell
   odoo-bin shell -d your_database
   >>> self.env['ir.module.module'].search([('name', '=', 'mail')]).state
   # Should return 'installed'
   ```

3. **Verify dependencies:**
   - Ensure `mail` module is installed and up to date
   - Check that `hr_recruitment` is installed
   - Verify `hr_skills` is available

4. **Database update:**
   ```bash
   # Force database schema update
   odoo-bin -c /etc/odoo/odoo.conf -d your_database -u base,mail,hr_recruitment_application_extended --stop-after-init
   ```

### What Changed

**Models (Python files):**
- ✅ Added `_inherit = ['mail.thread', 'mail.activity.mixin']`
- ✅ Added `tracking=True` to key fields (degree, institution, position, company)
- ✅ Imported `ValidationError` for constraints

**Views (XML files):**
- ✅ Added chatter section with `message_follower_ids` and `message_ids`
- ✅ Restricted `message_follower_ids` to internal users only (`groups="base.group_user"`)
- ✅ Simplified configuration (removed `activity_ids` widget to avoid complexity)

**Manifest:**
- ✅ Version bumped to 17.0.1.0.1
- ✅ Confirmed `mail` dependency is present

### Benefits After Upgrade

1. **Full Audit Trail:**
   - See who added/modified education records
   - Track changes to work experience
   - Monitor referee information updates

2. **Compliance:**
   - Meet data protection requirements
   - Provide audit logs for HR compliance
   - Track data modifications for GDPR/data privacy

3. **Accountability:**
   - Clear responsibility for data changes
   - Timestamp all modifications
   - Historical record of all updates

### Support

If you encounter issues:
1. Check Odoo logs: `/var/log/odoo/odoo-server.log`
2. Enable debug mode in Odoo UI
3. Run with `--log-level=debug` for detailed output
4. Check database for orphaned records

### Notes

- The chatter will show automatic messages when tracked fields change
- Messages are stored in `mail_message` table
- Activities can be assigned to follow up on education/experience verification
- Followers can be added to get notifications about changes
