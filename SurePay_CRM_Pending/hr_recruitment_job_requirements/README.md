# HR Recruitment - Job Requirements & Screening

## Overview
This module enables automated eligibility screening of applicants based on predefined job requirements. It automatically evaluates candidates against minimum qualifications and rejects those who don't meet the criteria.

## Features

### Job Requirements Configuration

Define requirements for each job position:
- **Minimum Years of Experience**: 0-2, 3-5, 6-10, 10+ years
- **Required Education Level**: High School, Diploma, Bachelor's, Master's, PhD
- **Required Field of Study**: Specific field (e.g., Computer Science)
- **Required Skills**: Select from skill catalog
- **Minimum Required Skills**: How many skills must match

### Automated Screening

**Two Screening Modes:**
1. **Strict Mode**: Applicant must meet ALL requirements
2. **Lenient Mode**: Applicant must meet at least ONE requirement

**Screening Process:**
1. Applicant submits application
2. System automatically compares against job requirements
3. Checks experience, education, and skills
4. Generates screening log with detailed results
5. If failed:
   - Moves to "Rejected" stage
   - Sends eligibility rejection email (Template 1)
   - Updates screening status

### Screening Logs

Complete audit trail for each screening:
- Screening date and result
- Individual check results (Experience, Education, Skills)
- Applicant vs. Required comparison
- Failure reasons (if applicable)
- Auto-screened flag

### Manual Controls

**For HR Managers:**
- **Re-Screen**: Run screening again after updates
- **Manual Override**: Override failed screening
- **View Logs**: Access complete screening history

### Screening Status Tracking

Applicants have screening status:
- **Pending**: Not yet screened
- **Passed**: Met requirements
- **Failed**: Did not meet requirements
- **Manual Review**: Requires manual evaluation
- **Override**: Manually approved despite failure

## Installation

### Prerequisites
- Odoo 17.0
- `hr_recruitment` (Odoo standard)
- `hr_applicant_tracking_random` (base tracking module)
- `hr_recruitment_application_extended` (extended fields module)
- `hr_recruitment_stages_surepay` (custom stages module)
- `hr_recruitment_notifications_extended` (email templates module)

### Steps
1. Copy this module to your Odoo addons directory
2. Update the apps list in Odoo
3. Install "HR Recruitment - Job Requirements & Screening"

## Usage

### For HR Staff

#### Setting Up Job Requirements

1. Go to **Recruitment > Configuration > Job Positions**
2. Open a job position
3. Go to "Job Requirements" tab
4. Enable "Auto-Screening"
5. Configure requirements:
   - Select minimum experience
   - Select required education level
   - Enter field of study (optional)
   - Select required skills
   - Set minimum required skills count
6. Choose screening mode:
   - **Strict**: All requirements must be met
   - **Lenient**: At least one requirement must be met
7. Add screening notes (optional)
8. Save

#### Example Configuration

**Software Developer Position:**
- Auto-Screening: ✅ Enabled
- Screening Mode: Strict
- Min Experience: 3-5 years
- Education Level: Bachelor's Degree
- Field of Study: Computer Science
- Required Skills: Python, JavaScript, SQL
- Min Required Skills: 2

**Result**: Applicant must have:
- 3+ years experience AND
- Bachelor's degree in Computer Science AND
- At least 2 of the 3 required skills

#### Viewing Screening Results

1. Open any applicant record
2. Check "Screening Status" in header
3. Click "Screening Logs" smart button to see details
4. Review "Screening Logs" notebook page for full history

#### Manual Actions

**Re-Screen Applicant:**
1. Open applicant record
2. Click "Re-Screen" button in header
3. New screening is performed

**Override Failed Screening:**
1. Open failed applicant record
2. Click "Override Screening" button (Managers only)
3. Applicant can now proceed in pipeline

#### Viewing All Screening Logs

1. Go to **Recruitment > Screening Logs**
2. View all screening activities
3. Filter by result, date, job, etc.

