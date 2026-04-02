# Inventory Management System.

A complete Inventory and Sales Management System designed for small retail businesses. This web application provides administrators with full control over products, stock levels, and sales through a powerful admin panel, while customers can browse products, add to cart, and place orders.

## Features

### Customer Features
- Browse products with image galleries
- Shopping cart functionality
- Customer authentication (signup/login)
- Customer profile with order history
- Secure checkout process

### Admin Features
- Dashboard with sales analytics and charts
- Product management (CRUD operations)
- Inventory management (batch-based stock tracking)
- Manual billing system
- Demand forecasting using Machine Learning
- Sales reports and analytics

## Tech Stack

- **Backend**: Flask (Python)
- **Database**: MySQL/MariaDB
- **ORM**: SQLAlchemy
- **Authentication**: Flask-Login
- **Forms**: Flask-WTF
- **ML**: scikit-learn for demand forecasting

## Installation

1. Clone the repository:
```bash
git clone https://github.com/radhakrishna1210/inventory_management_system.git
cd inventory_management_system
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
Create a `.env` file in the root directory:
```
SECRET_KEY=your-secret-key-here
DATABASE_URL=mysql+pymysql://username:password@localhost/database_name
```

5. Run database migrations:
```bash
flask db upgrade
```

6. Create an admin user:
```bash
python create_admin.py
```

7. Run the application:
```bash
python run.py
```

## Deployment on Render

### Prerequisites
- A GitHub account with this repository
- A Render account (free tier available)

### Steps to Deploy

1. **Create a PostgreSQL Database on Render** (Render doesn't support MySQL on free tier, but you can use PostgreSQL):
   - Go to Render Dashboard
   - Click "New +" → "PostgreSQL"
   - Choose a name and region
   - Note the connection string

2. **Create a Web Service**:
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Configure:
     - **Name**: inventory-management-system
     - **Environment**: Python 3
     - **Build Command**: `pip install -r requirements.txt && flask db upgrade`
     - **Start Command**: `gunicorn run:app`
   
3. **Set Environment Variables**:
   - `SECRET_KEY`: Generate a random secret key
   - `DATABASE_URL`: Use the PostgreSQL connection string from step 1
   - `PYTHON_VERSION`: 3.11.0

4. **Update Database Configuration** (if using PostgreSQL):
   - Install `psycopg2-binary` in requirements.txt
   - Update the database connection string format

5. **Deploy**:
   - Click "Create Web Service"
   - Render will build and deploy your application

### Alternative: Using MySQL on Render

If you need MySQL specifically, you can:
- Use an external MySQL service (like PlanetScale, AWS RDS, or DigitalOcean)
- Update the `DATABASE_URL` environment variable with your MySQL connection string

## Project Structure

```
inventory_app/
├── app/
│   ├── __init__.py          # App factory and configuration
│   ├── models.py            # Database models
│   ├── forms.py             # WTForms
│   ├── ml_models.py         # ML demand forecasting
│   ├── main/                # Customer-facing routes
│   ├── admin/                # Admin panel routes
│   ├── templates/           # Jinja2 templates
│   └── static/             # CSS and uploaded images
├── migrations/              # Database migrations
├── requirements.txt         # Python dependencies
├── run.py                   # Application entry point
└── create_admin.py          # Script to create admin users
```

## Usage

### Creating Admin Users
```bash
python create_admin.py
```

### Running Database Migrations
```bash
flask db upgrade
flask db migrate -m "Description"
```

## License

This project is open source and available for use.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

