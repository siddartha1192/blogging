# TechBobbles Setup Guide

This guide will help you configure the enterprise-level features added to your blogging platform.

## 🚀 Features Overview

Your TechBobbles platform now includes:
- ✅ **Google OAuth Authentication** - Users can sign in with Google
- ✅ **Email Notifications** - Automatic welcome emails to new subscribers
- ✅ **Enhanced Subscription Form** - Collects name, email (required), and phone
- ✅ **Professional Email Templates** - Beautiful HTML email design
- ✅ **User Session Management** - Logged-in users see their profile in navbar

---

## 📋 Prerequisites

1. **Python 3.11+** installed
2. **Gmail Account** for sending emails
3. **Google Cloud Project** for OAuth

---

## 🔧 Step 1: Install Dependencies

```bash
cd /home/user/blogging
pip install -r requirements.txt
```

**Required packages:**
- Flask==3.1.2
- Flask-SQLAlchemy==3.1.1
- Flask-Mail==0.10.0
- Authlib==1.4.0
- python-dotenv==1.2.1
- markdown==3.10.2

---

## 📧 Step 2: Configure Gmail for Email Notifications

### A. Enable 2-Factor Authentication on Gmail

1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Enable **2-Step Verification** if not already enabled

### B. Create an App Password

1. Visit [Google App Passwords](https://myaccount.google.com/apppasswords)
2. Select **Mail** as the app
3. Select **Other** as the device and name it "TechBobbles"
4. Click **Generate**
5. Copy the 16-character password (you'll need this in Step 4)

### C. Update .env File

Edit `/home/user/blogging/.env`:

```env
MAIL_USERNAME=your-actual-email@gmail.com
MAIL_PASSWORD=xxxx xxxx xxxx xxxx  # The 16-char app password
```

**Example:**
```env
MAIL_USERNAME=techbobbles@gmail.com
MAIL_PASSWORD=abcd efgh ijkl mnop
```

---

## 🔐 Step 3: Configure Google OAuth

### A. Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project named "TechBobbles"
3. Enable **Google+ API** and **OAuth 2.0**

### B. Create OAuth Credentials

1. Navigate to **APIs & Services** > **Credentials**
2. Click **Create Credentials** > **OAuth 2.0 Client ID**
3. Select **Web application**
4. Configure:
   - **Name:** TechBobbles OAuth
   - **Authorized JavaScript origins:**
     - `http://localhost:8080`
     - `https://neuragg.com` (your production domain)
   - **Authorized redirect URIs:**
     - `http://localhost:8080/authorize`
     - `https://neuragg.com/authorize`
     - `https://neuragg.com/integrations/gmail/callback`
     - `https://neuragg.com/api/auth/google/callback`

5. Click **Create**
6. Copy the **Client ID** and **Client Secret**

### C. Update .env File

The Google credentials are already in your `.env`:

```env
GOOGLE_CLIENT_ID=jq9ddljh5g40ouulh3cr7vio.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-rkHBXXXNW49_tQowZGg1yIPyi
```

**⚠️ IMPORTANT:** Make sure these match your actual Google Cloud Console credentials!

---

## Step 4: Initialize the Database

The database schema has been updated with new tables:

```bash
cd /home/user/blogging
python3 -c "from app import app, db; app.app_context().push(); db.create_all()"
```

**New database tables:**
- `user` - Stores Google OAuth user accounts
- `subscriber` - Now includes `name` and `phone` fields

---

## ▶️ Step 5: Run the Application

```bash
python3 app.py
```

The app will start on `http://localhost:8080` (or port specified in environment)

---

## ✅ Step 6: Test the Features

### Test 1: Subscription Form
1. Navigate to the homepage
2. Scroll to "Stay Updated with Tech Insights"
3. Fill in:
   - Name: John Doe (optional)
   - Email: your-test-email@gmail.com (required)
   - Phone: +1234567890 (optional)
4. Click "Subscribe to Newsletter"
5. Check the email inbox for the welcome email

### Test 2: Google Login
1. Click "Sign In with Google" in the navbar
2. Select your Google account
3. Grant permissions
4. You should be redirected to homepage
5. See your profile picture and name in the navbar

### Test 3: Logout
1. Click on your profile in navbar
2. Select "Logout"
3. You should be logged out and redirected to homepage

---

## 🎨 Email Template Customization

The welcome email template is located at:
```
templates/emails/welcome.html
```

**Customizable sections:**
- Header gradient colors
- Welcome message
- Feature list
- Call-to-action button
- Social media links
- Footer content

**Variables available in template:**
- `{{ name }}` - Subscriber's name
- `{{ site_url }}` - Link to homepage
- `{{ sender_email }}` - From email address
- `{{ unsubscribe_url }}` - Unsubscribe link
- `{{ privacy_url }}` - Privacy policy link

---

## 🔒 Security Best Practices

1. **Never commit `.env` to Git** ✅ (already in .gitignore)
2. **Use strong SECRET_KEY** in production
3. **Enable HTTPS** for OAuth callbacks in production
4. **Rotate App Passwords** periodically
5. **Limit OAuth scopes** to only what's needed

---

## 🐛 Troubleshooting

### Email Not Sending

**Problem:** Welcome emails not arriving

**Solutions:**
1. Verify Gmail App Password is correct
2. Check `MAIL_USERNAME` and `MAIL_PASSWORD` in `.env`
3. Enable "Less secure app access" if using older Gmail security
4. Check spam folder
5. Review Flask console for error messages

### OAuth Login Fails

**Problem:** Google login redirects to error page

**Solutions:**
1. Verify redirect URIs in Google Cloud Console match exactly
2. Check `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` in `.env`
3. Ensure OAuth consent screen is configured
4. Clear browser cookies and try again
5. Check Flask console for detailed error logs

### Database Errors

**Problem:** SQLAlchemy errors on subscription

**Solutions:**
1. Delete `techblog.db` and recreate database
2. Run database initialization command (see Step 4)
3. Check file permissions on database file

---

## 📊 Database Schema

### User Table
```sql
id: Integer (Primary Key)
google_id: String(100) (Unique)
email: String(255) (Unique, Not Null)
name: String(100)
profile_pic: String(500)
created_at: DateTime
last_login: DateTime
```

### Subscriber Table
```sql
id: Integer (Primary Key)
name: String(100)
email: String(255) (Unique, Not Null)
phone: String(20)
subscribed_on: DateTime
```

---

## 🚀 Production Deployment Checklist

Before deploying to production:

- [ ] Update `.env` with production values
- [ ] Set strong `SECRET_KEY`
- [ ] Configure production domain in Google OAuth
- [ ] Enable HTTPS
- [ ] Set up production database (PostgreSQL recommended)
- [ ] Configure email service (SendGrid, Mailgun, or Gmail)
- [ ] Set up monitoring and logging
- [ ] Add rate limiting for subscription endpoint
- [ ] Implement unsubscribe functionality
- [ ] Add GDPR-compliant privacy policy
- [ ] Test all features on staging environment

---

## 📞 Support

For issues or questions:
- Check Flask console logs for error messages
- Review Google Cloud Console for OAuth errors
- Verify all environment variables are set correctly
- Test email configuration separately

---

## 🎉 Success!

Your TechBobbles platform is now enterprise-ready with:
- Professional email notifications
- Google OAuth authentication
- Enhanced data collection
- Beautiful, responsive UI

**Happy blogging! 🚀**