### For Applicants

Applicants who fail screening:
- Automatically moved to "Rejected" stage
- Receive professional rejection email (Template 1)
- Email explains they don't meet minimum requirements
- Encouraged to apply for other positions

## Technical Details

### Models

#### hr.job (Extended)
New fields:
- `auto_screen_enabled` (Boolean)
- `min_years_experience` (Selection)
- `required_education_level` (Selection)
- `required_field_of_study` (Char)
- `required_skill_ids` (Many2many)
- `min_required_skills` (Integer)
- `strict_screening` (Boolean)
- `screening_notes` (Text)

#### hr.applicant (Extended)
New fields:
- `screening_status` (Selection)
- `screening_log_ids` (One2many)
- `screening_log_count` (Integer - computed)
- `last_screening_date` (Datetime - computed)

New methods:
- `perform_eligibility_screening()`: Main screening logic
- `_check_experience_requirement()`: Experience validation
- `_check_education_requirement()`: Education validation
- `_check_skills_requirement()`: Skills validation
- `_handle_screening_failure()`: Rejection handling

#### applicant.screening.log (New Model)
Fields:
- `applicant_id`, `job_id`, `screening_date`
- `screening_result` (pass/fail/manual)
- `experience_check`, `education_check`, `skills_check`
- `applicant_experience_years`, `required_experience`
- `applicant_education`, `required_education`
- `applicant_skills_count`, `required_skills_count`, `matching_skills_count`
- `screening_notes`, `failure_reasons`

### Screening Logic

**Experience Check:**
- Maps requirement ranges to minimum years
- Compares applicant's total experience
- Pass if applicant meets or exceeds minimum

**Education Check:**
- Ranks education levels (High School=1, PhD=5)
- Compares applicant's highest education
- Optionally checks field of study match
- Pass if education level sufficient and field matches

**Skills Check:**
- Finds intersection of applicant and required skills
- Counts matching skills
- Pass if matches >= minimum required skills

**Overall Result:**
- **Strict Mode**: ALL checks must pass
- **Lenient Mode**: At least ONE check must pass
- N/A checks are ignored in calculation

### Automated Actions

**On Applicant Creation:**
- If job has auto-screening enabled
- Perform eligibility screening
- Create screening log
- Update screening status
- If failed: move to rejected, send email

### Email Integration

Uses Template 1 from notifications module:
- Subject: "Application Update – [Position Title]"
- Professional rejection message
- Encourages future applications
- Sent automatically on screening failure

## Configuration

### Recommended Settings

**Entry-Level Positions:**
- Screening Mode: Lenient
- Min Experience: 0-2 years
- Education: High School or Diploma
- Skills: 1-2 required

**Mid-Level Positions:**
- Screening Mode: Strict
- Min Experience: 3-5 years
- Education: Bachelor's Degree
- Skills: 2-3 required

**Senior Positions:**
- Screening Mode: Strict
- Min Experience: 6-10 years
- Education: Bachelor's or Master's
- Skills: 3-5 required

**Executive Positions:**
- Screening Mode: Strict
- Min Experience: 10+ years
- Education: Master's or PhD
- Skills: 4-6 required

## Best Practices

1. **Test First**: Test screening with sample applicants before enabling
2. **Start Lenient**: Begin with lenient mode, switch to strict after testing
3. **Review Logs**: Regularly review screening logs for accuracy
4. **Update Requirements**: Keep job requirements current
5. **Manual Review**: Use override for edge cases
6. **Clear Communication**: Ensure rejection emails are professional
7. **Skills Catalog**: Maintain accurate skills catalog

## Known Issues

None

## Changelog

### Version 1.0.0 (2025-10-19)
- Initial release
- Automated eligibility screening
- Job requirements configuration
- Screening logs and audit trail
- Manual override capability
- Integration with email notifications
- Strict and lenient screening modes

## Support

For support, contact SurePay Ltd IT Department

## License

LGPL-3

## Author

SurePay Ltd
