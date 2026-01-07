from flask import Flask, request, current_app, render_template, jsonify
from sqlalchemy import extract, func
from flask_cors import CORS
from flask_migrate import Migrate
from flask_restful import Api, Resource, reqparse
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt, get_jwt_identity
from dotenv import load_dotenv
from config import Config
from auth import bcrypt, check_password, hash_password 
from models import db,Client, Admin, Expense, Subscription, Payment, Invoice, InvoiceItem
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import os
from flask_apscheduler import APScheduler
from mpesa import lipa_na_mpesa
import secrets
import string
from fpdf import FPDF


load_dotenv()
blacklist = set()

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
migrate = Migrate(app, db)  
api = Api(app)
jwt = JWTManager(app)

CORS(app, 
     origins="https://fit-flow-omega.vercel.app",
     supports_credentials=True,
     allow_headers=["Content-Type", "Authorization"],
     methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])

@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload):
    jti = jwt_payload["jti"]
    return jti in blacklist

def send_email(to_email, subject, message, pdf_data=None, pdf_filename="invoice.pdf "):
    """
    Simple plaintext email sender (Gmail SMTP).
    Expects MAIL_USERNAME and MAIL_PASSWORD in env.
    """
    sender_email = os.environ.get("MAIL_USERNAME")
    sender_password = os.environ.get("MAIL_PASSWORD")
    if not sender_email or not sender_password:
        current_app.logger.warning("Email creds missing; skipping email send.")
        return False

    smtp_server = "smtp.gmail.com"
    smtp_port = 587

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(message, "plain"))

    if pdf_data:
            try:
                # Create the PDF attachment part
                pdf_part = MIMEApplication(pdf_data, Name=pdf_filename)
                pdf_part['Content-Disposition'] = f'attachment; filename="{pdf_filename}"'
                msg.attach(pdf_part)
                current_app.logger.info(f"Successfully attached PDF: {pdf_filename}")
            except Exception as e:
                current_app.logger.error(f"Failed to attach PDF: {e}")
                return False # Fail if PDF attachment fails
        # --- End of new part ---

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, to_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        current_app.logger.error(f"Email failed: {e}")
        return False


def create_invoice_pdf(invoice):
    """Generates a PDF for a given invoice object and returns it as bytes."""
    client = invoice.client
    pdf = FPDF()
    pdf.add_page()
    
    # Header
    pdf.set_font("Arial", 'B', 20)
    pdf.cell(0, 10, "FitFlow Gym Invoice", 0, 1, 'C')
    pdf.ln(5)
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 7, "www.fitflow.com", 0, 1, 'C')
    pdf.cell(0, 7, "+254 700 000 000", 0, 1, 'C')
    pdf.ln(10)

    # Invoice Info
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(95, 8, "Bill To:", 0, 0, 'L')
    pdf.cell(95, 8, "Invoice Details:", 0, 1, 'R')
    
    pdf.set_font("Arial", '', 12)
    pdf.cell(95, 7, f"{client.first_name} {client.last_name}", 0, 0, 'L')
    pdf.cell(95, 7, f"Invoice #: {invoice.invoice_number}", 0, 1, 'R')
    
    pdf.cell(95, 7, f"{client.email}", 0, 0, 'L')
    pdf.cell(95, 7, f"Issue Date: {invoice.issue_date.strftime('%Y-%m-%d')}", 0, 1, 'R')
    
    pdf.cell(95, 7, f"{client.phone}", 0, 0, 'L')
    pdf.cell(95, 7, f"Due Date: {invoice.due_date.strftime('%Y-%m-%d')}", 0, 1, 'R')
    pdf.ln(10)

    # Table Header
    pdf.set_fill_color(220, 220, 220)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(100, 10, 'Description', 1, 0, 'C', True)
    pdf.cell(30, 10, 'Quantity', 1, 0, 'C', True)
    pdf.cell(30, 10, 'Unit Price', 1, 0, 'C', True)
    pdf.cell(30, 10, 'Total', 1, 1, 'C', True)

    # Table Body (Invoice Items)
    pdf.set_font("Arial", '', 12)
    for item in invoice.items:
        pdf.cell(100, 10, item.description, 1, 0, 'L')
        pdf.cell(30, 10, str(item.quantity), 1, 0, 'R')
        pdf.cell(30, 10, f"{item.unit_price:.2f}", 1, 0, 'R')
        pdf.cell(30, 10, f"{(item.quantity * item.unit_price):.2f}", 1, 1, 'R')
    
    pdf.ln(5)

    # Total
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(160, 10, 'Total Amount:', 0, 0, 'R')
    pdf.cell(30, 10, f"KES {invoice.total_amount:.2f}", 1, 1, 'R')
    pdf.ln(10)
    
    # Status
    pdf.set_font("Arial", 'B', 16)
    status_text = f"Status: {invoice.status.upper()}"
    if invoice.status == 'paid':
         pdf.set_text_color(0, 128, 0) # Green
    elif invoice.status in ['sent', 'overdue']:
         pdf.set_text_color(255, 0, 0) # Red
    pdf.cell(0, 10, status_text, 0, 1, 'C')
    
    # Return PDF as bytes
    return pdf.output(dest='S').encode('latin-1')

def generate_password(length=10):
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(chars) for _ in range(length))

class ConfigWithScheduler(Config):
    SCHEDULER_API_ENABLED = True

app.config.from_object(ConfigWithScheduler)
scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()

