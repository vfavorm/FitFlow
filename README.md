# FitFlow

**FitFlow** is a web-based gym management application built with **Flask** (backend) and **React** (frontend). It streamlines gym operations by offering secure authentication, subscription management, financial tracking, and **M-PESA payment integration** for clients and administrators.

## Problem

Gyms often struggle with:  

- Managing client access and subscriptions.  
- Offering secure login/logout functionality for clients and admins.  
- Tracking payments and finances efficiently.  

Without a centralized system, these tasks become **inefficient** and **error-prone**, impacting client experience and administrative workflow.  

---

## Solution

**FitFlow** provides a centralized platform that simplifies gym operations:  

- **JWT-based authentication** for clients and admins.  
- **Subscription management** and expiry tracking.  
- **M-PESA integration** for seamless payment.  
- Expense and revenue tracking for better financial planning.  
- Automated notifications for subscription status.  
- Role-based access: **Admins** manage accounts, payments, and finances; **clients** manage subscriptions and payments.  

---

## Features

### Clients Can:

- Log in securely.  
- Select and manage subscription plans.  
- Pay for subscriptions via **M-PESA**.  
- Receive email notifications when subscriptions end.  

### Admins Can:

- Add and manage client accounts.  
- Track and record payments, including **cash payments**.  
- Update client subscription details.  
- Log gym expenses and compare against revenue.  
- Access additional admin routes and dashboards.  

---

## Technologies

- **Frontend:** React.js, Axios, CSS Modules  
- **Backend:** Flask, Flask-RESTful, Flask-JWT-Extended, Flask-CORS, Flask-Migrate  
- **Database:** SQLite (via SQLAlchemy ORM)  
- **Payments:** Safaricom Daraja **M-PESA API**  
- **Email/SMS:** SMTP  
- **Others:** JWT authentication, secure token management  
