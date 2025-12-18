"""
Email Notifications Module (Optional)
Λειτουργεί μόνο αν υπάρχουν email secrets
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

class EmailManager:
    """Διαχείριση email notifications (προαιρετικό)"""
    
    def __init__(self, config):
        """
        config: dict με keys smtp_server, smtp_port, sender_email, sender_password
        """
        self.config = config
        self.enabled = config is not None
    
    def send_notification(self, to_email, subject, body):
        """Αποστολή email"""
        if not self.enabled:
            return False, "Email not configured"
        
        try:
            msg = MIMEMultipart()
            msg['From'] = self.config['sender_email']
            msg['To'] = to_email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'html', 'utf-8'))
            
            server = smtplib.SMTP(self.config['smtp_server'], self.config['smtp_port'])
            server.starttls()
            server.login(self.config['sender_email'], self.config['sender_password'])
            server.send_message(msg)
            server.quit()
            
            return True, "Email sent successfully"
        except Exception as e:
            return False, str(e)
    
    def send_task_reminder(self, to_email, task_title, due_date):
        """Υπενθύμιση για εργασία"""
        subject = f"Υπενθύμιση: {task_title}"
        body = f"""
        <html>
        <body>
            <h2>Υπενθύμιση Εργασίας</h2>
            <p><strong>Εργασία:</strong> {task_title}</p>
            <p><strong>Προθεσμία:</strong> {due_date}</p>
            <p>Η εργασία πλησιάζει την προθεσμία της.</p>
            <br>
            <p>Στοά ΑΚΡΟΠΟΛΙΣ</p>
        </body>
        </html>
        """
        return self.send_notification(to_email, subject, body)
    
    def send_meeting_reminder(self, to_emails, meeting_date, agenda):
        """Υπενθύμιση για συνεδρία"""
        subject = "Υπενθύμιση Συνεδρίας ΑΚΡΟΠΟΛΙΣ"
        body = f"""
        <html>
        <body>
            <h2>Προσεχής Συνεδρία</h2>
            <p><strong>Ημερομηνία:</strong> {meeting_date}</p>
            <p><strong>Θέματα Ημερήσιας Διάταξης:</strong></p>
            <p>{agenda}</p>
            <br>
            <p>Στοά ΑΚΡΟΠΟΛΙΣ Υπ ΑΡΙΘΜ 84</p>
        </body>
        </html>
        """
        
        results = []
        for email in to_emails:
            success, msg = self.send_notification(email, subject, body)
            results.append((email, success, msg))
        
        return results

