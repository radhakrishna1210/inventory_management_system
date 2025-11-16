# Deployment Guide for Render

This guide will help you deploy the Inventory Management System to Render.

## Prerequisites

1. GitHub account with this repository
2. Render account (sign up at https://render.com)

## Step-by-Step Deployment

### Option 1: Using PostgreSQL (Recommended for Render Free Tier)

Render's free tier includes PostgreSQL, which works well with this application.

#### 1. Create PostgreSQL Database

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click **"New +"** → **"PostgreSQL"**
3. Configure:
   - **Name**: `inventory-db`
   - **Database**: `inventory`
   - **User**: `inventory_user`
   - **Region**: Choose closest to you
   - **Plan**: Free
4. Click **"Create Database"**
5. Wait for database to be ready, then copy the **Internal Database URL**

#### 2. Update Requirements for PostgreSQL

Add PostgreSQL driver to `requirements.txt`:
```
psycopg2-binary==2.9.9
```

#### 3. Create Web Service

1. In Render Dashboard, click **"New +"** → **"Web Service"**
2. Connect your GitHub account if not already connected
3. Select this repository: `inventory_management_system`
4. Configure the service:
   - **Name**: `inventory-management-system`
   - **Environment**: `Python 3`
   - **Region**: Same as database
   - **Branch**: `main`
   - **Root Directory**: (leave empty)
   - **Build Command**: 
     ```
     pip install -r requirements.txt && flask db upgrade
     ```
   - **Start Command**: 
     ```
     gunicorn --bind 0.0.0.0:$PORT run:app
     ```
   - **Important**: Make sure the start command is exactly `gunicorn --bind 0.0.0.0:$PORT run:app` (not `gunicorn app:app`)
   - **Plan**: Free

#### 4. Set Environment Variables

**IMPORTANT**: You MUST set the `DATABASE_URL` environment variable, otherwise the app will fail to start.

In the Web Service settings, go to **"Environment"** tab and add:

- **SECRET_KEY**: 
  - Generate a random key: `python -c "import secrets; print(secrets.token_hex(32))"`
  - Or use: `openssl rand -hex 32`
  - Click "Generate" or paste your generated key

- **DATABASE_URL**: 
  - **CRITICAL**: This must be set!
  - Go to your PostgreSQL database in Render dashboard
  - Copy the **"Internal Database URL"** (for same-region services) or **"External Database URL"**
  - Format: `postgresql://user:password@host:port/database`
  - **Note**: If the URL starts with `postgres://`, the app will automatically convert it to `postgresql://`
  - Paste the entire connection string as the value

- **PYTHON_VERSION**: `3.11.0` (optional, but recommended)

#### 5. Link Database (Recommended - Easiest Method)

**This is the easiest way to set DATABASE_URL automatically:**

1. In your Web Service settings
2. Go to **"Environment"** tab
3. Scroll down to **"Add Environment Variable"**
4. Click the dropdown and select **"Add Database"**
5. Choose your PostgreSQL database from the list
6. This automatically sets `DATABASE_URL` with the correct connection string
7. **Verify**: You should see `DATABASE_URL` appear in your environment variables list

#### 6. Deploy

1. Click **"Create Web Service"**
2. Render will:
   - Clone your repository
   - Install dependencies
   - Run database migrations
   - Start your application
3. Wait for deployment to complete (usually 2-5 minutes)

#### 7. Create Admin User

After deployment, you need to create an admin user. You can:

**Option A: Using Render Shell**
1. Go to your Web Service
2. Click **"Shell"** tab
3. Run:
   ```bash
   python create_admin.py
   ```

**Option B: Using Local Connection**
1. Set up SSH tunnel to Render database
2. Run `create_admin.py` locally with the database connection

### Option 2: Using External MySQL

If you prefer MySQL, you can use an external MySQL service:

1. **Set up MySQL Database**:
   - Use services like:
     - [PlanetScale](https://planetscale.com) (free tier available)
     - [AWS RDS](https://aws.amazon.com/rds/)
     - [DigitalOcean Managed Databases](https://www.digitalocean.com/products/managed-databases)
     - [Railway](https://railway.app) (MySQL available)

2. **Get Connection String**:
   - Format: `mysql+pymysql://user:password@host:port/database`
   - Make sure to use `mysql+pymysql://` prefix for PyMySQL

3. **Set Environment Variables**:
   - `DATABASE_URL`: Your MySQL connection string
   - `SECRET_KEY`: Generated secret key
   - `PYTHON_VERSION`: 3.11.0

4. **Follow steps 3-7** from Option 1 (but skip database creation on Render)

## Post-Deployment

### 1. Verify Deployment

- Visit your Render service URL (e.g., `https://inventory-management-system.onrender.com`)
- You should see the home page

### 2. Run Database Migrations (if needed)

If migrations didn't run during build:
1. Go to **"Shell"** in Render dashboard
2. Run: `flask db upgrade`

### 3. Create Admin User

1. Go to **"Shell"** in Render dashboard
2. Run: `python create_admin.py`
3. Follow prompts to create admin account

### 4. Access Admin Panel

- Go to: `https://your-app.onrender.com/admin/login`
- Login with admin credentials

## Important Notes

### File Uploads

- **Local Storage**: Uploaded images are stored in `app/static/uploads/`
- **Limitation**: On Render free tier, files are ephemeral (lost on restart)
- **Solution**: Use cloud storage (AWS S3, Cloudinary, etc.) for production

### Environment Variables

Never commit `.env` file to Git. All secrets should be in Render's environment variables.

### Database Migrations

Migrations run automatically during build. If you add new migrations:
1. Commit to GitHub
2. Render will auto-deploy
3. Migrations run in build command

### Static Files

Static files (CSS, images) are served automatically by Flask. Make sure:
- Files are committed to Git
- Paths in templates use `url_for('static', ...)`

## Troubleshooting

### Build Fails

- Check build logs in Render dashboard
- Verify all dependencies in `requirements.txt`
- Ensure Python version matches

### Database Connection Errors

- **Error: "Either 'SQLALCHEMY_DATABASE_URI' or 'SQLALCHEMY_BINDS' must be set"**
  - **Solution**: The `DATABASE_URL` environment variable is not set
  - Go to your Web Service → Environment tab
  - Add `DATABASE_URL` with your PostgreSQL connection string
  - Or use "Add Database" to link it automatically
  - Redeploy after adding the variable

- Verify `DATABASE_URL` is set correctly
- Check database is running
- Ensure database allows connections from Render IPs
- For PostgreSQL, make sure the URL uses `postgresql://` (not `postgres://`)

### Application Crashes

- Check logs in Render dashboard
- Verify all environment variables are set
- Ensure database migrations completed

### Admin User Creation Fails

- Verify database connection
- Check if User table exists: `flask db upgrade`
- Try creating user via Render Shell

## Scaling

### Free Tier Limitations

- **Sleeps after 15 minutes** of inactivity
- **512MB RAM**
- **Limited CPU**

### Upgrade Options

- **Starter Plan**: $7/month - No sleep, 512MB RAM
- **Standard Plan**: $25/month - 2GB RAM, better performance

## Support

For issues:
1. Check Render logs
2. Review application logs
3. Check database connection
4. Verify environment variables

