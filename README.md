# Product Swap App

A Flask-based web application that allows users to exchange products (books, electronics, and instrumental tools).

## Features

### User
- Register and login
- Add items for swap with image, description, and category
- Browse items listed by others
- Request swaps for items

### Admin
- View and manage all swap requests
- Accept or reject swap requests

## Setup Instructions

### Requirements
- Python 3.7+
- Flask
- Flask_SQLAlchemy
- Werkzeug

### Installation
1. Create a virtual environment (optional):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the app:
   ```bash
   python run.py
   ```

4. Access the app at [http://localhost:5000](http://localhost:5000)

### Notes
- The default admin account is:
  - Username: `admin`
  - Password: `admin`