@scheduler.task('cron', id='check_expired_subscriptions', hour=0)  # Runs daily at midnight
def check_expired_subscriptions():
    with app.app_context():
        today = datetime.utcnow().date()
        
        # Find clients whose expiry date is today or in the past AND who are still marked Active
        expired_clients = Client.query.filter(
            Client.subscription_expiry <= today, 
            Client.status == 'Active'
        ).all()

        if not expired_clients:
            current_app.logger.info("Scheduler: No active clients expired today.")
            return # No one to process

        for client in expired_clients:
            # Set client status to Inactive
            client.status = 'Inactive' 
            db.session.add(client)
            
            # Find the 'sent' invoice that is now overdue
            overdue_invoice = Invoice.query.filter(
                Invoice.client_id == client.id,
                Invoice.status == 'sent', # Find the invoice that was 'sent'
                db.func.date(Invoice.due_date) <= today
            ).order_by(Invoice.due_date.desc()).first()

            email_message = f"Hi {client.first_name}, your subscription has expired. Your account is now inactive. Please renew to continue accessing the gym."
            pdf_to_send = None
            pdf_filename = None
            subject = "Subscription Expired"

            if overdue_invoice:
                overdue_invoice.status = 'overdue' # Update status
                db.session.add(overdue_invoice)
                
                try:
                    pdf_to_send = create_invoice_pdf(overdue_invoice)
                    pdf_filename = f"Invoice_OVERDUE_{overdue_invoice.invoice_number}.pdf"
                    subject = "Subscription Expired - Invoice Overdue"
                    email_message = f"""
Hi {client.first_name},

Your subscription has expired, and your account is now inactive.
Your renewal invoice ({overdue_invoice.invoice_number}) is attached and is now considered overdue.

Please log in to your dashboard to make a payment and reactivate your account.

Regards,
FitFlow Gym
"""
                except Exception as e:
                    current_app.logger.error(f"Failed to generate overdue PDF for {client.id}: {e}")

            send_email(
                client.email,
                subject,
                email_message,
                pdf_data=pdf_to_send,
                pdf_filename=pdf_filename
            )
            current_app.logger.info(f"Processed expiry for client {client.id}. Status set to Inactive.")
        
        db.session.commit() # Commit all status changes and invoice updates

@scheduler.task('cron', id='send_monthly_report', day=1, hour=6)  # every 1st of the month at 6 AM
def send_monthly_report():
    with app.app_context():
        # Determine previous month
        today = datetime.utcnow()
        first_day_current_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        last_day_prev_month = first_day_current_month - timedelta(days=1)
        month = last_day_prev_month.month
        year = last_day_prev_month.year
        month_name = last_day_prev_month.strftime('%B %Y')

        # Fetch successful payments for previous month
        payments = Payment.query.filter(
            Payment.status == 'Success',
            extract('month', Payment.created_at) == month,
            extract('year', Payment.created_at) == year
        ).all()

        # Fetch expenses for previous month
        expenses = Expense.query.filter(
            extract('month', Expense.created_at) == month,
            extract('year', Expense.created_at) == year
        ).all()

        # Totals
        total_earnings = sum(p.amount for p in payments)
        total_expenses = sum(e.cost for e in expenses)
        net_revenue = total_earnings - total_expenses

        # Generate PDF report
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, f"Monthly Financial Report - {month_name}", ln=True, align="C")
        pdf.ln(5)

        # Payments Section
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, "Payments (Successful Only)", ln=True)
        pdf.set_font("Arial", '', 12)
        if payments:
            pdf.cell(50, 8, "Date", border=1)
            pdf.cell(50, 8, "Client", border=1)
            pdf.cell(50, 8, "Amount", border=1, ln=True)
            for p in payments:
                client_name = f"{p.client.first_name} {p.client.last_name}" if p.client else "Unknown"
                pdf.cell(50, 8, p.created_at.strftime('%d-%b-%Y'), border=1)
                pdf.cell(50, 8, client_name, border=1)
                pdf.cell(50, 8, f"KES {p.amount:.2f}", border=1, ln=True)
        else:
            pdf.cell(0, 8, "No successful payments recorded.", ln=True)
        pdf.ln(5)

        # Expenses Section
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, "Expenses", ln=True)
        pdf.set_font("Arial", '', 12)
        if expenses:
            pdf.cell(50, 8, "Date", border=1)
            pdf.cell(80, 8, "Description", border=1)
            pdf.cell(40, 8, "Cost", border=1, ln=True)
            for e in expenses:
                pdf.cell(50, 8, e.created_at.strftime('%d-%b-%Y'), border=1)
                pdf.cell(80, 8, e.description, border=1)
                pdf.cell(40, 8, f"KES {e.cost:.2f}", border=1, ln=True)
        else:
            pdf.cell(0, 8, "No expenses recorded.", ln=True)
        pdf.ln(10)

        # Summary
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 8, f"Total Earnings: KES {total_earnings:.2f}", ln=True)
        pdf.cell(0, 8, f"Total Expenses: KES {total_expenses:.2f}", ln=True)
        pdf.cell(0, 8, f"Net Revenue: KES {net_revenue:.2f}", ln=True)

        pdf_bytes = pdf.output(dest='S').encode('latin-1')

        # Send email to all admins with PDF attached
        admins = Admin.query.all()
        for admin in admins:
            send_email(
                to_email=admin.email,
                subject=f"Monthly Gym Financial Report - {month_name}",
                message=f"""
Hello {admin.name},

Attached is the financial report for {month_name}.

Summary:
Total Earnings (Successful payments only): KES {total_earnings:.2f}
Total Expenses: KES {total_expenses:.2f}
Net Revenue: KES {net_revenue:.2f}

Regards,
FitFlow Gym Management System
""",
                pdf_data=pdf_bytes,
                pdf_filename=f"Financial_Report_{month_name.replace(' ', '_')}.pdf"
            )
            current_app.logger.info(f"Sent monthly financial report to {admin.email}")


def generate_invoice_number():
    """Generates a unique invoice number."""
    timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
    random_part = secrets.token_hex(2).upper()
    return f"INV-{timestamp}-{random_part}"


