# 🍽️ The Gilded Fork - Enterprise Edition (v4.0)

A complete, end-to-end Restaurant Management System (RMS) written in Python. This application manages the entire dining lifecycle: from table reservations and inventory tracking to kitchen display and final billing.

## 🌟 Features

### 🏢 Front of House (Floor Plan)
* **Visual Interface:** A grid-based view of all restaurant tables.
* **Real-time Status:** Color-coded tables indicate status immediately:
    * 🟢 **Free:** Ready for guests.
    * 🔴 **Occupied:** Guests are dining.
    * 🟠 **Reserved:** Held for a specific guest (includes Name).
    * ⚪ **Dirty:** Needs clearing after checkout.
* **Reservation System:** Create and cancel reservations directly from the floor plan.

### 🍔 Point of Sale (POS) & Menu
* **Ordering:** Add items to a specific table's tab.
* **Live Calculation:** automatically calculates Subtotal, Tax (8%), and Total.
* **Receipt Generation:** Automatically saves a detailed `.txt` receipt to the local folder upon checkout.

### 📦 Inventory Management (Enterprise Logic)
* **Smart Deductions:** The system links Menu Items to Ingredients (e.g., *Ribeye Steak* requires *1 Steak Meat*).
* **Stock Checks:** Prevents servers from ordering items if ingredients are out of stock.
* **Automatic Tracking:** Deducts inventory counts immediately when an order is placed.

### 👨‍🍳 Back of House (Kitchen Display System)
* **Digital Tickets:** Orders sent from the floor appear instantly on the Kitchen screen.
* **Workflow:** Chefs can "Bump" (complete) orders when food is ready.

### 📊 Admin Analytics
* **Dashboard:** View Total Revenue, Total Order Counts, and Best Selling Items.
* **User Management:** Role-based access control.

---

## 🛠️ Tech Stack
* **Language:** Python 3.x
* **GUI:** Tkinter (Standard Library)
* **Database:** SQLite3 (Local, Persistent)
* **Security:** SHA-256 Password Hashing

---

## 🚀 How to Run

1.  **Prerequisites:** Ensure you have Python installed. No external libraries (`pip install`) are required.
2.  **Launch:**
    ```bash
    python restaurant_full.py
    ```
3.  **First Run:** The system will automatically create a database file named `gilded_fork_enterprise.db` and populate it with default tables, menu items, and inventory.

---

## 🔑 Login Credentials

Use the following default accounts to access the system:

| Role | Username | Password | Access Level |
| :--- | :--- | :--- | :--- |
| **Manager** | `admin` | `admin` | Full Access (Admin Stats + Floor) |
| **Server** | `server` | `1234` | Floor Plan, POS, & Kitchen |

---

## 📂 File Structure

* `restaurant_full.py`: The main application source code.
* `gilded_fork_enterprise.db`: The SQL database (created automatically).
* `receipt_ID_DATE.txt`: Receipts generated after every checkout.

---

## 📝 Usage Guide

1.  **Login** as `server`.
2.  **Reserve a Table:** On the Floor Plan, click **"Rsrv"** on a Green table and enter a name.
3.  **Seat a Guest:** Click **"Open"** (or "Manage" if reserved) to open the table.
4.  **Place Order:** Add items (e.g., Ribeye Steak). *Note: If inventory is 0, the order will be blocked.*
5.  **Send to Kitchen:** Click **"Send to Kitchen"**.
6.  **Cook Food:** Go to the **Kitchen (KDS)** tab. Click **"BUMP"** to clear the ticket.
7.  **Checkout:** Go back to the table, click **"Checkout / Pay"**.
    * This generates a receipt file.
    * The table turns Grey (Dirty).
8.  **Clear Table:** Click **"Occupy / Clear"** to make the table Green (Free) again.

---

## 🐛 Troubleshooting

* **"IndentationError" or "SyntaxError":** If you copy-pasted the code from a web browser, you might have invisible "non-breaking space" characters. Use "Find & Replace" in your text editor to replace all special spaces with standard Space bar spaces.
* **"Out of Stock" Warning:** This is a feature, not a bug! It means the `inventory` table in the database has run out of ingredients for that item.

---

**License:** MIT