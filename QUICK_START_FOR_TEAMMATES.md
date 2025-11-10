# ⚡ Quick Start Guide for New Team Members

## 🚀 Setup in 5 Minutes

### 1️⃣ Clone & Install (2 minutes)
```bash
git clone <your-repo-url>
cd modularecg-main
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
```

### 2️⃣ Configure Cloud (2 minutes) - AUTOMATIC!
```bash
# Run the interactive setup script
python3 setup_cloud.py
```

**The script will ask you for 4 values (get from Divyansh):**
1. AWS_ACCESS_KEY_ID (20 chars, starts with AKIA)
2. AWS_SECRET_ACCESS_KEY (40 chars, will be hidden)
3. AWS_S3_BUCKET (bucket name)
4. AWS_S3_REGION (default: us-east-1)

**It will automatically:**
- ✅ Validate your inputs
- ✅ Create the .env file
- ✅ Test the connection
- ✅ Confirm everything works!

**Expected:** `🎉 SUCCESS! Cloud sync is now configured!`

### 4️⃣ Run the App
```bash
python src/main.py
```

---

## 📋 Checklist

- [ ] Repository cloned
- [ ] Virtual environment activated
- [ ] Dependencies installed
- [ ] `.env` created with AWS credentials
- [ ] Test script passed
- [ ] App runs successfully

---

## 🆘 Common Issues

| Issue | Solution |
|-------|----------|
| `.env file not found` | Run: `cp env_template.txt .env` |
| `Cloud Not Configured` | Check `.env` is in project root |
| `Access Denied` | Verify credentials with Divyansh |
| `boto3 not installed` | Run: `pip install boto3` |

---

## 📚 Full Documentation

- **Complete Setup:** See `CLOUD_SETUP_GUIDE.md`
- **Dependencies:** See `DEPENDENCIES_SUMMARY.md`
- **Technical Docs:** See `TECHNICAL_DOCUMENTATION.md`

---

## 👥 Team Contacts

- **Team Lead:** Divyansh (backend, AWS setup)
- **Frontend:** Indresh, PTR
- **Android:** (Android dev name)

---

**Ready to code? Run:** `python src/main.py` 🎉