@scheduler.task('cron', id='generate_renewal_invoices', hour=8) # Runs daily at 8 AM
def generate_renewal_invoices():
    """
    Generates invoices for clients whose subscriptions are expiring soon
    and emails the invoice to them.
    An invoice is created 7 days before the subscription expiry date.
    """
    with app.app_context():
        # Calculate the target date for expiry (7 days from now)
        renewal_date = (datetime.utcnow() + timedelta(days=7)).date()

        # Find clients whose subscription expires on the renewal_date
        clients_for_renewal = Client.query.filter(
            db.func.date(Client.subscription_expiry) == renewal_date,
            Client.subscription_id.isnot(None)
        ).all()

        for client in clients_for_renewal:
            # Check if an unpaid invoice for this renewal already exists
            existing_invoice = Invoice.query.filter(
                Invoice.client_id == client.id,
                Invoice.status.in_(['sent', 'overdue']),
                db.func.date(Invoice.due_date) == client.subscription_expiry.date()
            ).first()

            if existing_invoice:
                current_app.logger.info(f"Invoice already exists for client {client.id}. Skipping.")
                continue

            subscription = client.subscription
            
            # This check is good practice, though 'subscription_id.isnot(None)'
            # in the query above should already handle it.
            if not subscription:
                current_app.logger.warning(f"Client {client.id} has subscription_id but no subscription object. Skipping.")
                continue
                
            invoice = Invoice(
                client_id=client.id,
                invoice_number=generate_invoice_number(),
                issue_date=datetime.utcnow(),
                due_date=client.subscription_expiry,
                total_amount=subscription.price,
                status='sent'
            )
            
            invoice_item = InvoiceItem(
                invoice=invoice,
                description=f"{subscription.name} Subscription Renewal",
                quantity=1,
                unit_price=subscription.price
            )

            db.session.add(invoice)
            db.session.add(invoice_item)
            db.session.commit()

            # --- Send email notification with PDF invoice ---
            try:
                pdf_data = create_invoice_pdf(invoice)
                
                send_email(
                    to_email=client.email,
                    subject=f"Subscription Renewal Invoice - {invoice.invoice_number}",
                    message=f"""
Hi {client.first_name},

Your subscription for "{subscription.name}" is due for renewal soon.
Your subscription expires on: {client.subscription_expiry.strftime('%Y-%m-%d')}

Attached is your renewal invoice ({invoice.invoice_number}) for KES {invoice.total_amount:.2f}.

You can pay via M-PESA from your client dashboard.

Regards,
FitFlow Gym
""",
                    pdf_data=pdf_data,
                    pdf_filename=f"Invoice_{invoice.invoice_number}.pdf"
                )
                current_app.logger.info(f"Generated and EMAILED invoice {invoice.invoice_number} to {client.email}")
            
            except Exception as e:
                current_app.logger.error(f"Failed to generate or send invoice PDF for client {client.id}: {e}")


class ClientResource(Resource):
    @jwt_required()
    def patch(self, client_id):
        # Admin check
        # current_user_email = get_jwt_identity()
        # if not Admin.query.filter_by(email=current_user_email).first():
        #     return {"message": "Unauthorized access"}, 403

        client = Client.query.get(client_id)
        if not client:
            return {"message": "Client not found"}, 404

        data = request.get_json()

        # Update basic details
        client.first_name = data.get("first_name", client.first_name)
        client.last_name = data.get("last_name", client.last_name)
        client.email = data.get("email", client.email)
        client.phone = data.get("phone", client.phone)

        # Handle subscription change
        subscription_id = data.get("subscription_id")
        if subscription_id:
            subscription = Subscription.query.get(subscription_id)
            if subscription:
                client.subscription_id = subscription.id
                # Optionally, you could reset the expiry date here if needed
                # client.subscription_expiry = datetime.utcnow() + timedelta(days=subscription.duration_days)
            else:
                return {"message": "Subscription not found"}, 404
        elif subscription_id == '': # Handle un-assigning a subscription
            client.subscription_id = None
            client.subscription_expiry = None
            client.status = "Inactive"

        db.session.commit()
        
        # Return the full, updated client object
        return {
            "message": "Client updated successfully", 
            "client": {
                "id": client.id,
                "first_name": client.first_name,
                "last_name": client.last_name,
                "email": client.email,
                "phone": client.phone,
                "status": client.status,
                "subscription": client.subscription.name if client.subscription else None,
                "subscription_expiry": client.subscription_expiry.isoformat() if client.subscription_expiry else None,
            }
        }, 200

    @jwt_required()
    def delete(self, client_id):
        # Admin check
        current_user_email = get_jwt_identity()
        if not Admin.query.filter_by(email=current_user_email).first():
            return {"message": "Unauthorized access"}, 403

        client = Client.query.get(client_id)
        if not client:
            return {"message": "Client not found"}, 404
        
        db.session.delete(client)
        db.session.commit()
        return {"message": f"Client {client.first_name} {client.last_name} deleted successfully"}, 200


class ClientLogin(Resource):
    def post(self):
        data = request.get_json()
        email = data.get("email")
        password = data.get("password")

        user = Client.query.filter_by(email = email).first()
        if user and check_password(password, user.password_hash):
            token = create_access_token(
                identity=user.email,
                expires_delta=timedelta(days=7)  # Extend expiry to 7 days
            ) 
            return {
                "message": "Login successful",
                "access_token": token,
                "user": user.to_dict()
            }, 200

        return {"message": "Invalid email or password"}, 401

class DashboardResource(Resource):
    @jwt_required()
    def get(self):
        user_email = get_jwt_identity()
        user = Client.query.filter_by(email=user_email).first()

        if not user:
            return {"error": "User not found"}, 404

        # Get subscription
        subscription = user.subscription
        subscription_data = {
            "type": subscription.name if subscription else "None",
            "price": subscription.price if subscription else "N/A",
            "expiry": user.subscription_expiry.strftime("%d/%m/%Y") if user.subscription_expiry else "N/A"
        }

        # Get last payment
        last_payment = Payment.query.filter_by(client_id=user.id).order_by(Payment.created_at.desc()).first()
        payment_data = {
            "amount": last_payment.amount if last_payment else "N/A",
            "date": last_payment.created_at.strftime("%d/%m/%Y") if last_payment else "N/A",
            "method": last_payment.method if last_payment else "N/A"
        }

        return {
            "user": {
                "name": f"{user.first_name} {user.last_name}",
                "email": user.email,
                "phone": user.phone,
                "created_at": user.created_at.strftime("%d/%m/%Y")
            },
            "subscription": subscription_data,
            "last_payment": payment_data
        }, 200

