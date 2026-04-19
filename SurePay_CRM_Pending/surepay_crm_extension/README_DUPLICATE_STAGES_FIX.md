# CRM Duplicate Stages Fix

## Problem Description

The SurePay CRM Extension module was creating duplicate CRM stages due to multiple sources creating the same stages:

1. **`hooks.py`** - The `post_init_hook` function was creating stages through SQL INSERT statements
2. **`crm_stage_data.xml`** - The XML data file was also creating stages through `<record>` definitions  
3. **`crm_stage.py`** - The `_setup_surepay_stages` method also had SQL INSERT statements

This resulted in multiple stages with the same name appearing in the CRM pipeline, causing confusion and inconsistent behavior.

## Solution Implemented

### 1. Removed Duplicate Stage Creation Sources

- **Removed `crm_stage_data.xml` reference from `__manifest__.py`**: The XML data file is no longer loaded, preventing duplicate stage creation through XML records.
- **Removed `_setup_surepay_stages` method from `crm_stage.py`**: This method was redundant since the `post_init_hook` already handles stage creation.

### 2. Enhanced `post_init_hook` Function

The `post_init_hook` function in `hooks.py` has been completely rewritten to:

- **Archive all existing stages first**: Start with a clean slate by setting `fold = true` on all stages
- **Create/update SurePay stages systematically**: Define the 6 required stages and either create new ones or update existing ones
- **Remove duplicates**: Archive any duplicate SurePay stages, keeping only the one with the lowest ID for each name
- **Ensure proper sequencing**: Set the correct sequence numbers for all SurePay stages
- **Set Cold Lead as default**: Configure Cold Lead as the default stage for leads without a stage

### 3. Added Manual Cleanup Method

A new method `cleanup_duplicate_stages()` has been added to the `CrmStage` model that can be called manually to fix any remaining duplicate issues.

## Expected Result

After applying this fix, you should see exactly **6 visible CRM stages**:

1. **Cold Lead** (Sequence: 1)
2. **Prospecting** (Sequence: 10) 
3. **Preparation** (Sequence: 20)
4. **Closing** (Sequence: 30)
5. **Won** (Sequence: 40, is_won: True)
6. **Lost** (Sequence: 50)

All other stages should be hidden (fold = true) and not appear in the CRM pipeline.

## How to Apply the Fix

### Option 1: Module Upgrade (Recommended)

1. Upgrade the `surepay_crm_extension` module:
   ```python
   # In Odoo shell or via UI
   env['ir.module.module'].search([('name', '=', 'surepay_crm_extension')]).button_upgrade()
   ```

2. The `post_init_hook` will automatically run and clean up the duplicates.

### Option 2: Manual Cleanup

If the module upgrade doesn't resolve the issue, you can run the manual cleanup:

1. **Via Python Code**:
   ```python
   # In Odoo shell
   env['crm.stage'].cleanup_duplicate_stages()
   ```

2. **Via SQL** (Advanced):
   ```sql
   -- Archive all stages
   UPDATE crm_stage SET fold = true;
   
   -- Create/update SurePay stages (run for each stage)
   INSERT INTO crm_stage (name, sequence, fold, is_won, team_id, create_uid, write_uid, create_date, write_date)
   VALUES ('{"en_US": "Cold Lead"}', 1, false, false, NULL, 1, 1, NOW(), NOW())
   ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, sequence = EXCLUDED.sequence, fold = EXCLUDED.fold, is_won = EXCLUDED.is_won;
   
   -- Repeat for other stages with appropriate values
   
   -- Remove duplicates
   UPDATE crm_stage SET fold = true
   WHERE name->>'en_US' IN ('Cold Lead', 'Prospecting', 'Preparation', 'Closing', 'Won', 'Lost')
   AND id NOT IN (
       SELECT MIN(id) 
       FROM crm_stage 
       WHERE name->>'en_US' IN ('Cold Lead', 'Prospecting', 'Preparation', 'Closing', 'Won', 'Lost')
       GROUP BY name->>'en_US'
   );
   
   -- Ensure SurePay stages are visible
   UPDATE crm_stage SET fold = false WHERE name->>'en_US' IN ('Cold Lead', 'Prospecting', 'Preparation', 'Closing', 'Won', 'Lost');
   ```

## Verification

### Using the Test Script

A test script `test_stages.py` has been provided to verify the fix:

```python
# In Odoo shell
exec(open('/path/to/surepay_crm_extension/test_stages.py').read())
test_crm_stages(env)
```

This script will:
- Count total, visible, and hidden stages
- Detect duplicate stages
- Verify all expected SurePay stages are present
- Check stage sequences
- Provide an overall pass/fail result

### Manual Verification

1. **Check in Odoo UI**:
   - Go to CRM > Pipeline
   - Verify only 6 stages are visible in the kanban view
   - Check that stages are in the correct order

2. **Check via Database**:
   ```sql
   SELECT name->>'en_US', sequence, fold, is_won 
   FROM crm_stage 
   WHERE fold = false 
   ORDER BY sequence;
   ```
   
   Expected output:
   ```
   Cold Lead      |   1 | f | f
   Prospecting    |  10 | f | f  
   Preparation    |  20 | f | f
   Closing        |  30 | f | f
   Won            |  40 | f | t
   Lost           |  50 | f | f
   ```

## Troubleshooting

### Issue: Still seeing duplicate stages

**Solution**: Run the manual cleanup method:
```python
env['crm.stage'].cleanup_duplicate_stages()
```

### Issue: Stages are missing or in wrong order

**Solution**: The `post_init_hook` should handle this, but you can also run:
```python
env['crm.stage'].cleanup_duplicate_stages()
```

### Issue: Module upgrade fails

**Solution**: Check the server logs for errors and ensure:
1. The `crm_stage_data.xml` file is not referenced in `__manifest__.py`
2. The `hooks.py` file has the correct syntax
3. Database permissions are sufficient

## Files Modified

1. **`__manifest__.py`**: Removed `crm_stage_data.xml` from data section
2. **`hooks.py`**: Completely rewritten `post_init_hook` function
3. **`crm_stage.py`**: Removed `_setup_surepay_stages` method, added `cleanup_duplicate_stages` method
4. **`test_stages.py`**: New test script for verification
5. **`README_DUPLICATE_STAGES_FIX.md`**: This documentation

## Prevention

To prevent future duplicate stage issues:

1. **Single Source of Truth**: Only use `post_init_hook` for stage creation
2. **Avoid XML Data Files**: Don't use XML data files for stages that are created programmatically
3. **Idempotent Operations**: Ensure stage creation logic handles existing stages properly
4. **Regular Testing**: Use the provided test script to verify stage configuration

## Support

If you encounter any issues with this fix or need further assistance, please check the server logs for detailed error messages and ensure all modifications have been applied correctly.
