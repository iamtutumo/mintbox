# SurePay CRM Extension

## Overview

The SurePay CRM Extension is a comprehensive Odoo 17 module that extends the standard CRM functionality with custom sales stages, enhanced lead management, and improved user interface filtering. This module is designed to work seamlessly across different Odoo deployments and servers.

## Features

### 🎯 Custom Sales Stages
- **Cold Lead**: Default starting stage for new leads
- **Prospecting**: Active prospecting stage
- **Preparation**: Deal preparation stage
- **Closing**: Final negotiation stage
- **Won**: Successfully closed deals
- **Lost**: Unsuccessful deals

### 🔧 Enhanced Lead Management
- **School Code Field**: Custom field for tracking school codes
- **Cold Lead Management**: Special handling for cold leads
- **Stage Validation**: Automatic validation for stage transitions
- **Lead Migration**: Automatic migration of existing leads to custom stages

### 🎨 Improved User Interface
- **Stage Filtering**: Complete hiding of non-custom stages
- **Kanban View Optimization**: Only custom stages visible in pipeline
- **Search Filters**: Custom filters for each stage
- **Clean Interface**: Simplified stage selection and management

## Requirements

### Odoo Version
- **Odoo 17.0+** (Required)
- **Community or Enterprise Edition**

### Dependencies
- **crm**: Base CRM module
- **base**: Base Odoo module

### External Dependencies
- **Python**: No external Python packages required
- **System**: No external system binaries required

## Installation

### 1. Module Placement
Place the module in your Odoo addons directory:
```
/odoo/addons/
└── surepay_crm_extension/
    ├── __init__.py
    ├── __manifest__.py
    ├── models/
    ├── views/
    ├── data/
    ├── security/
    └── hooks.py
```

### 2. Module Installation via UI
1. Navigate to **Apps** menu
2. Update apps list (if necessary)
3. Search for "SurePay CRM Extension"
4. Click **Install**

### 3. Module Installation via Command Line
```bash
# Update module list
docker exec <container_name> odoo -d <database_name> -u base --stop-after-init

# Install the module
docker exec <container_name> odoo -d <database_name> -i surepay_crm_extension --stop-after-init
```

## Configuration

### Automatic Setup
The module includes automatic setup via `post_init_hook`:
- Archives default Odoo CRM stages
- Creates custom SurePay stages
- Migrates existing leads to appropriate stages
- Sets Cold Lead as default stage

### Manual Verification
After installation, verify:
1. **CRM Pipeline**: Only 6 custom stages visible
2. **Lead Stage Dropdown**: Only custom stages available
3. **Stage Management**: Custom stages properly configured
4. **Lead Migration**: Existing leads migrated to Cold Lead

## Usage

### CRM Pipeline
The CRM pipeline will show only the 6 custom stages:
```
Cold Lead → Prospecting → Preparation → Closing → Won/Lost
```

### Lead Management
1. **New Leads**: Automatically assigned to Cold Lead stage
2. **Stage Progression**: Move leads through the sales pipeline
3. **School Code**: Required when moving to Closing stage
4. **Won/Lost**: Mark deals as won or lost

### Stage Filtering
- **Search Filters**: Use custom filters for each stage
- **Kanban View**: Automatically filtered to show only active stages
- **Tree View**: Consistent filtering across all views

## Technical Details

### Module Structure
```
surepay_crm_extension/
├── __init__.py                 # Module initialization
├── __manifest__.py            # Module manifest
├── models/                    # Model definitions
│   ├── __init__.py
│   ├── crm_lead.py           # CRM Lead model extensions
│   └── crm_stage.py          # CRM Stage model extensions
├── views/                     # View definitions
│   ├── crm_lead_views.xml    # Lead view customizations
│   └── crm_stage_views.xml   # Stage view customizations
├── data/                      # Data files
│   └── crm_stage_data.xml    # Stage data definitions
├── security/                  # Security configuration
│   └── ir.model.access.csv   # Access rights
└── hooks.py                   # Installation/uninstallation hooks
```

### Database Changes
- **crm.stage**: Extended with custom fields
- **crm.lead**: Extended with school_code and is_cold_lead fields
- **Stage Migration**: Automatic migration of existing data

### Hooks
- **post_init_hook**: Runs after installation to set up stages and migrate data
- **uninstall_hook**: Runs before uninstallation to restore default stages

## Troubleshooting

### Common Issues

#### 1. Module Installation Fails with 'Cannot update missing record'
**Problem**: Error: `Cannot update missing record 'crm.crm_case_opportunities'`
**Solution**: This is a known Odoo 17 compatibility issue that has been fixed in the current version.
- Ensure you have the latest version of the module
- The action override now uses the correct Odoo 17 action ID `crm.crm_lead_action_pipeline`
- Run module upgrade: `odoo -d <db> -u surepay_crm_extension`

#### 2. Module Installation Fails
**Problem**: Module doesn't install or shows other errors
**Solution**: 
- Verify Odoo 17 compatibility
- Check that CRM module is installed
- Ensure proper file permissions

#### 2. Stages Not Visible
**Problem**: Custom stages don't appear in the interface
**Solution**:
- Run module upgrade: `odoo -d <db> -u surepay_crm_extension`
- Check browser cache and refresh
- Verify user has CRM access rights

#### 3. Lead Migration Issues
**Problem**: Existing leads not migrated to custom stages
**Solution**:
- Run module upgrade to trigger hooks
- Check database for stage assignments
- Verify hook execution in logs

#### 4. Stage Filtering Not Working
**Problem**: Hidden stages still appear in views
**Solution**:
- Clear browser cache
- Run module upgrade
- Check view definitions for proper domain filters

### Debug Mode
Enable debug mode for detailed logging:
```bash
docker exec <container_name> odoo -d <database_name> --dev=all --log-level=debug
```

## Server Migration

### Pre-Migration Checklist
1. **Backup Database**: Always backup before migration
2. **Export Configuration**: Note any custom configurations
3. **Check Dependencies**: Verify all required modules are available
4. **Test Environment**: Test in staging environment first

### Migration Steps
1. **Copy Module**: Transfer entire module directory to new server
2. **Update Addons Path**: Ensure module is in addons path
3. **Install Dependencies**: Install required modules (crm, base)
4. **Install Module**: Install SurePay CRM Extension
5. **Verify Functionality**: Test all features and configurations

### Post-Migration Verification
- ✅ Module installs without errors
- ✅ All 6 custom stages visible
- ✅ Stage filtering works correctly
- ✅ Lead migration completed
- ✅ User interface functions properly

## Support

### Version Compatibility
- **Odoo 17.0**: Fully supported
- **Odoo 16.0**: Not supported
- **Odoo 15.0**: Not supported

### Known Limitations
- Requires clean installation of CRM module
- Stage names are hardcoded in English
- Custom field names are fixed

### Getting Help
For issues and support:
1. Check this README for common solutions
2. Review Odoo server logs for error details
3. Verify module compatibility with your Odoo version
4. Test in a development environment first

## License

This module is licensed under the LGPL-3 license. See the LICENSE file for details.

## Changelog

### Version 17.0.1.0.0
- Initial release
- Custom CRM stages implementation
- Stage filtering and hiding
- Lead migration functionality
- Kanban view optimization
- Cross-server compatibility improvements