class AdminLogin(Resource):
    def post(self):
        data = request.get_json()
        email = data.get("email")
        password = data.get("password")

        user = Admin.query.filter_by(email=email).first()
        if user and check_password(password, user.password_hash):
            token = create_access_token(
                identity=user.email,  
                # additional_claims={"role": "admin"},
                expires_delta=timedelta(days=7)
            )         
            return {
                "message": "Login successful",
                "access_token": token,
                "user": user.to_dict()
            }, 200
        
        return {
            "message": "Invalid email or password"
        }, 401 


class Logout(Resource):
    @jwt_required()
    def post(self):
        jti = get_jwt()["jti"]
        blacklist.add(jti)
        return {"message": "Logged out successfully"}, 200
    

class AddClient(Resource):
    @jwt_required()
    def post(self):
        try:
            # Get current admin user
            current_user_email = get_jwt_identity()
            admin = Admin.query.filter_by(email=current_user_email).first()
            if not admin:
                return {"error": "Unauthorized, admin access required"}, 403
            
            # Parse request data
            data = request.get_json()
            if not data:
                return {"error": "No data provided"}, 400
            
            # Validate required fields
            required_fields = ['first_name', 'last_name', 'email', 'phone']
            missing = [field for field in required_fields if field not in data or not data[field]]
            if missing:
                return {'error': f'Missing required fields: {", ".join(missing)}'}, 400
            
            # Check email format
            if '@' not in data['email']:
                return {'error': 'Invalid email format'}, 400
                
            # Check phone format
            if not isinstance(data['phone'], str) or not data['phone'].isdigit() or len(data['phone']) < 10:
                return {'error': 'Phone number must be at least 10 digits'}, 400
                
            # Check if email/phone exists
            if Client.query.filter_by(email=data['email']).first():
                return {'error': 'Email already in use'}, 400
            if Client.query.filter_by(phone=data['phone']).first():
                return {'error': 'Phone number already in use'}, 400
            
            # Handle subscription if provided
            subscription = None
            subscription_expiry = None
            if 'subscription' in data and data['subscription']:
                subscription = Subscription.query.filter_by(name=data['subscription']).first()
                if not subscription:
                    return {'error': 'Invalid subscription name'}, 400
                
                subscription_expiry = datetime.utcnow() + timedelta(days=subscription.duration_days)
            
            # Generate a random default password
            random_password = generate_password()
            
            # Create new client
            new_client = Client(
                first_name=data['first_name'],
                last_name=data['last_name'],
                email=data['email'],
                phone=data['phone'],
                password_hash=hash_password(random_password),
                status=data.get('status', 'Active'),
                subscription=subscription,
                subscription_expiry=subscription_expiry
            )

            db.session.add(new_client)
            db.session.commit()

            # Create reset token and link
            reset_token = create_access_token(identity=new_client.email, expires_delta=timedelta(hours=1))
            reset_link = f"http://localhost:3000/reset-password?token={reset_token}"

            # Send welcome email
            send_email(
                to_email=new_client.email,
                subject="Welcome to FitFlow - Set Your Password",
                message=f"""
                Hi {new_client.first_name},

                🎉 Welcome to FitFlow! Your account has been created.

                👉 Temporary password: {random_password}

                Please use this temporary password to log in.  
                For security, we recommend you set your own password using the link below (expires in 1 hour):

                {reset_link}

                Thank you for joining us!

                Kind regards,
                FitFlow Management
                """
            )
            return {
                "message": "Client added successfully",
                "client": new_client.to_dict(),
            }, 201

        except Exception as e:
            db.session.rollback()
            return {"error": str(e)}, 500

class AddExpense(Resource):
    @jwt_required()
    def post(self):
        current_user = get_jwt_identity()
        print("JWT Identity:", current_user) 

        admin = Admin.query.filter_by(email=current_user).first()
        if not admin:
            print("Unauthorized attempt by:", current_user)
            return {"error": "Unauthorized, admin access required"}, 403

        data = request.get_json()
        print("Incoming expense data:", data)  # 👈 Debug what React sends

        try:
            cost_str = data.get("cost")
            if cost_str is None:
                return {"error": "Cost is required"}, 400
            cost = int(cost_str)

            new_expense = Expense(
                expense=data.get("expense"),
                cost=cost,
            ) 

            db.session.add(new_expense)
            db.session.commit()

            print("✅ Expense added:", new_expense.expense, new_expense.cost)
            return {"message": "Expense added successfully!"}, 201

        except Exception as e:
            db.session.rollback()
            print("❌ Error adding expense:", str(e))
            return {"error": f"Failed to add expense: {str(e)}"}, 500
        
class Subscriptions(Resource):
    def get(self):
        subs = Subscription.query.all()
        return [plan.to_dict() for plan in subs]

