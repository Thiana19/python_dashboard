# Perfume Management System

## Overview
The **Perfume Management System** is a **Django-based** web application designed to streamline **formulation management, compliance checks, inventory tracking, and quality assurance** for perfume production. It features **role-based access control** to manage user roles and ensure seamless collaboration between R&D, QA, and Managers.

## Features
✅ **User Management** – Login, role-based dashboards, and admin controls.  
✅ **Formulation Management** – Add, edit, and validate perfume formulations.  
✅ **Compliance Checker** – Automated ingredient validation for regulatory compliance.  
✅ **Inventory Management** – Track ingredient stock levels and set reorder thresholds.  
✅ **Dashboard & Reports** – Visual analytics for Managers.  
✅ **Quality Assurance** – Review and approve/reject formulations.  

---

## **Modules & Navigation Structure**
### **1. User Management Module**
- **Purpose:** Manage user roles and access control.
- **Pages:**
  - **Login Page:** `/login/`
  - **User Dashboard (Role-Based):** `/dashboard/`
  - **Admin User Management:** `/admin/users/`
- **UI:**
  - Simple login form.
  - Role-based dashboards for R&D, QA, and Managers.
  - Admin can add, edit, or delete users.

---

### **2. Formulation Management Module**
- **Purpose:** Manage perfume recipes and track compliance.
- **Pages:**
  - **Formulation List:** `/formulations/`
  - **Formulation Details:** `/formulations/<id>/`
  - **Add/Edit Formulation:** `/formulations/add/`
- **UI:**
  - Table with formulations (name, version, compliance status).
  - Real-time compliance check.
  - Ingredient dropdowns with quantity input.

---

### **3. Compliance Checker Module**
- **Purpose:** Ensure formulations meet regulatory requirements.
- **Pages:**
  - **Real-time validation on Add/Edit Formulation Page:** `/formulations/add/`
  - **Compliance Dashboard:** `/compliance/`
- **UI:**
  - Ingredients flagged as **green (compliant)** or **red (non-compliant)**.
  - List of compliance issues with resolution tracking.

---

### **4. Inventory Management Module**
- **Purpose:** Monitor stock levels for ingredients and packaging.
- **Pages:**
  - **Inventory Dashboard:** `/inventory/`
  - **Add/Update Inventory:** `/inventory/update/`
- **UI:**
  - Table with ingredient stock levels.
  - Notifications for **low stock alerts**.

---

### **5. Dashboard & Reporting Module**
- **Purpose:** Provide high-level analytics and insights.
- **Pages:**
  - **Manager Dashboard:** `/dashboard/`
  - **Reports Page:** `/reports/`
- **UI:**
  - **Pie chart:** Compliance statistics.
  - **Bar chart:** Ingredient stock levels.
  - **Download Reports** in **PDF/CSV**.

---

### **6. Quality Assurance (QA) Module**
- **Purpose:** QA team logs test results and approves/rejects formulations.
- **Pages:**
  - **QA Dashboard:** `/qa/`
  - **QA Test Results:** `/qa/<id>/`
- **UI:**
  - List of formulations pending approval.
  - Approve/Reject buttons.
  - Comments section for QA feedback.

---

## **Navigation Structure**
**Navbar Links:**
- Dashboard  
- Formulations  
- Inventory  
- Compliance  
- QA  
- Reports *(Managers only)*

**Role-Based Views:**
- **R&D:** Access to Formulations, Compliance, Inventory.  
- **QA:** Access to QA Dashboard and Formulations.  
- **Manager:** Access to Dashboard, Reports, and Inventory Summary.  

---

## **Screenshots**
### **Dashboard View**
![Dashboard](static/images/dashboard.png)

### **Reports Page**
![Reports](static/images/reports.png)

---
