# HR Recruitment - Extended Application Form

## Overview
This module extends the standard HR recruitment application form with comprehensive candidate information fields including education history, work experience, skills, and referees.

## Features

### Extended Applicant Fields
- **Cover Letter**: Rich text field for applicant's motivation letter
- **Education History**: Multiple qualifications with details
  - Degree/Certification
  - Institution
  - Field of Study
  - Year Completed
  - Grade/GPA
  - Currently Studying flag
- **Work Experience**: Multiple positions with comprehensive details
  - Position/Job Title
  - Company
  - Start/End Dates
  - Currently Working flag
  - Key Responsibilities
  - Key Achievements
  - Automatic duration calculation
- **Skills**: Many2many relationship with hr.skill
- **Referees/References**: Multiple references with contact details
  - Name, Position, Company
  - Relationship type
  - Email and Phone
  - Years Known
  - Can Contact flag
  - Contact tracking (contacted date, feedback)

### Public Application Web Form
- Fully functional online application form at `/jobs/apply/<job_id>`
- Dynamic form fields (add multiple education, experience, referees)
- Auto-population to HR module
- Success page with tracking ID
- Mobile-responsive design

### Enhanced Applicant Form
- Smart buttons for Education, Experience, and Referees counts
- Qualifications Summary section
- Dedicated notebook pages for each section
- Inline editing capabilities

### Computed Fields
- Education Count
- Highest Education
- Experience Count
- Total Experience Years
- Skills Count
- Referee Count

## Installation

### Prerequisites
- Odoo 17.0
- `hr_recruitment` (Odoo standard)
- `hr_applicant_tracking_random` (base tracking module)
- `website` (Odoo standard)
- `hr_skills` (Odoo standard)

### Steps
1. Copy this module to your Odoo addons directory
2. Update the apps list in Odoo
3. Install "HR Recruitment - Extended Application Form"

## Usage

### For HR Staff

#### Viewing Extended Information
1. Open any applicant record
2. Use smart buttons to view counts and access detailed records
3. Navigate through notebook pages:
   - Cover Letter
   - Education
   - Work Experience
   - Skills
   - Referees

#### Adding Information Manually
1. Open applicant form
2. Go to respective notebook page
3. Click "Add a line" to add new entries

### For Job Applicants

#### Applying Online
1. Navigate to `/jobs/apply/<job_id>`
2. Fill in personal information
3. Write cover letter
4. Add education history (click "Add Another Education" for multiple)
5. Add work experience (click "Add Another Experience" for multiple)
6. Select skills from dropdown
7. Add referees (click "Add Another Referee" for multiple)
8. Submit application
9. Save the tracking ID provided

## Technical Details

### New Models

#### hr.applicant.education
- Fields: degree, institution, field_of_study, year_completed, grade, currently_studying
- Validation: Year completed cannot be in future
- Display name: "Degree - Institution (Year)"

#### hr.applicant.experience
- Fields: position, company, start_date, end_date, currently_working, responsibilities, achievements
- Computed: duration_months
- Validation: Date logic (end > start, not in future)
- Display name: "Position at Company (Year)"

#### hr.applicant.referee
- Fields: name, position, company, relationship, email, phone, years_known, can_contact
- Tracking: contacted, contacted_date, feedback
- Validation: Email format, years_known range
- Display name: "Name (Company)"

### Extended Models

#### hr.applicant
- New fields: cover_letter, education_ids, experience_ids, skill_ids, referee_ids
- Computed fields: education_count, highest_education, experience_count, total_experience_years, skill_count, referee_count
- Smart button actions: action_view_education, action_view_experience, action_view_referees

### Controllers

#### /jobs/apply/<job_id>
- Displays application form for specific job
- Loads skills for dropdown

#### /jobs/apply/submit (POST)
- Handles form submission
- Creates applicant and related records
- Returns tracking ID

#### /jobs/apply/success
- Displays success message with tracking ID

### Security
- Public users can create applicant records and related data
- HR Users can read/write all records
- HR Managers have full access

## Configuration
No additional configuration required. Works out of the box after installation.

## Known Issues
None

## Changelog

### Version 1.0.0 (2025-10-19)
- Initial release
- Extended application form with 4 new models
- Public web application form
- Smart buttons and computed fields
- Comprehensive validation

## Support
For support, contact SurePay Ltd IT Department

## License
LGPL-3

## Author
SurePay Ltd