class MarkCashPayment(Resource):
    @jwt_required()
    def post(self):
        try:
            # --- Authenticate admin ---
            current_user = get_jwt_identity()
            admin = Admin.query.filter_by(email=current_user).first()
            if not admin:
                return {"error": "Unauthorized, admin access required"}, 403

            # --- Get data from request ---
            data = request.get_json()
            if not data:
                return {"error": "No JSON data provided"}, 400
                
            current_app.logger.info(f"Received payment data: {data}")
            
            client_email = data.get("email")
            subscription_name = data.get("subscription")
            payment_date_str = data.get("payment_date") 

            if not client_email or not subscription_name:
                return {"error": "Missing required fields (email, subscription)"}, 400

            # --- Find client ---
            client = Client.query.filter_by(email=client_email).first()
            if not client:
                return {"error": f"Client with email '{client_email}' not found"}, 404

            # --- Find subscription ---
            subscription = Subscription.query.filter_by(name=subscription_name).first()
            if not subscription:
                return {"error": f"Subscription plan '{subscription_name}' not found"}, 404

            # --- Resolve effective payment date ---
            effective_date = datetime.utcnow()
            if payment_date_str:
                try:
                    effective_date = datetime.strptime(payment_date_str, "%Y-%m-%d")
                except ValueError:
                    return {"error": "Invalid payment_date format. Use YYYY-MM-DD"}, 400

            # --- Calculate new expiry date ---
            amount_to_record = float(subscription.price)
            today = effective_date.date()
            
            current_app.logger.info(f"Processing payment for client {client_email}, subscription {subscription_name}")
            current_app.logger.info(f"Current client expiry: {client.subscription_expiry}, Today: {today}")
            
            # Check if client has an active subscription
            if client.subscription_expiry:
                current_expiry = client.subscription_expiry.date()
                current_app.logger.info(f"Current expiry date: {current_expiry}")
                
                # If current expiry is in the future, extend from there
                if current_expiry >= today:
                    base_dt = client.subscription_expiry
                    current_app.logger.info(f"Extending from current expiry: {base_dt}")
                else:
                    # Subscription expired, start fresh from today
                    base_dt = datetime.combine(today, datetime.min.time())
                    current_app.logger.info(f"Subscription expired, starting fresh from: {base_dt}")
            else:
                # No existing subscription, start fresh
                base_dt = datetime.combine(today, datetime.min.time())
                current_app.logger.info(f"No existing subscription, starting from: {base_dt}")
            
            # Calculate new expiry
            new_expiry = base_dt + timedelta(days=subscription.duration_days)
            current_app.logger.info(f"New expiry date: {new_expiry}")

            # --- Record payment ---
            payment = Payment(
                client_id=client.id,
                subscription_id=subscription.id,
                amount=amount_to_record,
                phone_number=client.phone,
                status="Success",
                method="Cash",
                created_at=effective_date
            )
            db.session.add(payment)
            db.session.flush()  # Get payment ID for invoice
            current_app.logger.info(f"Payment recorded with ID: {payment.id}")

            # --- Update client subscription ---
            client.subscription_id = subscription.id
            client.subscription_expiry = new_expiry
            client.status = "Active"
            client.last_payment_date = effective_date
            client.last_payment_amount = amount_to_record
            
            current_app.logger.info(f"Client subscription updated: {client.subscription_id}, Expiry: {client.subscription_expiry}")

            # --- Generate invoice number ---
            try:
                invoice_number = generate_invoice_number()
                current_app.logger.info(f"Generated invoice number: {invoice_number}")
            except Exception as inv_err:
                current_app.logger.error(f"Error generating invoice number: {inv_err}")
                invoice_number = f"INV-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

            # --- Create invoice ---
            paid_invoice = Invoice(
                client_id=client.id,
                invoice_number=invoice_number,
                issue_date=effective_date,
                due_date=effective_date,
                total_amount=amount_to_record,
                status="paid",
                payment_id=payment.id
            )
            db.session.add(paid_invoice)
            db.session.flush()
            current_app.logger.info(f"Invoice created with ID: {paid_invoice.id}")

            # --- Create invoice item ---
            paid_item = InvoiceItem(
                invoice_id=paid_invoice.id,
                description=f"{subscription.name} Subscription ({subscription.duration_days} days)",
                quantity=1,
                unit_price=subscription.price
            )
            db.session.add(paid_item)
            current_app.logger.info(f"Invoice item created")

            # --- Send email with PDF (non-blocking) ---
            try:
                pdf_data = create_invoice_pdf(paid_invoice)
                send_email(
                    to_email=client.email,
                    subject=f"Payment Receipt - Invoice {paid_invoice.invoice_number}",
                    message=f"""Hi {client.first_name},

We have recorded your cash payment of KES {amount_to_record:.2f} for the {subscription.name} plan.
Your new subscription expiry date is {new_expiry.strftime('%d-%m-%Y')}.

Your payment receipt is attached.

Thank you!
FitFlow Gym""",
                    pdf_data=pdf_data,
                    pdf_filename=f"Receipt_{paid_invoice.invoice_number}.pdf"
                )
                current_app.logger.info(f"Email sent to {client.email}")
            except Exception as email_err:
                current_app.logger.error(f"Cash payment email failed: {email_err}")
                # Don't fail the whole transaction if email fails

            # --- Commit transaction ---
            db.session.commit()
            current_app.logger.info("Transaction committed successfully")

            # --- Construct response ---
            response_payload = {
                "client": f"{client.first_name} {client.last_name}",
                "subscription": subscription.name,
                "amount": amount_to_record,
                "payment_status": "Success",
                "payment_date": effective_date.strftime("%Y-%m-%d"),
                "new_expiry": new_expiry.strftime("%Y-%m-%d"),
                "client_status": client.status,
                "invoice_number": paid_invoice.invoice_number,
                "note": f"Payment settled. Receipt {paid_invoice.invoice_number} generated."
            }

            return {"message": "Payment processed", **response_payload}, 200

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error in MarkCashPayment: {str(e)}", exc_info=True)
            return {"error": f"An error occurred while processing payment: {str(e)}"}, 500
        
class SelectSubscription(Resource):
    @jwt_required()
    def post(self):
        current_user = get_jwt_identity()
        client = Client.query.filter_by(email=current_user).first()
        if not client:
            return {"error": "Client not found"}, 404

        data = request.get_json()
        subscription_name = data.get("subscription")

        if not subscription_name:
            return {"error": "Subscription name is required"}, 400

        subscription = Subscription.query.filter_by(name=subscription_name).first()
        if not subscription:
            return {"error": "Subscription plan not found"}, 404

        client.subscription = subscription
        client.subscription_expiry = datetime.utcnow() + timedelta(days=subscription.duration_days)

        db.session.commit()

        return {
            "message": f"Successfully subscribed to {subscription.name}.",
            "subscription_expiry": client.subscription_expiry.isoformat()
        }, 200


