# -*- coding: utf-8 -*-
"""
Migration script to fix database schema issues for surepay_payroll module
This includes adding missing columns, relationships, and cleaning up fields
"""

def migrate(cr, version):
    """
    Comprehensive database schema fixes for surepay_payroll module
    """

    # 1. Add missing columns to hr_employee table
    cr.execute("""
        ALTER TABLE hr_employee
        ADD COLUMN IF NOT EXISTS advance_count INTEGER DEFAULT 0
    """)

    cr.execute("""
        ALTER TABLE hr_employee
        ADD COLUMN IF NOT EXISTS loan_count INTEGER DEFAULT 0
    """)

    cr.execute("""
        ALTER TABLE hr_employee
        ADD COLUMN IF NOT EXISTS total_advance_outstanding NUMERIC DEFAULT 0.0
    """)

    cr.execute("""
        ALTER TABLE hr_employee
        ADD COLUMN IF NOT EXISTS total_loan_outstanding NUMERIC DEFAULT 0.0
    """)

    cr.execute("""
        ALTER TABLE hr_employee
        ADD COLUMN IF NOT EXISTS lst_amount NUMERIC DEFAULT 0.0
    """)

    cr.execute("""
        ALTER TABLE hr_employee
        ADD COLUMN IF NOT EXISTS advance_amount NUMERIC DEFAULT 0.0
    """)

    cr.execute("""
        ALTER TABLE hr_employee
        ADD COLUMN IF NOT EXISTS loan_amount NUMERIC DEFAULT 0.0
    """)

    cr.execute("""
        ALTER TABLE hr_employee
        ADD COLUMN IF NOT EXISTS other_deductions NUMERIC DEFAULT 0.0
    """)

    cr.execute("""
        ALTER TABLE hr_employee
        ADD COLUMN IF NOT EXISTS nssf_number VARCHAR
    """)

    cr.execute("""
        ALTER TABLE hr_employee
        ADD COLUMN IF NOT EXISTS tin_number VARCHAR
    """)

    cr.execute("""
        ALTER TABLE hr_employee
        ADD COLUMN IF NOT EXISTS payroll_country VARCHAR DEFAULT 'ug'
    """)

    cr.execute("""
        ALTER TABLE hr_employee
        ADD COLUMN IF NOT EXISTS current_budget_id INTEGER
    """)

    cr.execute("""
        ALTER TABLE hr_employee
        ADD COLUMN IF NOT EXISTS total_budget_allocated NUMERIC DEFAULT 0.0
    """)

    cr.execute("""
        ALTER TABLE hr_employee
        ADD COLUMN IF NOT EXISTS total_budget_spent NUMERIC DEFAULT 0.0
    """)

    cr.execute("""
        ALTER TABLE hr_employee
        ADD COLUMN IF NOT EXISTS total_budget_remaining NUMERIC DEFAULT 0.0
    """)

    cr.execute("""
        ALTER TABLE hr_employee
        ADD COLUMN IF NOT EXISTS budget_utilization NUMERIC DEFAULT 0.0
    """)

    # 2. Create loan table if it doesn't exist
    cr.execute("""
        CREATE TABLE IF NOT EXISTS surepay_payroll_hr_loan (
            id SERIAL PRIMARY KEY,
            employee_id INTEGER NOT NULL,
            amount_requested DOUBLE PRECISION NOT NULL,
            date_requested DATE NOT NULL,
            status VARCHAR(20) NOT NULL DEFAULT 'draft',
            currency_id INTEGER,
            company_id INTEGER,
            installment_amount DOUBLE PRECISION NOT NULL,
            total_installments INTEGER NOT NULL,
            installments_paid INTEGER DEFAULT 0,
            outstanding_balance DOUBLE PRECISION DEFAULT 0.0,
            reason TEXT,
            rejection_reason TEXT,
            create_uid INTEGER,
            create_date TIMESTAMP WITHOUT TIME ZONE,
            write_uid INTEGER,
            write_date TIMESTAMP WITHOUT TIME ZONE
        )
    """)

    # Add foreign key constraints for loan table
    cr.execute("""
        ALTER TABLE surepay_payroll_hr_loan
        ADD CONSTRAINT IF NOT EXISTS fk_surepay_payroll_hr_loan_employee_id
        FOREIGN KEY (employee_id) REFERENCES hr_employee(id) ON DELETE RESTRICT
    """)

    cr.execute("""
        ALTER TABLE surepay_payroll_hr_loan
        ADD CONSTRAINT IF NOT EXISTS fk_surepay_payroll_hr_loan_currency_id
        FOREIGN KEY (currency_id) REFERENCES res_currency(id) ON DELETE RESTRICT
    """)

    cr.execute("""
        ALTER TABLE surepay_payroll_hr_loan
        ADD CONSTRAINT IF NOT EXISTS fk_surepay_payroll_hr_loan_company_id
        FOREIGN KEY (company_id) REFERENCES res_company(id) ON DELETE RESTRICT
    """)

    # Add indexes for loan table
    cr.execute("""
        CREATE INDEX IF NOT EXISTS idx_surepay_payroll_hr_loan_employee_id ON surepay_payroll_hr_loan(employee_id)
    """)

    cr.execute("""
        CREATE INDEX IF NOT EXISTS idx_surepay_payroll_hr_loan_status ON surepay_payroll_hr_loan(status)
    """)

    cr.execute("""
        CREATE INDEX IF NOT EXISTS idx_surepay_payroll_hr_loan_date_requested ON surepay_payroll_hr_loan(date_requested)
    """)

    # 3. Fix salary advance table fields
    # Add missing columns
    cr.execute("""
        ALTER TABLE surepay_payroll_hr_salary_advance
        ADD COLUMN IF NOT EXISTS date_requested DATE
    """)

    cr.execute("""
        ALTER TABLE surepay_payroll_hr_salary_advance
        ADD COLUMN IF NOT EXISTS currency_id INTEGER
    """)

    cr.execute("""
        ALTER TABLE surepay_payroll_hr_salary_advance
        ADD COLUMN IF NOT EXISTS is_deducted BOOLEAN DEFAULT FALSE
    """)

    # Copy data from request_date to date_requested if needed
    cr.execute("""
        UPDATE surepay_payroll_hr_salary_advance
        SET date_requested = request_date
        WHERE date_requested IS NULL AND request_date IS NOT NULL
    """)

    # Update is_deducted based on existing relationships
    cr.execute("""
        UPDATE surepay_payroll_hr_salary_advance sa
        SET is_deducted = EXISTS (
            SELECT 1 FROM surepay_payroll_hr_payslip_line pl
            WHERE pl.salary_advance_id = sa.id
        )
        WHERE is_deducted = FALSE
    """)

    # Clean up unnecessary loan-specific fields from salary advance table
    loan_fields_to_drop = [
        'advance_loan_type', 'amount_approved', 'auto_deduct', 'bank_account_id',
        'collateral_details', 'collateral_required', 'early_repayment_penalty',
        'guarantor_id', 'guarantor_required', 'hr_manager_notes', 'hr_officer_notes',
        'installment_amount', 'installments_paid', 'interest_frequency', 'interest_rate',
        'interest_type', 'last_installment_date', 'late_payment_fee', 'loan_purpose',
        'loan_term', 'next_installment_date', 'number_of_installments', 'repayment_method',
        'repayment_plan', 'repayment_start_date', 'total_interest', 'total_repaid',
        'total_repayable', 'request_date'
    ]

    for field in loan_fields_to_drop:
        cr.execute(f"""
            ALTER TABLE surepay_payroll_hr_salary_advance DROP COLUMN IF EXISTS {field}
        """)

    # Add useful fields to salary advance
    cr.execute("""
        ALTER TABLE surepay_payroll_hr_salary_advance
        ADD COLUMN IF NOT EXISTS reason TEXT
    """)

    cr.execute("""
        ALTER TABLE surepay_payroll_hr_salary_advance
        ADD COLUMN IF NOT EXISTS rejection_reason TEXT
    """)

    # 4. Add relationship columns to payslip line table
    cr.execute("""
        ALTER TABLE surepay_payroll_hr_payslip_line
        ADD COLUMN IF NOT EXISTS salary_advance_id INTEGER
    """)

    cr.execute("""
        ALTER TABLE surepay_payroll_hr_payslip_line
        ADD COLUMN IF NOT EXISTS loan_id INTEGER
    """)

    # Add foreign key constraints
    cr.execute("""
        ALTER TABLE surepay_payroll_hr_payslip_line
        ADD CONSTRAINT IF NOT EXISTS surepay_payroll_hr_payslip_line_salary_advance_id_fkey
        FOREIGN KEY (salary_advance_id) REFERENCES surepay_payroll_hr_salary_advance(id) ON DELETE SET NULL
    """)

    cr.execute("""
        ALTER TABLE surepay_payroll_hr_payslip_line
        ADD CONSTRAINT IF NOT EXISTS surepay_payroll_hr_payslip_line_loan_id_fkey
        FOREIGN KEY (loan_id) REFERENCES surepay_payroll_hr_loan(id) ON DELETE SET NULL
    """)

    # Add indexes
    cr.execute("""
        CREATE INDEX IF NOT EXISTS surepay_payroll_hr_payslip_line_salary_advance_id_idx
        ON surepay_payroll_hr_payslip_line(salary_advance_id)
    """)

    cr.execute("""
        CREATE INDEX IF NOT EXISTS surepay_payroll_hr_payslip_line_loan_id_idx
        ON surepay_payroll_hr_payslip_line(loan_id)
    """)

    # 5. Initialize computed fields for existing employees
    cr.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name = 'surepay_payroll_hr_salary_advance'
        )
    """)
    advance_table_exists = cr.fetchone()[0]

    if advance_table_exists:
        cr.execute("""
            UPDATE hr_employee
            SET advance_count = (
                SELECT COUNT(*)
                FROM surepay_payroll_hr_salary_advance
                WHERE surepay_payroll_hr_salary_advance.employee_id = hr_employee.id
            )
        """)

        cr.execute("""
            UPDATE hr_employee
            SET total_advance_outstanding = (
                SELECT COALESCE(SUM(outstanding_balance), 0.0)
                FROM surepay_payroll_hr_salary_advance
                WHERE surepay_payroll_hr_salary_advance.employee_id = hr_employee.id
                AND surepay_payroll_hr_salary_advance.status IN ('approved', 'active')
                AND surepay_payroll_hr_salary_advance.outstanding_balance > 0
            )
        """)

    cr.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name = 'surepay_payroll_hr_loan'
        )
    """)
    loan_table_exists = cr.fetchone()[0]

    if loan_table_exists:
        cr.execute("""
            UPDATE hr_employee
            SET loan_count = (
                SELECT COUNT(*)
                FROM surepay_payroll_hr_loan
                WHERE surepay_payroll_hr_loan.employee_id = hr_employee.id
            )
        """)

        cr.execute("""
            UPDATE hr_employee
            SET total_loan_outstanding = (
                SELECT COALESCE(SUM(outstanding_balance), 0.0)
                FROM surepay_payroll_hr_loan
                WHERE surepay_payroll_hr_loan.employee_id = hr_employee.id
                AND surepay_payroll_hr_loan.status IN ('approved', 'active')
                AND surepay_payroll_hr_loan.outstanding_balance > 0
            )
        """)
