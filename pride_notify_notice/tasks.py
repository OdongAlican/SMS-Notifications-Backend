from celery import shared_task
from pride_notify_notice.utils import handle_loans_due, handle_birthdays, handle_URA_reports, handle_group_loans, update_group_loans
import urllib3
from datetime import datetime
import json
from .models import GroupLoanSMSLog, SMSLog, BirthdaySMSLog
from dateutil.parser import parse
import os
from dotenv import load_dotenv
from django.conf import settings
from openpyxl import Workbook
# from openpyxl.styles import Font, Alignment
from openpyxl.utils import get_column_letter
from django.core.mail import EmailMessage
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
load_dotenv()

@shared_task(bind=True, max_retries=5, default_retry_delay=300)
def retrieve_data(self):
    try:
        loan_data = handle_loans_due()
        # print(loan_data)
        person_list = loan_data.get("Person", [])

        if not person_list:
            raise ValueError("Empty 'Person' list received.")

        # updated_loan_list = update_List(person_list)
        response_data = []

        for loan in person_list:
            response = send_sms_to_api(loan)
            if response:
                response_data.append(response)

        return response_data

    except (ValueError) as e:
        print(f"Data error: {e}")
        raise self.retry(exc=e)

    except Exception as exc:
        print(f"Unexpected error occurred: {exc}")
        raise self.retry(exc=exc)