class AddAdmin(Resource):
    def post(self):
        data = request.get_json()
        email = data.get("email")
        password = data.get("password")
        name = data.get("name")
        secret_code = data.get("secret_code")

        # It's better to load secrets from environment variables
        required_secret = os.environ.get("ADMIN_CREATION_SECRET", "SUPER_SECRET")

        if not all([email, password, name, secret_code]):
            return {"error": "All fields, including the secret code, are required"}, 400

        if secret_code != required_secret:
            return {"message": "Invalid secret code."}, 403

        existing = Admin.query.filter_by(email=email).first()
        if existing:
            return {"error": "Admin with this email already exists."}, 409

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new = Admin(
            email=email,
            name=name,
            password_hash=hashed_password
        )

        db.session.add(new)
        db.session.commit()

        return {"message": "Admin successfully created"}, 201
    

class CreateAdmin(Resource):
    def post(self):
        if Admin.query.count() > 0:
            return {"message": "Initial admin already created. Use the protected endpoint."}, 403

        data = request.get_json()
        if not data.get("email") or not data.get("password") or not data.get("name"):
            return {"error": "Email, password, and name are required"}, 400

        hashed_password = bcrypt.generate_password_hash(data["password"]).decode('utf-8')
        new_admin = Admin(email=data["email"], name=data["name"], password_hash=hashed_password)
        db.session.add(new_admin)
        db.session.commit()
        return {"message": "Initial admin created successfully"}, 201
    
    
class GetClients(Resource):
    @jwt_required()
    def get(self):
        try:
            current_user = get_jwt_identity()
            admin = Admin.query.filter_by(email=current_user).first()

            if not admin:
                return {"error": "Unauthorized, admin access required"}, 403

            search_term = request.args.get('search', default='', type=str)
            status_filter = request.args.get('status', default=None, type=str)

            query = Client.query

            # Apply search filter
            if search_term:
                search = f"%{search_term}%"
                query = query.filter(
                    db.or_(
                        Client.first_name.ilike(search),
                        Client.last_name.ilike(search),
                        Client.email.ilike(search),
                        Client.phone.ilike(search)
                    )
                )

            # Apply status filter
            if status_filter:
                query = query.filter(Client.status.ilike(status_filter))

            clients = query.order_by(Client.first_name.asc()).all()

  
            return {
                "clients": [{
                    "id": c.id,
                    "first_name": c.first_name,
                    "last_name": c.last_name,
                    "email": c.email,
                    "phone": c.phone,
                    "status": c.status,
                    "subscription": c.subscription.name if c.subscription else None,  # Fixed
                    "subscription_id": c.subscription.id if c.subscription else None,  # Added if needed
                    "subscription_expiry": c.subscription_expiry.isoformat() if c.subscription_expiry else None,
                "created_at": c.created_at.isoformat() if c.created_at else None,  # Added for completeness
                } for c in clients]
            }, 200

        except Exception as e:
            current_app.logger.error(f"Error fetching clients: {str(e)}")
            return {"error": "Failed to fetch clients"}, 500
        
class GetExpense(Resource):
    @jwt_required()
    def get(self):
        current_user = get_jwt_identity()
        admin = Admin.query.filter_by(email=current_user).first()

        if not admin:
            return {"error": "Unauthorized."}, 403
        
        expense_name = request.args.get("expense")
        expense = Expense.query.filter_by(expense=expense_name).first()
        if not expense:
            return {"error": "Expense is not found"}, 404
    
        return {
            "id": expense.id,
            "expense": expense.expense,
            "cost": expense.cost,
            "created_at": expense.created_at.isoformat()
        }, 200  

class ClientDashboard(Resource):
    @jwt_required()
    def get(self):
        current_user_email = get_jwt_identity()
        client = Client.query.filter_by(email=current_user_email).first()

        if not client:
            return {"error": "Client not found"}, 404

        return {
            "client": {
                "id": client.id,
                "first_name": client.first_name,
                "last_name": client.last_name,
                "email": client.email,
                "phone": client.phone,
                "subscription": client.subscription.name if client.subscription else None,
                "subscription_price": client.subscription.price if client.subscription else None,
                "subscription_expiry": client.subscription_expiry.isoformat() if client.subscription_expiry else None,
                "created_at": client.created_at.isoformat() if client.created_at else None,
            },
            "payment_instructions": "To renew your subscription, please go to the payment section and use M-PESA. This feature is coming soon."
        }, 200


class GetAllExpenses(Resource):
    @jwt_required()
    def get(self):
        try:
            current_user = get_jwt_identity()
            admin = Admin.query.filter_by(email=current_user).first()

            if not admin:
                return {"error": "Unauthorized, admin access required"}, 403

            # Get optional month/year filters from query params
            month = request.args.get('month', type=int)
            year = request.args.get('year', type=int, default=datetime.utcnow().year)
            
            # Base query
            query = Expense.query.order_by(Expense.created_at.desc())
            
            # Apply filters if provided
            if month:
                query = query.filter(
                    extract('month', Expense.created_at) == month,
                    extract('year', Expense.created_at) == year
                )
            else:
                # Filter by year only if no month specified
                query = query.filter(
                    extract('year', Expense.created_at) == year
                )

            expenses = query.all()
            
            # Calculate total
            total = sum(exp.cost for exp in expenses)
            
            return {
                "expenses": [
                    {
                        "id": e.id,
                        "expense": e.expense,
                        "cost": e.cost,
                        "created_at": e.created_at.isoformat(),
                    }
                    for e in expenses
                ],
                "total": total,
                "count": len(expenses),
                "month": month,
                "year": year
            }, 200
            
        except Exception as e:
            current_app.logger.error(f"Error fetching expenses: {str(e)}")
            return {"error": "Failed to fetch expenses"}, 500


