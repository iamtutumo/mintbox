# Testing Which File Causes the Error

The error "Element odoo has extra content: data, line 3" persists.

Let's try removing template files temporarily from the manifest to identify the issue.

## Test 1: Remove template files from manifest

Edit `__manifest__.py` and comment out the template files:

```python
'data': [
    'security/ir.model.access.csv',
    'views/hr_applicant_tracking_views.xml',
    'views/hr_applicant_views.xml',
    # 'views/website_templates.xml',
    # 'views/mail_templates.xml',
],
```

If this works, the issue is with the template files.

## Test 2: If Test 1 works, try adding templates one by one

First add website_templates.xml, then mail_templates.xml to see which one fails.

## Alternative: Check if module name is correct

The error might also be because the module name in the files doesn't match.
Check that all XML files reference the correct module name.
