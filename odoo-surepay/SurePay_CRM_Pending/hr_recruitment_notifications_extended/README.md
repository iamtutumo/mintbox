# HR Recruitment - Extended Notifications

## Overview
This module provides a comprehensive email notification system for the recruitment process with automated stage-based communications.

## Features

### Email Templates (7 Templates)

1. **Application Received Confirmation**
   - Sent automatically when application is submitted
   - Includes tracking ID and application details
   - Provides link to check application status

2. **Eligibility Screening Rejection (Template 1)**
   - For candidates who don't meet minimum requirements
   - Professional and encouraging tone
   - As per SurePay requirements document

3. **Post-Shortlisting Rejection (Template 2)**
   - For candidates not selected after review
   - Encourages future applications
   - As per SurePay requirements document

4. **Interview Invitation**
   - Congratulatory message for shortlisted candidates
   - Interview preparation tips
   - Next steps information

5. **Offer Letter**
   - Job offer notification
   - Position details
   - Next steps and timeline

6. **Onboarding Welcome**
   - Welcome message for accepted candidates
   - Onboarding checklist
   - First day expectations

7. **Generic Stage Change Notification**
   - Flexible template for any stage change
   - Current status update
   - Tracking link included

### Automated Email Triggers

- **On Application Creation**: Sends application received confirmation
- **On Stage Change**: Sends configured email based on stage settings
- **Configurable Per Stage**: Each stage can have its own email template

### Stage Configuration

Each recruitment stage can be configured with:
- **Send Email on Entry**: Toggle to enable/disable automatic emails
- **Email Template**: Select which template to use
- **Email Description**: Document what email will be sent

## Installation

### Prerequisites
- Odoo 17.0
- `hr_recruitment` (Odoo standard)
- `hr_applicant_tracking_random` (base tracking module)
- `hr_recruitment_stages_surepay` (custom stages module)

### Steps
1. Copy this module to your Odoo addons directory
2. Update the apps list in Odoo
3. Install "HR Recruitment - Extended Notifications"

## Usage

### For HR Staff

#### Configuring Stage Emails
1. Go to **Recruitment > Configuration > Stages**
2. Open a stage (e.g., "Interview")
3. In the "Email Notifications" section:
   - Check "Send Email on Stage Entry"
   - Select an email template (e.g., "Interview Invitation")
   - Add description of what email does
4. Save the stage

#### Recommended Stage-Template Mapping

| Stage | Recommended Template | Auto-Send |
|-------|---------------------|-----------|
| Application Received | Application Received | ✅ Yes |
| Eligibility Screening (Rejected) | Eligibility Rejection | ✅ Yes |
| Shortlisting | - | ❌ No |
| Committee Review | - | ❌ No |
| Interview | Interview Invitation | ✅ Yes |
| Committee Final | - | ❌ No |
| Offer | Offer Letter | ✅ Yes |
| Onboarding | Onboarding Welcome | ✅ Yes |
| Rejected (after shortlist) | Shortlisting Rejection | ✅ Yes |

#### Manual Email Sending
1. Open any applicant record
2. Click "Send message" or use email composer
3. Select one of the email templates
4. Customize if needed
5. Send

### For Applicants

Applicants will automatically receive emails when:
- They submit an application
- Their application moves to a configured stage
- They are rejected at any stage
- They are invited for interview
- They receive an offer
- They enter onboarding

All emails include:
- Professional SurePay Ltd branding
- Clear next steps
- Tracking ID for status checking
- Contact information for questions

## Technical Details

### Models Extended

#### hr.recruitment.stage
- New fields:
  - `send_email_on_enter` (Boolean)
  - `email_template_id` (Many2one to mail.template)
  - `email_description` (Text)

#### hr.applicant
- Override `create()`: Send application received email
- Override `write()`: Send stage-based emails on stage change
- Automatic email sending with error handling

### Email Templates

All templates use Jinja2 syntax and include:
- Personalized greeting
- Position and company information
- Tracking ID integration
- Professional formatting
- Mobile-responsive HTML

### Automated Actions

- **On Create**: Application received email sent automatically
- **On Stage Change**: If stage has `send_email_on_enter=True`, sends configured template
- **Error Handling**: Email failures don't block stage changes

### Security

- Uses sudo() for email sending to ensure delivery
- Error logging for failed emails
- Graceful failure handling

## Configuration

### Setting Up Stage Emails

1. **Application Received Stage**:
   - Template: "Application Received"
   - Auto-send: Yes

2. **Eligibility Screening Stage** (for rejections):
   - Template: "Eligibility Rejection"
   - Auto-send: Yes (when moving rejected candidates)

3. **Interview Stage**:
   - Template: "Interview Invitation"
   - Auto-send: Yes

4. **Offer Stage**:
   - Template: "Offer Letter"
   - Auto-send: Yes

5. **Onboarding Stage**:
   - Template: "Onboarding Welcome"
   - Auto-send: Yes

6. **Rejected Stage** (after shortlisting):
   - Template: "Shortlisting Rejection"
   - Auto-send: Yes

### Customizing Email Templates

1. Go to **Settings > Technical > Email > Templates**
2. Search for "Recruitment:"
3. Edit any template to customize:
   - Subject line
   - Email body
   - Styling
   - Content

## Best Practices

1. **Test Emails First**: Send test emails before enabling auto-send
2. **Review Templates**: Customize templates to match your company voice
3. **Monitor Delivery**: Check email logs for failed deliveries
4. **Applicant Communication**: Ensure applicants know to check spam folders
5. **Tracking Links**: Always include tracking ID in rejection emails

## Known Issues

None

## Changelog

### Version 1.0.0 (2025-10-19)
- Initial release
- 7 comprehensive email templates
- Automated email triggers
- Stage-based email configuration
- Application received auto-confirmation

## Support

For support, contact SurePay Ltd IT Department

## License

LGPL-3

## Author

SurePay Ltd