class GetPayments(Resource):
    @jwt_required()
    def get(self):
        client_email = get_jwt_identity()
        client = Client.query.filter_by(email=client_email).first()
        if not client:
            return {"error": "Client not found"}, 404

        payments = Payment.query.filter_by(client_id=client.id).all()
        return [payment.to_dict() for payment in payments], 200


class MpesaInitiate(Resource):
    @jwt_required()
    def post(self):
        data = request.get_json()
        phone_number = data.get("phone_number")
        plan_name = data.get("plan_name")

        if not phone_number or not plan_name:
            return {"error": "phone_number and plan_name are required"}, 400

        # Get user making request
        email = get_jwt_identity()
        user = Client.query.filter_by(email=email).first()
        if not user:
            return {"error": "User not found"}, 404

        # Get subscription plan
        plan = Subscription.query.filter_by(name=plan_name).first()
        if not plan:
            return {"error": "Subscription plan not found"}, 404

        # Initiate STK Push using mpesa.py
        try:
            response = lipa_na_mpesa(phone_number, plan.price)
        except Exception as e:

            current_app.logger.error(f"STK Push error: {e}")
            return {"error": "Failed to initiate M-PESA STK Push"}, 500

        # Safely extract required values
        response_code = response.get("ResponseCode")
        checkout_id = response.get("CheckoutRequestID")

        if response_code != "0" or checkout_id is None:
            return {"error": "Failed to initiate M-PESA STK Push", "details": response}, 400

        # Record payment as pending
        payment = Payment(
            client_id=user.id,
            subscription_id=plan.id,
            amount=plan.price,
            phone_number=phone_number,
            method="M-PESA",
            status="Pending",
            checkout_response=checkout_id
        )
        db.session.add(payment)
        db.session.commit()

        return {
            "message": "STK Push sent. Check your phone to complete the payment.",
            "checkout_id": checkout_id
        }, 200

class DashBoard(Resource):
    @jwt_required()
    def get(self):
        # Get JWT claims
        # claims = get_jwt()
        # if claims.get("role") != "admin":
        #     return {"error": "Admin access only"}, 403

        # Get current admin email
        admin_email = get_jwt_identity()
        admin = Admin.query.filter_by(email=admin_email).first()
        if not admin:
            return {"error": "Admin not found"}, 404

        now = datetime.utcnow()
        month = now.month
        year = now.year

        # Dashboard counts and sums
        clients_count = Client.query.count()

        expenses_total = (
            db.session.query(func.sum(Expense.cost))
            .filter(extract("month", Expense.created_at) == month)
            .filter(extract("year", Expense.created_at) == year)
            .scalar() or 0
        )

        payments_total = (
            db.session.query(func.sum(Payment.amount))
            .filter(Payment.status == "Success")
            .filter(extract("month", Payment.created_at) == month)
            .filter(extract("year", Payment.created_at) == year)
            .scalar() or 0
        )


        # Subscription info
        subscriptions = (
            db.session.query(
                Subscription.id,
                Subscription.name,
                Subscription.price,
                func.count(Client.id).label("client_count")
            )
            .outerjoin(Client, Client.subscription_id == Subscription.id)
            .filter(
                (Client.created_at != None) &  # Only consider clients with created_at
                (extract("month", Client.created_at) == month) &
                (extract("year", Client.created_at) == year)
            )
            .group_by(Subscription.id)
            .all()
        )

        # Build response
        return {
            "clients": clients_count,
            "expenses": round(expenses_total, 2),
            "payments": round(payments_total, 2),
            "subscriptions": [
                {
                    "id": s.id,
                    "name": s.name,
                    "price": s.price,
                    "clients": s.client_count
                }
                for s in subscriptions
            ]
        }, 200


class AddMpesaPaymentNCallback(Resource):
    def post(self):
        data = request.get_json()
        current_app.logger.info(f"M-PESA Callback received: {data}")

        body = data.get("Body", {}).get("stkCallback", {})
        checkout_id = body.get("CheckoutRequestID")
        result_code = body.get("ResultCode")

        payment = Payment.query.filter_by(checkout_response=checkout_id).first()
        if not payment:
            current_app.logger.error(f"Payment with CheckoutID {checkout_id} not found.")
            return {"error": "Payment record not found"}, 404

        if result_code != 0:
            payment.status = "Failed"
            payment.method = "M-PESA"
            payment.checkout_response = None
            payment.mpesa_receipt = None
            payment.phone_number = None
            db.session.commit()
            return {"message": "Payment failed"}, 400

        # Process CallbackMetadata
        callback_metadata = body.get("CallbackMetadata", {}).get("Item", [])
        receipt, amount_paid, phone = None, None, None
        for item in callback_metadata:
            if item["Name"] == "MpesaReceiptNumber":
                receipt = item["Value"]
            elif item["Name"] == "Amount":
                amount_paid = float(item["Value"])
            elif item["Name"] == "PhoneNumber":
                phone = item["Value"]

        # Update payment record
        payment.mpesa_receipt = receipt
        payment.status = "Success"
        payment.amount = amount_paid or payment.amount
        payment.phone_number = phone

        # Update client's subscription
        client = payment.client
        plan = payment.subscription

        today = datetime.utcnow()
        if not client.subscription_expiry or client.subscription_expiry < today:
            client.subscription_expiry = today + timedelta(days=plan.duration_days)
        else:
            client.subscription_expiry += timedelta(days=plan.duration_days)
        client.subscription_id = plan.id
        client.status = "Active"
        client.last_payment_date = today
        client.last_payment_amount = payment.amount

        # Create invoice
        invoice = Invoice(
            client_id=client.id,
            invoice_number=generate_invoice_number(),
            issue_date=today,
            due_date=today,
            total_amount=payment.amount,
            status='paid'
        )
        item = InvoiceItem(
            invoice=invoice,
            description=f"{plan.name} Subscription",
            quantity=1,
            unit_price=payment.amount
        )
        db.session.add(invoice)
        db.session.add(item)
        db.session.commit()

        try:
            pdf_data = create_invoice_pdf(invoice)
            send_email(
                to_email=client.email,
                subject=f"Payment Receipt - {invoice.invoice_number}",
                message=f"Hi {client.first_name},\nYour payment of KES {payment.amount:.2f} for {plan.name} was successful.\nMpesa Receipt: {receipt}\nExpiry: {client.subscription_expiry.strftime('%d-%m-%Y')}",
                pdf_data=pdf_data,
                pdf_filename=f"Receipt_{invoice.invoice_number}.pdf"
            )
        except Exception as e:
            current_app.logger.error(f"Failed to send receipt email: {e}")

        return {"message": "Payment processed and subscription updated"}, 200

