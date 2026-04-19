# SurePay Payroll Uganda

**Author:** SurePay Ltd
**Website:** https://surepayltd.com
**Version:** 17.0.1.0.1
**License:** LGPL-3

## Overview

SurePay Payroll Uganda is a comprehensive Odoo 17 payroll management system specifically designed for Ugandan businesses. It provides complete payroll processing with full compliance to Ugandan statutory requirements including NSSF contributions, PAYE tax calculations using URA brackets, and Local Service Tax (LST).

## Features

### 🇺🇬 **Uganda-Specific Features**
- **NSSF Contributions**: Automatic calculation of 5% employee + 10% employer contributions
- **PAYE Tax**: URA tax bracket calculations with progressive rates
- **Local Service Tax (LST)**: Configurable per employee/location
- **Statutory Compliance**: Built-in compliance with Ugandan labor laws

### 💰 **Payroll Processing**
- **Salary Structures**: Flexible salary structure configuration
- **Payslip Generation**: Automated payslip generation with detailed breakdown
- **Multiple Pay Periods**: Support for monthly, quarterly, semi-annual, and annual payroll
- **Contract Integration**: Seamless integration with employee contracts

### 📊 **Comprehensive Reporting**
- **Payslip Reports**: Detailed employee payslips with all components
- **NSSF Reports**: Monthly NSSF contribution reports (employee + employer)
- **PAYE Reports**: Tax reports by employee with totals
- **LST Reports**: Local Service Tax reports by employee/location
- **Payroll Summary**: Complete payroll overview with statistics

### 🔐 **Security & Access Control**
- **Employee Access**: Employees can view their own payslips
- **HR Officer Access**: Process payroll and manage employee data
- **HR Manager Access**: Configure rules and access all reports
- **Multi-company Support**: Secure multi-company payroll processing

### 🌍 **Multi-Country Flexibility**
- **Country Selection**: Configurable payroll country per employee
- **Flexible Rules**: Adaptable for other East African countries
- **Multi-company**: Support for multiple legal entities
- **Currency Support**: Multi-currency payroll processing

## Installation

### Prerequisites
- Odoo 17 Community Edition
- HR Contract module (`hr_contract`)
- HR Holidays module (`hr_holidays`)

### Installation Steps
1. Place the module in your Odoo addons directory
2. Update your addons list in Odoo
3. Install the "SurePay Payroll Uganda" module
4. Configure payroll structures and rules

## Configuration

### 1. Employee Setup
1. Navigate to Employees → Employees
2. Edit employee records and add:
   - NSSF Number
   - TIN Number
   - Payroll Country (default: Uganda)
   - LST Amount (if applicable)
   - Advance/Loan deductions (if applicable)

### 2. Contract Configuration
1. Navigate to Employees → Contracts
2. Create or edit employee contracts
3. Set salary structure to "Uganda Payroll Structure"
4. Configure allowances:
   - HRA (House Rent Allowance)
   - Transport Allowance
   - Meal Allowance
   - Other allowances

### 3. Payroll Structure
The module includes a pre-configured "Uganda Payroll Structure" with:
- **Basic Pay**: Employee basic salary
- **Allowances**: HRA, Transport, Meal allowances
- **NSSF**: 5% employee + 10% employer contributions
- **PAYE**: URA tax bracket calculations
- **LST**: Local Service Tax
- **Deductions**: Advances, loans, other deductions
- **Net Salary**: Final take-home pay

## Usage

### Processing Payroll
1. Navigate to Payroll → Payslips
2. Click "Generate Payslips"
3. Select employees and period
4. Review and confirm payslips
5. Process payments

### Viewing Payslips
- **Employees**: Can view their own payslips through Employee Portal
- **HR Officers**: Can view and process department payslips
- **HR Managers**: Can access all payslips and reports

### Generating Reports
1. Navigate to Payroll → Reporting
2. Select report type:
   - Uganda Payslip (individual employee)
   - Uganda Payroll Summary (comprehensive overview)
3. Select date range and filters
4. Generate and export reports

## Tax Calculations

### PAYE Tax Brackets (URA)
The system uses the following URA tax brackets:

| Income Range (UGX) | Tax Rate | Calculation |
|-------------------|----------|-------------|
| 0 – 235,000 | 0% | 0 |
| 235,001 – 335,000 | 10% | 10% of amount above 235,000 |
| 335,001 – 410,000 | 20% | 10,000 + 20% of amount above 335,000 |
| 410,001 – 10,000,000 | 30% | 25,000 + 30% of amount above 410,000 |
| Above 10,000,000 | 40% | 2,900,000 + 40% of amount above 10,000,000 |

