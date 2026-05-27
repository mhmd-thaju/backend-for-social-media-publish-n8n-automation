# Social Media Scheduler Pro - Setup Guide

## Prerequisites
- Python 3.8+
- MongoDB installed and running on `localhost:27017`
- n8n webhook URL configured

## Installation Steps

### 1. Create Virtual Environment
```bash
python -m venv .venv
.venv\Scripts\activate  # On Windows
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Create a `.env` file in the root directory (copy from `.env.example`):
```env
MONGO_URL=mongodb://localhost:27017
N8N_WEBHOOK_URL=https://testingautomations.app.n8n.cloud/webhook-test/fastapi-data
LOG_LEVEL=INFO
```

### 4. Verify MongoDB Connection
Make sure MongoDB is running:
```bash
mongod  # Start MongoDB service
```

### 5. Start the Application
```bash
uvicorn main:app --reload
```

Visit: http://localhost:8000

---

## Features

### 📝 Create & Schedule Posts
- **Multi-Platform Support**: Post to **Instagram**, **Facebook**, **LinkedIn**, or **Multiple Platforms** simultaneously.
- **LinkedIn Integration**: Custom media type logic optimized for LinkedIn posts:
  - **LinkedIn Text**: Text-only status updates.
  - **LinkedIn Text + Image**: High-engagement posts combining copy with graphical media.
- **Flexible Scheduling**: Publish immediately or schedule at any date-time.
- **MongoDB Queue**: Queue management persists scheduled workflows.
- **APScheduler**: Triggers n8n integration at precise schedule dates.

### 💾 Database Storage
- All scheduled and published posts saved securely to MongoDB.
- Complete metadata tracking: media type, platforms, status, errors, and post history.

### 🔐 Account Management
- Store page/user access tokens securely.
- Track token expiry with visual dashboard countdowns and active **expiry warnings** for tokens expiring within 7 days.
- Fully supports managing multiple profiles/accounts per platform (Instagram, Facebook, LinkedIn).

### 🎨 Professional Responsive UI
- Gradient theme with high-performance responsive flex layout.
- Real-time interaction: selects platform and hides/shows required inputs automatically depending on the chosen media type.
- Live status alerts and table displays for active and past scheduled actions.

---

## Centralized Configuration

To prevent configuration mismatches and enforce a single source of truth:
- The integration `N8N_WEBHOOK_URL` is parsed exactly once in `scheduler_queue.py` using `dotenv` to load environment variables from your `.env` configuration file.
- All other files (like the API routes in `main.py`) leverage this centralized import, ensuring consistent webhook endpoint execution.

---

## Project Structure
```
main.py                 # FastAPI application and route validation
database.py            # Async Motor & sync PyMongo configurations
models.py              # Pydantic schemas and database platform enums
scheduler_queue.py     # APScheduler queue, central env config, and webhook executor
requirements.txt       # Python dependencies
templates/
  └── index.html       # Rich responsive web dashboard
.env                   # Environment configuration
```

---

## API Endpoints

### Posts Management
- `GET /api/posts` - List all scheduled and published posts.
- `POST /api/publish` - Create and schedule a new post. (Validated to ensure platform and media type compatibility, e.g., LinkedIn posts must use LinkedIn media types).
- `DELETE /api/posts/{post_id}` - Cancel and delete a scheduled post.

### Accounts Management
- `GET /api/accounts` - Fetch all saved accounts.
- `POST /api/accounts` - Save a new Facebook, Instagram, or LinkedIn account token.
- `DELETE /api/accounts/{account_id}` - Delete an account.
- `GET /api/accounts/expiry-warnings` - Retrieve active alerts for expiring credentials.

---

## Database Schemas

### Scheduled Posts Collection
```json
{
  "_id": ObjectId,
  "media_type": "text|image|video|story_image|story_video|linkedin_text|linkedin_image",
  "platform": "instagram|facebook|linkedin|both",
  "scheduled_time": datetime,
  "text_topic": string,
  "image_url": string,
  "video_url": string,
  "status": "pending|scheduled|published|failed",
  "created_at": datetime,
  "published_at": datetime,
  "error_message": string
}
```

### Accounts Collection
```json
{
  "_id": ObjectId,
  "platform": "instagram|facebook|linkedin",
  "account_name": string,
  "page_access_token": string,
  "user_access_token": string,
  "token_expiry_date": datetime,
  "created_at": datetime,
  "is_active": boolean
}
```

---

## Platform Credential Generation Guides

### Facebook Page
1. Create an app in [Facebook Developers Console](https://developers.facebook.com/).
2. Under **App Settings** > **Basic**, enter a privacy policy URL and save.
3. Open **Tools** > **Graph API Explorer**.
4. Request the following permissions:
   `page_show_list`, `pages_read_engagement`, `pages_manage_posts`, `pages_read_user_content`, `page_events`, `business_management`.
5. Generate an access token and select opt-in for current and future pages in the popup.
6. Retrieve your page access token using `/me/accounts` in the explorer search bar.
7. Setup Facebook Graph API credentials in n8n.

### Instagram
1. Convert your Instagram account to a Professional account.
2. Link your Facebook page with the Instagram account.
3. Access [Meta Business Suite](https://business.facebook.com/) and ensure the page and Instagram account belong to the same business portfolio.
4. Verify asset configurations (full control enabled for Pages, Instagram accounts, and Apps).
5. In system users, generate an access token specifying "never" expire with permissions:
   `business_management`, `instagram_basic`, `instagram_content_publish`, `pages_show_list`, `pages_manage_posts`, `page_read_engagement`.
6. Add the token to n8n.

### LinkedIn
1. Create a LinkedIn Company Page.
2. Go to the [LinkedIn Developers Hub](https://developer.linkedin.com/) and register your app.
3. Associate your LinkedIn page with the app and complete verification (upload logo/details).
4. Add products:
   - **Share on LinkedIn**
   - **Sign In with LinkedIn using OpenID Connect**
   - **Community Management API** (if available) / **Events Management API**
5. Go to the **Auth** tab.
6. Click **OAuth 2.0 Tools** on the right.
7. Create a token, select required scopes, and request the access token.
8. Setup your LinkedIn credential in n8n (ensure legacy options are turned off).

---

## Troubleshooting

**MongoDB Connection Error**
- Ensure MongoDB service is running (`mongod` or services).
- Verify connection details in your `.env`.

**n8n Webhook Not Receiving Posts**
- Ensure n8n is running.
- Verify `N8N_WEBHOOK_URL` in `.env` matches the correct active n8n webhook.

**Scheduled Posts Not Executing**
- Check system logs for scheduler cues.
- Verify date-time zone formatting.