class AdminUpdate(Resource):
    @jwt_required()
    def patch(self):
        data = request.get_json()
        current_user_email = get_jwt_identity()

        # Fetch admin
        admin = Admin.query.filter_by(email=current_user_email).first()
        if not admin:
            return {"message": "Admin not found"}, 404

        # Update name/email if provided
        if data.get("name"):
            admin.name = data["name"]

        if data.get("email"):
            # Optional: check for unique email before updating
            existing = Admin.query.filter_by(email=data["email"]).first()
            if existing and existing.id != admin.id:
                return {"message": "Email already in use"}, 400
            admin.email = data["email"]

        # Update password if old_password and new_password are provided
        if data.get("old_password") and data.get("new_password"):
            try:
                if not check_password(admin.password_hash, data["old_password"]):
                    return {"message": "Old password is incorrect"}, 400
            except ValueError:
                # Catch invalid hash
                return {"message": "Stored password hash is invalid. Please reset password manually."}, 500

            # Set new password
            admin.password_hash = hash_password(data["new_password"])

        # Commit changes
        try:
            db.session.commit()
        except Exception as e:
            current_app.logger.error(f"Error updating admin profile: {e}")
            db.session.rollback()
            return {"message": "Failed to update profile"}, 500

        return {"message": "Profile updated successfully", "admin": admin.to_dict()}, 200 
# ---------------- FORGOT PASSWORD ---------------- #

class ForgotPassword(Resource):
    def post(self):
        data = request.get_json()
        email = data.get("email")

        if not email:
            return {"error": "Email is required"}, 400

        user = Client.query.filter_by(email=email).first()
        if not user:
            return {"message": "If that email exists, a reset link has been sent."}, 200  # Don't leak info

        # Generate a reset token (30 mins expiry)
        reset_token = create_access_token(identity=user.email, expires_delta=timedelta(minutes=30))
        reset_link = f"http://localhost:3000/reset-password?token={reset_token}"

        # Send email
        send_email(
            to_email=user.email,
            subject="Password Reset - FitFlow",
            message=f"""
Hello {user.first_name},

We received a request to reset your password.  
👉 Click the link below to set a new password (expires in 30 minutes):

{reset_link}

If you didn’t request this, please ignore this email.

Kind regards,  
FitFlow Team
"""
        )

        return {"message": "If the email exists, a reset link has been sent."}, 200


class ResetPasswordConfirm(Resource):
    @jwt_required()  # token from reset link
    def post(self):
        identity = get_jwt_identity()
        user = Client.query.filter_by(email=identity).first()

        if not user:
            return {"error": "User not found"}, 404

        data = request.get_json()
        new_password = data.get("new_password")
        if not new_password:
            return {"error": "New password is required"}, 400

        # Update password
        user.password_hash = bcrypt.generate_password_hash(new_password).decode('utf-8')
        db.session.commit()

        return {"message": "Password reset successful! You can now log in with your new password."}, 200

class AdminDetails(Resource):
    @jwt_required()
    def get(self):
        """
        Fetches the details for the currently authenticated admin.
        """
        current_user_email = get_jwt_identity()
        admin = Admin.query.filter_by(email=current_user_email).first()

        if not admin:
            return {"message": "Admin not found"}, 404
        
        return {"admin": admin.to_dict()}, 200

class InvoiceList(Resource):
    @jwt_required()
    def get(self):
        """
        Fetches invoices for the currently authenticated client.
        """
        current_user_email = get_jwt_identity()
        client = Client.query.filter_by(email=current_user_email).first()

        if not client:
            return {"error": "Client not found"}, 404

        invoices = Invoice.query.filter_by(client_id=client.id).order_by(Invoice.issue_date.desc()).all()
        
        return {
            "invoices": [
                invoice.to_dict() for invoice in invoices
            ]
        }, 200



api.add_resource(ForgotPassword, "/forgot-password")
api.add_resource(ResetPasswordConfirm, "/reset-password")
api.add_resource(AdminUpdate, "/admin/update")
api.add_resource(MpesaInitiate, '/start/payment') 
api.add_resource(AddMpesaPaymentNCallback, '/callback')
api.add_resource(CreateAdmin, '/admin/create') 
api.add_resource(ClientDashboard, '/dashboard/client')
api.add_resource(ClientLogin, '/client/login')
api.add_resource(AdminLogin, '/admin/login')
api.add_resource(AddAdmin, '/add/admin') 
api.add_resource(Logout, '/logout')
api.add_resource(AddClient, '/addClient')
api.add_resource(AddExpense,'/addExpense' )
api.add_resource(MarkCashPayment, '/markCashPayment')
api.add_resource(SelectSubscription, '/selectSubscription')
api.add_resource(GetClients, '/clients')
api.add_resource(GetExpense, '/getExpense')
api.add_resource(GetAllExpenses, '/expenses')
api.add_resource(Subscriptions, '/subscriptions')
api.add_resource(ClientResource, "/clients/<int:client_id>")
api.add_resource(GetPayments, "/client/payments")
api.add_resource(DashBoard, "/dashboard") 
api.add_resource(AdminDetails, "/admin/details")
api.add_resource(InvoiceList, "/client/invoices")



if __name__ == '__main__':
    app.run(port=5000)