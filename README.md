# 🏛️ Σύστημα Διαχείρισης Στοάς ΑΚΡΟΠΟΛΙΣ v2.0

Multi-Page Streamlit Application - Production Ready

## 🚀 Quick Deploy

```bash
# Upload όλα τα αρχεία στο GitHub repository
# Streamlit Cloud:
# - Main file: app.py
# - Deploy!
```

## 📦 Structure

```
grammateas/
├── app.py                  # Main entry
├── pages/                  # 6 pages (ALL complete)
├── modules/                # Backend (config, database, email, pdf)
├── lodge_members.db        # Database (40 μέλη)
└── requirements.txt
```

## ✅ Features

- **Αρχική**: Dashboard με status
- **Μητρώο**: View/search 40 μέλη
- **Επεξεργασία**: Single member edit
- **Μαζική Επεξεργασία**: Excel import/export, bulk updates
- **Καρτέλες**: PDF generation (ελληνικά)
- **Στατιστικά**: Charts & analytics
- **Εργασίες**: Task management

## 🎛️ Optional Features (Auto-detected)

Add to Streamlit secrets:

```toml
[email]
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = "587"
SENDER_EMAIL = "your@email.com"
SENDER_PASSWORD = "app-password"

[ai]
ANTHROPIC_API_KEY = "sk-ant-..."
```

---

**Ready to deploy!** 🚀
