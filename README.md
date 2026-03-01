# 🏥 MediVista – Hospital Management System

📌 Project Overview

MediVista is a role-based Hospital Management System developed using Streamlit, Python, SQLite, and Plotly. The system is designed to automate hospital operations, improve staff coordination, and provide real-time analytics for management. It replaces manual processes with a secure, centralized digital workflow.

The application follows a structured three-layer architecture consisting of:

Presentation Layer (User Interface)

Application Logic Layer (Business Rules & Processing)

Data Layer (SQLite Database)

This layered design ensures scalability, security, and maintainability.

🎯 Core Objectives


The main objective of MediVista is to:

Digitize appointment management

Provide secure role-based access control

Enable real-time revenue tracking

Improve patient–doctor communication

Centralize hospital data in one platform

Provide graphical insights for decision-making

👥 System Modules


👑 Admin Module

The Admin has full control over the system and manages hospital operations.

📖 Description

The admin dashboard provides real-time analytics and complete system management capabilities. It allows staff registration, monitoring hospital performance, and resolving patient queries.

🔹 Features

Add Doctors with shift timings

Add Nurses and allocate them to specific doctors

Register Receptionists

View total revenue

View total visits

View total doctors & nurses

Daily revenue graph visualization

Daily patient visit graph

View & resolve patient queries

Download appointment reports (CSV)



👩‍💼 Receptionist Module

The Receptionist handles patient registration and appointment booking.

📖 Description

This module streamlines front-desk operations. Appointments are booked using a structured 20-minute slot logic to maintain scheduling discipline.

🔹 Features

Register new patients

Select patient blood group

Book appointment

Select doctor

Choose 20-minute time slot

Add payment amount

View booked appointments



👨‍⚕ Doctor Module

The Doctor module provides access to assigned appointments and patient queries.

📖 Description

Doctors can monitor their schedules and respond to patient queries, improving medical workflow efficiency.

🔹 Features

View assigned appointments

View appointment date and slot

Access patient queries

Check shift timings



👩‍⚕ Nurse Module

The Nurse module ensures better coordination within hospital staff.

📖 Description

Nurses can view their assigned doctor and shift timings, ensuring clarity in task delegation.

🔹 Features

View allocated doctor

View shift schedule

Role-based limited access



👤 Patient Module

The Patient module enhances communication and transparency.

📖 Description

Patients can securely register, book appointments, and communicate with doctors or hospital management through a structured query system.

🔹 Features

Self-registration

Secure login

View appointments

Send query to Doctor

Send query to Management

Track query status (Pending / Resolved)



📊 Dashboard & Analytics

The Admin dashboard provides real-time hospital insights.

🔹 Analytics Includes

Total Revenue

Total Visits

Total Doctors

Total Nurses

Daily Revenue Graph

Daily Patient Visits Graph

Graphs are built using Plotly visualization engine.



🏗 System Architecture

MediVista follows a three-layer architecture:

1️⃣ Presentation Layer

Multi-role user interfaces

Role-Based Access Control

2️⃣ Application Logic Layer

Appointment management

Slot scheduling logic (20 mins)

Nurse allocation

Query handling system

Analytics engine

3️⃣ Data Layer

SQLite database

Stores Users, Doctors, Nurses, Patients, Appointments, Queries

🛠 Technologies Used

Python (Backend Logic)

Streamlit (Frontend Interface)

SQLite (Database)

Plotly (Visualization)

Hashlib (Password Security)



🔐 Login Credentials & User Roles

MediVista follows a role-based authentication system, where each user logs in according to their assigned role. Every role has different access permissions and functionalities.

👑 Admin Login

The Admin has full system control and manages all hospital operations.

🔑 Default Credentials

Email:

admin@admin.com

Password:

Admin@123
👨‍💼 Admin Capabilities

Add Doctors with shift timings

Add Nurses and allocate them to doctors

Register Receptionists

View dashboard analytics (Revenue & Visits)

Download appointment reports

View and resolve patient queries

👨‍⚕ Doctor Login

Doctors are registered by the Admin.
When a doctor is added, the system automatically generates login credentials.

🔑 Login Process

Email: Doctor email entered by Admin

Password: Auto-generated and shown during registration

🩺 Doctor Capabilities

View assigned appointments

View appointment slots and dates

Access patient queries

Check shift timings

👩‍⚕ Nurse Login

Nurses are also registered by the Admin and assigned to a specific doctor.

🔑 Login Process

Email: Nurse email entered by Admin

Password: Auto-generated during registration

🏥 Nurse Capabilities

View allocated doctor

View shift schedule

Limited role-based access

👩‍💼 Receptionist Login

Receptionists are registered by the Admin.

🔑 Login Process

Email: Receptionist email entered by Admin

Password: Auto-generated during registration

📋 Receptionist Capabilities

Register new patients

Select blood group

Book appointments

Choose 20-minute time slots

Add payment amount

View appointment list

👤 Patient Login

Patients can self-register using the Register option.

🔑 Login Process

Register using email and password

Use same credentials to login

🧑‍⚕ Patient Capabilities

View appointments

Send query to Doctor

Send query to Management

Track query status (Pending / Resolved)




🔐 Security Features

SHA-256 password hashing

Role-based authentication

Unique email validation

Controlled database transactions
