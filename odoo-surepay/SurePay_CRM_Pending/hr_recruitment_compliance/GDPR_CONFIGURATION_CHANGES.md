# GDPR Configuration Menu Changes

## Summary
All GDPR-related settings and features have been moved to a centralized Configuration menu under the Recruitment module.

## Changes Made

### 1. New Configuration Settings Model
**File:** `models/res_config_settings.py`

Created a comprehensive configuration model with the following GDPR settings:

#### Data Retention Settings
- **Default Retention Period (Days)**: Set the default number of days to retain applicant data (default: 730 days / 2 years)
- **Enable Automatic Anonymization**: Toggle automatic anonymization of expired records

#### Consent Settings
- **Auto-Consent for Web Forms**: Automatically grant GDPR consent for web form submissions

#### Audit Log Settings
- **Enable Audit Logging**: Track all actions on applicant records
- **Log IP Addresses**: Record IP addresses in audit logs

#### Export Settings
- **Default Export Format**: Choose between JSON, XML, or PDF for GDPR data exports

#### Notification Settings
- **Notify Before Anonymization**: Send notifications to managers before auto-anonymization
- **Notice Period (Days)**: Number of days before anonymization to send notification (default: 30 days)

### 2. Configuration Views
**File:** `views/res_config_settings_views.xml`

Created a user-friendly configuration interface with:
- Organized sections for different GDPR settings
- Clear descriptions for each setting
- Conditional visibility for dependent fields
- Modern Odoo 17 settings layout

### 3. Menu Structure Changes
**File:** `views/res_config_settings_views.xml`

Created new menu structure:
```
Recruitment
└── Configuration (NEW)
    ├── GDPR Settings (NEW)
    └── Audit Logs (MOVED)
```

### 4. Audit Logs Menu Relocation
**File:** `views/applicant_audit_log_views.xml`

Moved the Audit Logs menu from the main Recruitment menu to the Configuration submenu for better organization.

### 5. Manifest Update
**File:** `__manifest__.py`

Added `views/res_config_settings_views.xml` to the data files list.

## Benefits

1. **Centralized Management**: All GDPR-related settings are now in one place
2. **Better Organization**: Configuration items are separated from operational menus
3. **Easier Administration**: Administrators can quickly access and modify GDPR settings
4. **Improved UX**: Clear categorization and descriptions for all settings
5. **Scalability**: Easy to add more GDPR-related configurations in the future

## Access

To access the new GDPR Configuration:
1. Navigate to **Recruitment** → **Configuration** → **GDPR Settings**
2. Modify settings as needed
3. Click **Save** to apply changes

## Technical Notes

- All settings use `config_parameter` for persistent storage
- Settings are stored in `ir.config_parameter` table
- Default values are provided for all settings
- The configuration model inherits from `res.config.settings` (TransientModel)
- Menu sequence numbers ensure proper ordering

## Future Enhancements

Potential additions to the configuration menu:
- Data retention policies by job position
- Custom anonymization rules
- GDPR compliance reports configuration
- Email template settings for GDPR notifications
- Integration with external compliance tools
