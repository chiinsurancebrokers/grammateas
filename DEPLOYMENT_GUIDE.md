# 🚀 Οδηγός Deployment - Σύστημα Διαχείρισης Στοάς

## 📦 Αρχεία Repository

```
grammateas/
├── lodge_management_app.py          ← Κύριο app
├── config_manager.py                ← Configuration handler
├── tasks_module.py                  ← Tasks & Reminders
├── email_module.py                  ← Email notifications (optional)
├── requirements.txt                 ← Dependencies
├── lodge_members.db                 ← Database
├── .gitignore                       ← Git config
├── README.md                        ← Documentation
└── DEPLOYMENT_GUIDE.md              ← Αυτό το αρχείο
```

---

## 🎯 Deployment Options

### **Option 1: Basic Deployment (Χωρίς Secrets)** ✅ ΣΥΝΙΣΤΑΤΑΙ

Το app λειτουργεί **πλήρως χωρίς secrets** με core features:

#### **Βήματα:**
1. Upload αρχεία στο GitHub
2. https://share.streamlit.io → "New app"
3. Configuration:
   ```
   Repository: chiinsurancebrokers/grammateas
   Branch: main
   Main file: lodge_management_app.py
   ```
4. **Advanced Settings** → **ΑΦΗΣΕ SECRETS ΚΕΝΟ**
5. Deploy!

#### **Features που δουλεύουν:**
- ✅ Μητρώο Μελών (40 μέλη)
- ✅ Επεξεργασία Μέλους
- ✅ Μαζική Επεξεργασία (Excel import/export)
- ✅ Καρτέλες PDF
- ✅ Στατιστικά
- ✅ **Task Management** (εργασίες & υπενθυμίσεις)
- ⚪ Email Notifications (disabled)
- ⚪ AI Assistant (disabled)

---

### **Option 2: Full Deployment (Με Optional Features)** 🔧 ΠΡΟΧΩΡΗΜΕΝΟ

Ενεργοποίηση όλων των features με secrets.

#### **Βήμα 1: Gmail App Password**

1. Google Account → https://myaccount.google.com/apppasswords
2. Create app password για "Streamlit Lodge App"
3. Αντιγράφεις το password (16 χαρακτήρες)

#### **Βήμα 2: Anthropic API Key** (optional)

1. https://console.anthropic.com
2. Create API key
3. Αντιγράφεις: `sk-ant-api03-...`

#### **Βήμα 3: Streamlit Secrets**

Στο deployment, **Advanced Settings** → **Secrets**:

```toml
# Email Configuration (Optional)
[email]
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = "587"
SENDER_EMAIL = "your-email@gmail.com"
SENDER_PASSWORD = "your-16-char-app-password"

# AI Configuration (Optional)
[ai]
ANTHROPIC_API_KEY = "sk-ant-api03-your-key-here"

# Admin (Optional)
ADMIN_EMAIL = "admin@example.com"
```

#### **Features που ενεργοποιούνται:**
- ✅ Όλα τα βασικά +
- ✅ **Email Notifications** (αυτόματες ειδοποιήσεις)
- ✅ **Task Reminders** (email για εργασίες)
- ✅ **Meeting Reminders** (email για συνεδρίες)
- ✅ **AI Assistant** (Claude για βοήθεια)

---

## 🎛️ Feature Toggles

Το app ανιχνεύει **αυτόματα** ποια features είναι διαθέσιμα:

```python
# Στην εφαρμογή:
if config.email_enabled:
    # Εμφάνιση email options
    
if config.ai_enabled:
    # Εμφάνιση AI assistant
```

---

## 📊 Σύγκριση Options

| Feature | Basic | Full |
|---------|-------|------|
| Μητρώο Μελών | ✅ | ✅ |
| Bulk Edit | ✅ | ✅ |
| PDF Καρτέλες | ✅ | ✅ |
| Tasks | ✅ | ✅ |
| Email | ❌ | ✅ |
| AI | ❌ | ✅ |
| **Setup Time** | 2 min | 10 min |
| **Complexity** | Εύκολο | Μέτριο |