### NSSF Contributions
- **Employee Contribution**: 5% of gross salary
- **Employer Contribution**: 10% of gross salary
- **Total NSSF**: 15% of gross salary

### Local Service Tax (LST)
- Configurable per employee
- Set in employee record
- Can vary by location/department

## Multi-Country Support

The module is designed to be flexible for multi-country use:

### Supported Countries
- **Uganda (Default)**: Full NSSF, PAYE, LST compliance
- **Kenya**: Adaptable for Kenyan payroll rules
- **Tanzania**: Ready for Tanzanian payroll configuration
- **Rwanda**: Support for Rwandan payroll requirements
- **Other**: Customizable for additional countries

### Configuration Steps
1. Set employee's "Payroll Country" field
2. Create country-specific salary structures
3. Configure country-specific tax rules
4. Set up country-specific reports

## Security Model

### User Roles
- **Employee**: View own payslips only
- **HR Officer**: Process payroll, manage department employees
- **HR Manager**: Full access to configuration and all reports

### Access Rights
- **Payslip Access**: Role-based access control
- **Report Access**: Hierarchical access to reports
- **Configuration Access**: Manager-level configuration rights
- **Multi-company**: Company-based data segregation

## Integration

### HR Module Integration
- **Employee Management**: Seamless employee data integration
- **Contract Management**: Contract-based payroll processing
- **Leave Management**: Integration with leave system
- **Department Structure**: Department-based payroll processing

### Accounting Integration
- **Journal Entries**: Automatic payroll journal creation
- **Account Mapping**: Configurable account mappings
- **Cost Centers**: Department/cost center allocation
- **Financial Reporting**: Integration with financial reports

## Customization

### Adding New Rules
1. Navigate to Payroll → Salary Rules
2. Create new salary rule
3. Configure calculation logic
4. Add to salary structure

### Custom Reports
1. Navigate to Payroll → Reporting
2. Create custom report templates
3. Configure data sources
4. Set up report parameters

### Country Extensions
1. Create country-specific salary structures
2. Configure country-specific tax rules
3. Set up country-specific reports
4. Add country-specific fields

## Troubleshooting

### Common Issues

#### Payslip Calculation Errors
- Check employee contract configuration
- Verify salary structure assignment
- Ensure all required fields are populated
- Review salary rule calculations

#### Report Generation Issues
- Verify report template configuration
- Check data access permissions
- Ensure date ranges are correct
- Review filter configurations

#### Access Control Issues
- Verify user role assignments
- Check security rules configuration
- Ensure company assignments are correct
- Review department hierarchies

### Support
For technical support and assistance:
- **Email**: odoo@surepayltd.com
- **Website**: https://surepayltd.com
- **Documentation**: Available in module help section

## Compliance Information

### Ugandan Statutory Requirements
- **NSSF Act**: Compliant with National Social Security Fund regulations
- **Income Tax Act**: PAYE calculations follow URA guidelines
- **Local Government Act**: LST calculations as per local regulations
- **Labor Act**: Employee rights and protections

### Regular Updates
The module is regularly updated to reflect:
- Changes in tax rates and brackets
- Updates to statutory requirements
- New compliance regulations
- Bug fixes and improvements

## Contributing

We welcome contributions to improve the module:
- **Bug Reports**: Submit issues with detailed descriptions
- **Feature Requests**: Suggest new features and improvements
- **Code Contributions**: Submit pull requests for enhancements
- **Documentation**: Help improve documentation

## License

This module is licensed under the GNU Lesser General Public License v3.0 (LGPL-3.0). See the LICENSE file for details.

## Changelog

### Version 17.0.1.0.1
- Database schema fixes and improvements
- Added missing computed fields to hr_employee table
- Integrated salary advance and loan relationship columns
- Enhanced migration scripts for proper database upgrades
- Fixed stored computed field initialization
- Improved data consistency and relationships

### Version 17.0.1.0.0
- Initial release for Odoo 17
- Uganda-specific payroll implementation
- NSSF, PAYE, LST compliance features
- Multi-country support framework
- Enhanced security and reporting
- Comprehensive documentation

---

**SurePay Payroll Uganda** - Comprehensive payroll management for Ugandan businesses with full statutory compliance and multi-country flexibility.
