# -*- coding: utf-8 -*-

import xlwt
import base64
from io import BytesIO
from odoo import api, fields, models


class report_payrollregister(models.AbstractModel):
    _name = 'report.topline_hr_payroll.report_payrollregister'
    _description = 'Payroll Register Report'

    @api.model
    def render_html(self, docids, data=None):
        docargs = {
            'doc_ids': self.ids,
            'doc_model': self.model,
            'data': data,
        }
        return self.env['report'].render('topline_hr_payroll.report_payrollregister', docargs)

    @api.model
    def get_report_values(self, docids, data=None):
        return {
            'doc_ids': [],
            'doc_model': 'payroll.register',
            'data': data,
            'docs': self.env['payroll.register'],
        }


class payroll_reg(models.TransientModel):
    _name = 'payroll.register'
    _description = 'Payroll Register'

    mnths = []
    mnths_total = []
    rules = []
    rules_data = []

    total = 0.0

    name = fields.Char('Name', required=True, size=140)
    start_date = fields.Date('Start Date', required=True)
    end_date = fields.Date('End Date', required=True)
    employee_ids = fields.Many2many('hr.employee', 'payroll_register_rel',
                                    'payroll_year_id', 'employee_id', 'Employees', required=True)
    rule_ids = fields.Many2many('hr.salary.rule', 'payroll_register_rel_salary',
                                'reg_id', 'rule_id', 'Salary Rules', required=True)
    xls_output = fields.Boolean(
        'Excel Output', help='Tick if you want to output of report in excel sheet', default=True)

    def get_months_tol(self):
        return self.mnths_total

    def get_salary_rules(self, form):
        rule_name = []
        rules = []
        rule_ids = form.get('rule_ids', [])
        if rule_ids:
            for r in self.env['hr.salary.rule'].browse(rule_ids):
                rule_name.append(r.name)
                rules.append(r.id)
        self.rules = rules
        self.rules_data = rule_name
        return [rule_name]

    def get_salary(self, form, emp_id, emp_salary, total_mnths):
        total = 0.0
        cnt = 0
        flag = 0
        for r in self.rules:
            rname = self.env['hr.salary.rule'].browse(r)
            self._cr.execute("select pl.name as name ,pl.total \
                                 from hr_payslip_line as pl \
                                 left join hr_payslip as p on pl.slip_id = p.id \
                                 left join hr_employee as emp on emp.id = p.employee_id \
                                 left join resource_resource as r on r.id = emp.resource_id  \
                                where p.employee_id = %s and pl.salary_rule_id = %s \
                                and (p.date_from >= %s) AND (p.date_to <= %s) \
                                group by pl.total,r.name, pl.name,emp.id", (emp_id, r, form.get('start_date', False), form.get('end_date', False),))
            sal = self._cr.fetchall()
            salary = dict(sal)
            cnt += 1
            flag += 1
            if flag > 8:
                continue
            if rname.name in salary:
                emp_salary.append(salary[rname.name])
                total += salary[rname.name]
                total_mnths[cnt] = total_mnths[cnt] + salary[rname.name]
            else:
                emp_salary.append('')

        if len(self.rules) < 9:
            diff = 9 - len(self.rules)
            for x in range(0, diff):
                emp_salary.append('')
        return emp_salary, total, total_mnths

    def get_salary1(self, form, emp_id, emp_salary, total_mnths):
        total = 0.0
        cnt = 0
        flag = 0
        for r in self.rules:
            rname = self.env['hr.salary.rule'].browse(r)
            self._cr.execute("select pl.name as name , pl.total \
                                 from hr_payslip_line as pl \
                                 left join hr_payslip as p on pl.slip_id = p.id \
                                 left join hr_employee as emp on emp.id = p.employee_id \
                                 left join resource_resource as r on r.id = emp.resource_id  \
                                where p.employee_id = %s and pl.salary_rule_id = %s \
                                and (p.date_from >= %s) AND (p.date_to <= %s) \
                                group by pl.total,r.name, pl.name,emp.id", (emp_id, r, form.get('start_date', False), form.get('end_date', False),))

            sal = self._cr.fetchall()
            salary = dict(sal)
            cnt += 1
            flag += 1
            if rname.name in salary:
                emp_salary.append(salary[rname.name])
                total += salary[rname.name]
                total_mnths[cnt] = total_mnths[cnt] + salary[rname.name]
            else:
                emp_salary.append('')
        return emp_salary, total, total_mnths

    def get_employee(self, form, excel=False):
        emp_salary = []
        salary_list = []
        total_mnths = ['Total', 0, 0, 0, 0, 0,
                       0, 0, 0, 0]  # only for pdf report!
        emp_obj = self.env['hr.employee']
        emp_ids = form.get('employee_ids', [])

        total_excel_months = ['Total', ]  # for excel report
        for r in range(0, len(self.rules)):
            total_excel_months.append(0)
        employees = emp_obj.browse(emp_ids)
        for emp_id in employees:
            emp_salary.append(emp_id.name)
            emp_salary.append(emp_id.job_id.name or "")
            emp_salary.append(emp_id.department_id.name or "")
            if excel:
                emp_salary, _, total_mnths = self.get_salary1(
                    form, emp_id.id, emp_salary, total_mnths=total_excel_months)
            else:
                emp_salary, _, total_mnths = self.get_salary(
                    form, emp_id.id, emp_salary, total_mnths)
            salary_list.append(emp_salary)
            emp_salary = []
        self.mnths_total = total_mnths
        return salary_list

    
    def print_report(self):
        """
         To get the date and print the report
         @param self: The object pointer.
         @param cr: A database cursor
         @param uid: ID of the user currently logged in
         @param context: A standard dictionary
         @return: return report
        """
        datas = {'ids': self._context.get('active_ids', [])}

        res = self.read()
        res = res and res[0] or {}
        datas.update({'form': res})

        if datas['form'].get('xls_output', False):
            workbook = xlwt.Workbook()
            sheet = workbook.add_sheet('Payroll Register')
            sheet.row(0).height = 256*3

            title_style = xlwt.easyxf(
                'font: name Times New Roman,bold on, italic on, height 600')
            title_style1 = xlwt.easyxf('font: name Times New Roman,bold on')
            al = xlwt.Alignment()
            al.horz = xlwt.Alignment.HORZ_CENTER
            title_style.alignment = al

            sheet.write_merge(0, 0, 5, 9, 'Payroll Register', title_style)
            sheet.write(1, 6, datas['form']['name'], title_style1)
            sheet.write(2, 4, 'From', title_style1)
            sheet.write(2, 5, fields.Date.to_string(
                datas['form']['start_date']), title_style1)
            sheet.write(2, 6, 'To', title_style1)
            sheet.write(2, 7, fields.Date.to_string(
                datas['form']['end_date']), title_style1)
            main_header = self.get_salary_rules(datas['form'])

            report_header = ['Name', 'Job Position',
                             'Department'] + main_header[0]

            row = self.render_header(sheet, report_header, first_row=5)
            emp_datas = self.get_employee(datas['form'], excel=True)

            value_style = xlwt.easyxf(
                'font: name Helvetica', num_format_str='#,##0.00')
            cell_count = 0
            for value in emp_datas:
                for v in value:
                    sheet.write(row, cell_count, v, value_style)
                    cell_count += 1
                row += 1
                cell_count = 0
            sheet.write(row+1, 0, 'Total', value_style)

            # Get the values for all the totals
            total_datas = self.get_months_tol()
            cell_count = 3
            for value in [total_datas]:
                row += 1
                for v in value[1:]:
                    sheet.write(row, cell_count, v, value_style)
                    cell_count += 1
            stream = BytesIO()
            workbook.save(stream)
            stream.seek(0)
            result = base64.b64encode(stream.read())
            base_url = self.env['ir.config_parameter'].get_param(
                'web.base.url')
            attachment_obj = self.env['ir.attachment']
            attachment_id = attachment_obj.create(
                {'name': self.name+'.xls', 'datas_fname': self.name+'.xls', 'datas': result})
            download_url = '/web/content/' + \
                str(attachment_id.id) + '?download=true'
            return {
                "type": "ir.actions.act_url",
                "url": str(base_url) + str(download_url),
                "target": "self",
            }
        return self.env.ref('topline_hr_payroll.action_report_payroll_register').report_action(self, data=datas, config=False)

    def render_header(self, ws, fields, first_row=0):
        header_style = xlwt.easyxf('font: name Helvetica,bold on')
        col = 0
        for hdr in fields:
            ws.write(first_row, col, hdr, header_style)
            col += 1
        return first_row + 2

    def get_total(self):
        for count in range(1, len(self.mnths_total)):
            if not isinstance(self.mnths_total[count], float) and not isinstance(self.mnths_total[count], int):
                continue
            self.total += self.mnths_total[count]
        return self.total
