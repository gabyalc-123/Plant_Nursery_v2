# Plant_Nursery_v2

#  Lucky Leaf Plant Nursery – Online ordering for native plants 

---

##  Project Overview

This system provides a convenient way for users to:
- Register and log in
- Select products and place order
- Track order status

Admins can:
- Add, edit, or delete plant orders
- Manage plant types and stock
- View and manage all orders and users

---

## 🔧 Tech Stack

- **Backend**: Flask (Python)
- **Database**: SQLite
- **Frontend**: HTML, CSS
- **Tools**: PyCharm, Postman, GitHub

---

## 📋 Features

### 👤 Customer
- Register & Login
- Book fuel (with live total calculation)
- Select delivery time slot
- View past orders
- Cancel orders (if pending)

### 🧑‍💼 Admin
- Dashboard with stats
- Manage orders (cancel / mark delivered)
- Add/update/delete plant types
- Manage plant types
- View users

---

## 🚀 How to Run

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/plant_nursery_v2.git
   cd fuelnow
   ```

2. Create a virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the app:
   ```bash
   python app.py
   ```

5. Visit [http://localhost:5000](http://localhost:5000) in your browser.

---

## 🗃️ Folder Structure

```
fuelnow/
├── app.py
├── templates/
│   ├── user/
│   └── admin/
├── models/
├── static/
├── instance/
│   └── db.sqlite
├── requirements.txt
└── README.md
```

---

## 📆 Developed With SDLC

This project followed the **Software Development Life Cycle (SDLC)**:
- Planning
- Requirements Gathering
- Design
- Development
- Testing
- Deployment
- Maintenance

---

## 👤 Author

- **Name**: [Gaby Alcala / Jordyn Binkley]
- **College/Batch**: [UNT]
- **Date**: [04/25/2027]

---

## 📜 License

This project is for educational purposes only.
