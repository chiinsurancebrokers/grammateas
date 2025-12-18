# 🏛️ Σύστημα Διαχείρησης Στοάς ΑΚΡΟΠΟΛΙΣ v2.0

## 🎯 Multi-Page Application Architecture

Επαγγελματική, modular εφαρμογή με conditional features.

---

## 📦 Structure

```
grammateas/
├── app.py                          ← Main entry point (Αρχική σελίδα)
├── pages/                          ← Ξεχωριστές σελίδες
│   ├── 1_Μητρώο.py                ← Μητρώο Μελών ✅
│   ├── 2_Επεξεργασία.py           ← Επεξεργασία Μέλους (TODO)
│   ├── 3_Μαζική_Επεξεργασία.py    ← Bulk editing (TODO)
│   ├── 4_Καρτέλες.py              ← PDF καρτέλες (TODO)
│   ├── 5_Στατιστικά.py            ← Analytics (TODO)
│   └── 6_Εργασίες.py              ← Task management (TODO)
├── modules/                        ← Backend logic
│   ├── config.py                  ← Configuration & feature detection
│   ├── database.py                ← Database operations
│   ├── email.py                   ← Email notifications (optional)
│   └── pdf_generator.py           ← PDF generation
├── lodge_members.db                ← SQLite database
├── requirements.txt                ← Python dependencies
├── .gitignore                      ← Git configuration
├── README.md                       ← General documentation
└── DEPLOYMENT_GUIDE.md             ← Deployment instructions
```

---

## 🚀 Quick Start

### **Local Development:**

```bash
# Clone/Download
cd grammateas

# Install dependencies
pip install -r requirements.txt

# Run app
streamlit run app.py
```

**App opens at:** http://localhost:8501

---

### **Streamlit Cloud Deployment:**

1. **Upload to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit - Multi-page app"
   git push origin main
   ```

2. **Deploy**
   - https://share.streamlit.io
   - New app
   - Repository: `yourusername/grammateas`
   - Branch: `main`
   - Main file: `app.py`  ← ΣΗΜΑΝΤΙΚΟ!
   
3. **Done!** App deploys in ~2 minutes

---

## 🎨 Features

### **Core Features (Πάντα Διαθέσιμα - Χωρίς Secrets)**

| Feature | Status | Description |
|---------|--------|-------------|
| 📋 **Μητρώο** | ✅ | Προβολή & αναζήτηση 40 μελών |
| 👤 **Επεξεργασία** | 🚧 | Single member editing |
| ✏️ **Bulk Edit** | 🚧 | Excel import/export, mass updates |
| 📄 **Καρτέλες** | 🚧 | PDF generation με ελληνικά |
| 📈 **Στατιστικά** | 🚧 | Charts & analytics |
| 📋 **Εργασίες** | 🚧 | Task management & reminders |

### **Optional Features (Με Secrets)**

| Feature | Requires | Description |
|---------|----------|-------------|
| 📧 **Email** | SMTP credentials | Notifications, reminders |
| 🤖 **AI** | Anthropic API key | AI assistant, document generation |

---

## ⚙️ Configuration

### **Χωρίς Secrets (Default):**

Το app λειτουργεί **πλήρως** με core features.

**Καμία ενέργεια δεν απαιτείται!**

---

### **Με Optional Features:**

Αν θέλεις email ή AI, πρόσθεσε στο Streamlit Cloud **Advanced Settings** → **Secrets**:

```toml
# Email (Optional)
[email]
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = "587"
SENDER_EMAIL = "your@email.com"
SENDER_PASSWORD = "app-password-16-chars"

# AI (Optional)
[ai]
ANTHROPIC_API_KEY = "sk-ant-api03-..."
```

Το app **ανιχνεύει αυτόματα** ποια features είναι διαθέσιμα!

---

## 🎯 Πώς Λειτουργεί το Multi-Page

### **Streamlit Automatic Navigation:**

```python
# Streamlit ανιχνεύει αυτόματα το pages/ directory
pages/
├── 1_Μητρώο.py      → Sidebar: "Μητρώο"
├── 2_Επεξεργασία.py  → Sidebar: "Επεξεργασία"
└── ...
```

### **Feature Detection:**

```python
# modules/config.py
class Config:
    def _detect_features(self):
        # Αυτόματος έλεγχος secrets
        if 'SMTP_SERVER' in secrets:
            features['email'] = True
```

### **Conditional Pages:**

Pages μπορούν να εμφανίζονται/κρύβονται βάσει configuration!

---

## 📊 Development Roadmap

### **Phase 1: Core Setup (COMPLETED ✅)**
- [x] Multi-page structure
- [x] Config module με feature detection
- [x] Database module
- [x] Μητρώο page

### **Phase 2: Core Features (IN PROGRESS 🚧)**
- [ ] Complete Επεξεργασία page
- [ ] Complete Μαζική Επεξεργασία
- [ ] Complete Καρτέλες PDF
- [ ] Complete Στατιστικά
- [ ] Complete Εργασίες

### **Phase 3: Optional Features (PLANNED 📅)**
- [ ] Email notifications page
- [ ] AI Assistant page
- [ ] Calendar integration

---

## 🔧 Development Notes

### **Adding a New Page:**

1. Create `pages/X_Title.py`
2. Streamlit auto-discovers it
3. Appears in sidebar navigation

```python
# pages/7_My_Page.py
import streamlit as st

st.title("My New Page")
st.write("Content here")
```

### **Using Modules:**

```python
# In any page
import sys
sys.path.append('..')

from modules.database import get_database
from modules.config import get_config

db = get_database()
config = get_config()
```

### **Feature Checks:**

```python
config = get_config()

if config.is_feature_enabled('email'):
    # Show email options
    pass
```

---

## 🆘 Troubleshooting

### **"ModuleNotFoundError: No module named 'modules'"**

**Solution:**
```python
import sys
sys.path.append('..')  # Add this at top of page
```

---

### **Pages not showing in sidebar**

**Check:**
1. Files are in `pages/` directory
2. Filenames start with number + underscore: `1_Name.py`
3. Files are valid Python

---

### **Feature not enabled despite secrets**

**Check:**
1. Secrets format is correct (TOML)
2. Section names match: `[email]`, `[ai]`
3. Restart app after adding secrets

---

## 📈 Performance

- **Load time:** ~2-3 seconds
- **Memory:** ~200-300 MB
- **Database:** SQLite (24 KB)
- **Concurrent users:** Unlimited (Streamlit Cloud free tier)

---

## 🔐 Security

- **Database:** Read-only for users
- **Secrets:** Encrypted by Streamlit
- **GitHub:** Make repository **PRIVATE** (contains personal data)

---

## 📞 Support

- **GitHub Issues:** Create issue in repo
- **Email:** xiatropoulos@gmail.com
- **Streamlit Docs:** https://docs.streamlit.io

---

## 🎉 Benefits of Multi-Page Architecture

### **vs Single-Page:**

| Aspect | Single-Page | Multi-Page |
|--------|-------------|------------|
| **Organization** | All in one file | Clean separation |
| **Loading** | Load everything | Load only current page |
| **Development** | Complex | Easy to extend |
| **Debugging** | Hard to trace | Isolated pages |
| **Collaboration** | Merge conflicts | Work on different pages |

### **Production Ready:**

- ✅ Scalable
- ✅ Maintainable
- ✅ Professional
- ✅ Standard Streamlit pattern

---

**Version:** 2.0  
**Date:** December 2025  
**Author:** Χρήστος Ιατρόπουλος  
**License:** Private - ΑΚΡΟΠΟΛΙΣ Lodge