@shared_task(bind=True, max_retries=5, default_retry_delay=300)
def retrieve_birthday_data(self):
    try:
        birthday_data = handle_birthdays()
        # print(birthday_data)
        person_list = birthday_data.get("Person", [])

        if not person_list:
            raise ValueError("Empty 'Person' list received.")

        # updated_birthday_list = update_List_birthdays(person_list)
        response_data = []

        for birthday in person_list:
            response = send_sms_to_api(birthday)
            if response:
                response_data.append(response)

        return response_data

    except (ValueError) as e:
        print(f"Data error: {e}")
        raise self.retry(exc=e)

    except Exception as exc:
        print(f"Unexpected error occurred: {exc}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=5, default_retry_delay=300)
def retrieve_ura_report(self):
    try:
        ura_report_data = handle_URA_reports()
        print(ura_report_data)

        report_list = ura_report_data.get("Report", [])
        if not report_list:
            raise ValueError("Empty 'Report' list received.")

        wb = Workbook()
        ws = wb.active
        ws.title = "URA Report"
        
        # Get the initial ledger balance from the first transaction for opening balance
        opening_balance = float(report_list[0].get('LEDGER_BAL', 0)) if report_list else 0
        
        # Extract GL Account Number from first item
        gl_account_no = report_list[0].get('GL_ACCT_NO', 'N/A') if report_list else 'N/A'
        
        # Get start and end dates from first and last items in report
        try:
            start_date = datetime.fromisoformat(report_list[0]['TRAN_DT'].replace('Z', '+00:00')).strftime('%d/%m/%Y') if report_list else 'N/A'
            end_date = datetime.fromisoformat(report_list[-1]['TRAN_DT'].replace('Z', '+00:00')).strftime('%d/%m/%Y') if report_list else 'N/A'
        except (ValueError, KeyError, TypeError):
            start_date = 'N/A'
            end_date = 'N/A'
        
        # Add report title and date
        report_date = datetime.now().strftime('%d/%m/%Y')
        
        # Insert title row (Row 1)
        ws.append(["URA Transaction Report"])
        ws.merge_cells(f'A1:M1')  # Merge cells across all columns
        title_cell = ws['A1']
        title_cell.font = Font(bold=True, size=14)
        title_cell.alignment = Alignment(horizontal='center')
        
        # Insert date row (Row 2)
        ws.append([f"Generated on: {report_date}"])
        ws.merge_cells(f'A2:M2')  # Merge cells across all columns
        date_cell = ws['A2']
        date_cell.font = Font(italic=True)
        date_cell.alignment = Alignment(horizontal='center')
        
        # Insert GL Account No row (Row 3)
        ws.append([f"GL Account No: {gl_account_no}"])
        ws.merge_cells(f'A3:M3')  # Merge cells across all columns
        gl_cell = ws['A3']
        gl_cell.font = Font(bold=True)
        gl_cell.alignment = Alignment(horizontal='left')
        
        # Insert Account Description row (Row 4)
        ws.append(["Uganda Revenue Authority ePayments -Cash"])
        ws.merge_cells(f'A4:M4')  # Merge cells across all columns
        desc_cell = ws['A4']
        desc_cell.alignment = Alignment(horizontal='left')
        
        # Insert Date Range row (Row 5)
        ws.append([f"Period: {start_date} to {end_date}"])
        ws.merge_cells(f'A5:M5')  # Merge cells across all columns
        range_cell = ws['A5']
        range_cell.font = Font(bold=True)
        range_cell.alignment = Alignment(horizontal='left')
        
        # Insert empty row (Row 6)
        ws.append([""])
        
        # Insert opening balance section (Row 7)
        opening_balance_formatted = "{:,.2f}".format(opening_balance)
        ws.append(["Opening Balance:", "", "", "", "", "", "", "", "", "", "", opening_balance_formatted, ""])
        ws.merge_cells(f'A7:K7')  # Merge cells A-K
        opening_balance_label = ws['A7']
        opening_balance_label.font = Font(bold=True)
        opening_balance_label.alignment = Alignment(horizontal='right')
        
        # Format the opening balance cell
        opening_balance_cell = ws['L7']  # Column L, row 7
        opening_balance_cell.font = Font(bold=True)
        opening_balance_cell.number_format = '#,##0.00'
        
        # Insert empty row (Row 8)
        ws.append([""])
        
        # Add headers (Row 9)
        headers = [
            "S/N", "Post Date", "Effective Date", "Created By", "Transaction Description",
            "Reference", "Contra Account", "Origin Branch", "Debit", "Credit", "PRN", "Balance", "Payment Mode"
        ]
        ws.append(headers)

        # Bold headers
        for col_num, header in enumerate(headers, start=1):
            ws.cell(row=9, column=col_num).font = Font(bold=True)  # Now header is on row 9
            ws.cell(row=9, column=col_num).alignment = Alignment(horizontal='center')

        # Initialize running balance with opening balance
        running_balance = opening_balance

        # Add transactions starting from row 10
        start_row = 10
        for idx, report in enumerate(report_list, 1):
            try:
                post_date = datetime.fromisoformat(report['TRAN_DT'].replace('Z', '+00:00')).strftime('%d/%m/%Y')
            except:
                post_date = ""

            try:
                effective_date = datetime.fromisoformat(report['EFFECTIVE_DT'].replace('Z', '+00:00')).strftime('%d/%m/%Y')
            except:
                effective_date = ""

            created_by = report.get('USER_NAME', '')
            if created_by:
                created_by = ' '.join(word.capitalize() for word in created_by.lower().split())

            transaction_desc = report.get('TRAN_DESC', '')
            prn_value = report.get('PRN', '')
            tin_value = report.get('TIN', '')

            if prn_value and f"PRN: {prn_value}" not in transaction_desc:
                transaction_desc += f", PRN: {prn_value}"
            if tin_value and f"TIN: {tin_value}" not in transaction_desc:
                transaction_desc += f", TIN: {tin_value}"

            debit_amt = float(report.get('DEBIT_AMT') or 0)
            credit_amt = float(report.get('CREDIT_AMT') or 0)
            
            # Calculate running balance
            running_balance = running_balance + credit_amt - debit_amt
            calculated_ledger_bal = running_balance

            row = [
                idx,
                post_date,
                effective_date,
                created_by,
                transaction_desc,
                str(report.get('TRAN_REF_TXT', '')),    # Keep as string
                str(report.get('CONTRA_ACCT_NO', '')),  # Keep as string
                str(report.get('USER_BU', '')),
                debit_amt,
                credit_amt,
                str(prn_value),                         # Force as string
                calculated_ledger_bal,
                str(report.get('PAYMENT_TYPE', '')),
            ]

            ws.append(row)

        # Format numeric columns with comma and 2 decimals - adjust row index for headers now at row 9
        money_columns = ['I', 'J', 'L']  # Debit, Credit, Balance
        for col in money_columns:
            for cell in ws[col][start_row-1:]:  # Start after headers
                cell.number_format = '#,##0.00'

        # Format text columns to prevent scientific notation - adjust row index
        text_columns = ['F', 'G', 'K']  # Reference, Contra Account, PRN
        for col in text_columns:
            for cell in ws[col][start_row-1:]:  # Start after headers
                cell.number_format = '@'
                cell.alignment = Alignment(horizontal='left')

        # Auto-adjust column widths
        for col_cells in ws.columns:
            max_length = 0
            column = col_cells[0].column
            col_letter = get_column_letter(column)
            for cell in col_cells:
                try:
                    if cell.value:
                        max_length = max(max_length, len(str(cell.value)))
                except:
                    pass
            ws.column_dimensions[col_letter].width = max_length + 2

        # Add borders to the entire table
        thin_border = Border(left=Side(style='thin'), 
                             right=Side(style='thin'),
                             top=Side(style='thin'),
                             bottom=Side(style='thin'))
                             
        # Apply the border to all cells with content
        for row in ws.iter_rows(min_row=9, max_row=ws.max_row, min_col=1, max_col=13):
            for cell in row:
                cell.border = thin_border
                
        # Apply alternating row colors for better readability
        for row_idx in range(10, ws.max_row + 1):  # Start from row 10
            if row_idx % 2 == 0:  # even rows
                for col_idx in range(1, 14):  # columns A-M
                    ws.cell(row=row_idx, column=col_idx).fill = PatternFill(start_color="F2F2F2", 
                                                                           end_color="F2F2F2",
                                                                           fill_type="solid")

        # Save Excel file
        excel_filename = f"ura_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        wb.save(excel_filename)

        # Send the Excel file via email
        send_csv_report_email(
            recipient_email=settings.URA_REPORT_EMAILS,
            subject="URA Report Excel",
            message="Please find attached the latest URA report.",
            csv_file_path=excel_filename
        )

        print(f"URA report saved to {excel_filename}")
        return [{
            'filename': excel_filename,
            'content': f"URA report generated and saved to {excel_filename}"
        }]

    except (ValueError) as e:
        print(f"Data error: {e}")
        raise self.retry(exc=e)

    except Exception as exc:
        print(f"Unexpected error occurred: {exc}")
        raise self.retry(exc=exc)


def send_csv_report_email(recipient_email, subject, message, csv_file_path):
    try:
        recipients = recipient_email if isinstance(recipient_email, list) else [recipient_email]

        email = EmailMessage(
            subject=subject,
            body=message,
            from_email=settings.SENDER_EMAIL,
            to=recipients,
        )

        # Attach CSV file
        if os.path.exists(csv_file_path):
            with open(csv_file_path, 'rb') as f:
                email.attach(os.path.basename(csv_file_path), f.read(), 'text/csv')
        else:
            print("CSV file not found at:", csv_file_path)
            return False

        email.send()
        print(f"Email sent to {recipient_email} with CSV attachment.")
        return True
    except Exception as e:
        print("Error sending CSV report email:", e)
        return False



@shared_task(bind=True, max_retries=5, default_retry_delay=300)
def retrieve_group_loans(self):
    try:
        group_loans_data = handle_group_loans()
        # print(group_loans_data)
        person_list = group_loans_data.get("Report", [])
        # print(person_list)

        if not person_list:
            raise ValueError("Empty 'Person' list received.")

        updated_birthday_list = update_group_loans(person_list)
        response_data = []

        for group_loan in updated_birthday_list:
            response = send_sms_to_api(group_loan)
            if response:
                response_data.append(response)

        return response_data

    except (ValueError) as e:
        print(f"Data error: {e}")
        raise self.retry(exc=e)

    except Exception as exc:
        print(f"Unexpected error occurred: {exc}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=2, default_retry_delay=60)
def send_sms_to_api(self, message_detail):
    resp = ""
    http = urllib3.PoolManager(cert_reqs='CERT_NONE', assert_hostname=False)
    response_data = {}
    
    try:
        # Set up base fields
        acct_nm = ""
        tel_number = ""
        message = ""
        log_model = None
        due_dt_for_db = None
        amt_due = None
        date_of_birth = None
        group_cust_no = None

        if 'AMT_DUE' in message_detail:
            # Loan due message handling (existing code)
            acct_nm = message_detail.get('CUST_NM')
            tel_number = message_detail.get('TEL_NUMBER')
            due_dt_serial = message_detail.get('DUE_DT')
            amt_due = float(message_detail.get('AMT_DUE', 0))

            due_dt_obj = parse(due_dt_serial) if isinstance(due_dt_serial, str) else due_dt_serial
            due_dt_for_db = due_dt_obj.date()
            due_dt_for_sms = due_dt_obj.strftime('%d-%m-%Y')

            formatted_amt_due = "{:,}".format(round(amt_due))
            message = (
                f"Dear {acct_nm}, your loan installment of {formatted_amt_due} UGX is due on {due_dt_for_sms}. "
                "Thank you for banking with us. Toll Free: 0800333999"
            )
            log_model = SMSLog

        elif 'BIRTH_DT' in message_detail:
            # Birthday message
            acct_nm = message_detail.get('FIRST_NM')
            tel_number = message_detail.get('TEL_NUMBER')
            date_of_birth_raw = message_detail.get('BIRTH_DT')
            client_type = message_detail.get('CLIENT_TYPE', 'CUSTOMER')

            try:
                date_of_birth = parse(date_of_birth_raw).date()
            except Exception as e:
                print(f"Failed to parse BIRTH_DT: {e}")
                date_of_birth = None

            message = (
                f"Dear {acct_nm}, Pride Wishes you a Happy Birthday. We value our relationship with you. "
                "Thank you for choosing Pride. Toll Free: 0800333999"
            )
            log_model = BirthdaySMSLog

        
        elif 'GROUP_CUST_NO' in message_detail:
            # Group loan message - updated format
            full_name = message_detail.get('MEMBER_NM', '')
            
            name_parts = full_name.split()
            if len(name_parts) > 1:
                display_name = name_parts[-1]
            else:
                display_name = full_name
        
            acct_nm = full_name
            tel_number = message_detail.get('PHONE', '')
            group_cust_no = message_detail.get('GROUP_CUST_NO', '')
            
            try:
                loan_amount = float(message_detail.get('LOAN_AMOUNT_PAID', '0'))
                comp_amount = float(message_detail.get('COMP_AMOUNT_PAID', '0'))
                vol_amount = float(message_detail.get('VOL_AMOUNT_PAID', '0'))
                
                total_amount = loan_amount + comp_amount + vol_amount
                
                formatted_total = "{:,.0f}".format(total_amount)
            except (ValueError, TypeError) as e:
                print(f"Error calculating total amount: {e}")
                formatted_total = "0"
            
            try:
                create_dt = datetime.fromisoformat(message_detail.get('CREATE_DT', '').replace('Z', '+00:00'))
                formatted_date = create_dt.strftime('%d-%m-%Y')
            except (ValueError, TypeError, AttributeError) as e:
                print(f"Error formatting date: {e}")
                formatted_date = datetime.now().strftime('%d-%m-%Y')
            
            message = (
                f"Dear {display_name}, your a/c has been credited with UGX {formatted_total} on {formatted_date}. "
                "For Help Call 0800333999. Never share your ATM/Mobile PIN."
            )
            log_model = GroupLoanSMSLog

        else:
            raise ValueError("Invalid message_detail format: no recognized fields found.")

        # Send SMS (existing code)
        sender_name = os.getenv("MOONLIGHT_SENDER_NAME", "default_sender")
        password = os.getenv("MOONLIGHT_SENDER_PASSWORD", "default_password")
        address = os.getenv("MOONLIGHT_SENDER_ADDRESS", "http://example.com/api")

        resp = http.request(
            'GET',
            f"{address}?sender_name={sender_name}&password={password}&recipient_addr={tel_number}&message={message}"
        )

        # Attempt to parse response
        try:
            api_response = json.loads(resp.data.decode('utf-8'))
        except json.decoder.JSONDecodeError:
            api_response = {"raw_response": resp.data.decode('utf-8')}


        response_data = {
            'account_name': acct_nm,
            'phone_number': tel_number,
            'message': message,
            'due_date': due_dt_for_db,
            'amount_due': amt_due,
            'status': api_response,
            'response_data': api_response
        }

        # Save to appropriate model
        if log_model == SMSLog:
            log_model.objects.create(
                account_name=acct_nm,
                phone_number=tel_number,
                message=message,
                due_date=due_dt_for_db,
                amount_due=amt_due,
                status=api_response,
                response_data=api_response
            )
        elif log_model == BirthdaySMSLog:
            log_model.objects.create(
                acct_nm=acct_nm,
                client_type=client_type,
                message=message,
                date_of_birth=date_of_birth,
                contact=tel_number,
                status=api_response,
                response_data=api_response
            )
        elif log_model == GroupLoanSMSLog:
            # Create new group loan SMS log entry
            log_model.objects.create(
                acct_nm=acct_nm,
                group_cust_no=group_cust_no,
                message=message,
                contact=tel_number,
                status=api_response,
                response_data=api_response
            )

        return response_data

    except Exception as e:
        error_msg = str(e)
        fallback_response = resp.data.decode('utf-8') if resp else "No response received"
        print(f"Error sending SMS: {error_msg}")

        # Log even failed attempts
        if 'SMSLog' in str(type(log_model)):
            log_model.objects.create(
                account_name=acct_nm,
                phone_number=tel_number,
                message=message,
                due_date=due_dt_for_db,
                amount_due=amt_due,
                status=fallback_response,
                response_data={"error": error_msg}
            )
        elif 'BirthdaySMSLog' in str(type(log_model)):
            log_model.objects.create(
                acct_nm=acct_nm,
                client_type=client_type if 'client_type' in locals() else 'Birthday',
                message=message,
                date_of_birth=date_of_birth,
                contact=tel_number,
                status=fallback_response,
                response_data={"error": error_msg}
            )
        elif 'GroupLoanSMSLog' in str(type(log_model)):
            # Error handling for group loan SMS
            log_model.objects.create(
                acct_nm=acct_nm,
                group_cust_no=group_cust_no if group_cust_no else "",
                message=message,
                contact=tel_number,
                status=fallback_response,
                response_data={"error": error_msg}
            )

        return {
            'account_name': acct_nm,
            'phone_number': tel_number,
            'message': message,
            'due_date': due_dt_for_db,
            'amount_due': amt_due,
            'status': fallback_response,
            'response_data': {"error": error_msg}
        }