---

## 🔐 Security Best Practices

### **Για GitHub:**
1. **Make repository PRIVATE** (προσωπικά δεδομένα!)
2. ΜΗΝ commit secrets στο repo
3. Χρησιμοποίησε `.gitignore` σωστά

### **Για Streamlit:**
1. Secrets αποθηκεύονται **encrypted**
2. Δεν εμφανίζονται στα logs
3. Accessible μόνο από το app

### **Για Email:**
1. Χρησιμοποίησε **App Password** (όχι κύριο password)
2. Ενεργοποίησε **2FA** στο Gmail
3. Revoke το password αν δεν χρειάζεται

---

## 🆘 Troubleshooting

### **Πρόβλημα 1: "ModuleNotFoundError"**
```
ModuleNotFoundError: No module named 'anthropic'
```

**Λύση:** Έλεγξε `requirements.txt` - πρέπει να περιέχει:
```
anthropic
python-dotenv
```

---

### **Πρόβλημα 2: "Email not configured"**
```
⚠️ Email features disabled - no secrets found
```

**Λύση:** Αυτό είναι **φυσιολογικό** αν δεν έχεις βάλει email secrets!
- Το app λειτουργεί κανονικά χωρίς email
- Για να ενεργοποιήσεις email, πρόσθεσε secrets

---

### **Πρόβλημα 3: "SMTP Authentication failed"**

**Λύση:**
1. Έλεγξε το App Password (16 χαρακτήρες, χωρίς κενά)
2. Έλεγξε αν η 2FA είναι ενεργή
3. Δοκίμασε να δημιουργήσεις νέο App Password

---

### **Πρόβλημα 4: "Database locked"**

**Λύση:**
- Κάνε refresh τη σελίδα
- Αν επιμένει, restart το app από το Streamlit dashboard

---

## 📈 Monitoring

### **Χρήση Resources:**
```
Deployed app: ~250 MB RAM
Database: ~24 KB
PDF generation: ~2-5 MB RAM per PDF
```

### **Streamlit Cloud Limits:**
- **Free tier:** Unlimited users, 1 GB RAM
- **Community tier:** Public apps or private with GitHub teams

---

## 🔄 Updates

### **Για να ενημερώσεις το app:**

1. **Local changes:**
   ```bash
   git add .
   git commit -m "Update: description"
   git push origin main
   ```

2. **Streamlit auto-deploys** σε ~30 δευτερόλεπτα

3. **Manual reboot** (αν χρειάζεται):
   - Streamlit dashboard → "..." → "Reboot app"

---

## 🎯 Recommended Setup

Για **production use**:

```
1. Start with BASIC deployment (χωρίς secrets)
2. Δοκίμασε όλα τα core features
3. Αν χρειάζεσαι email → Πρόσθεσε email secrets
4. Αν χρειάζεσαι AI → Πρόσθεσε AI secrets
5. Monitor usage και προσάρμοσε
```

**Προτεραιότητα:**
```
Core Features > Tasks > Email > AI
```

---

## 📞 Support

- **Streamlit Docs:** https://docs.streamlit.io
- **GitHub Issues:** Create issue στο repo
- **Anthropic:** https://docs.anthropic.com

---

## ✅ Deployment Checklist

```
☐ Repository στο GitHub (private!)
☐ Όλα τα αρχεία uploaded
☐ .gitignore configured
☐ Streamlit account created
☐ App deployed
☐ Database accessible
☐ PDF generation tested
☐ Secrets configured (αν χρειάζεται)
☐ Email tested (αν ενεργοποιημένο)
☐ Backup strategy
```

---

**Έκδοση:** 2.0  
**Ημερομηνία:** Δεκέμβριος 2025  
**Maintainer:** Χρήστος Ιατρόπουλος
