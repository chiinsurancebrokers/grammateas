"""
Configuration Manager - Feature Detection & Settings
Ανιχνεύει αυτόματα ποια features είναι διαθέσιμα βάσει secrets
"""

import streamlit as st
from typing import Dict, Optional

class Config:
    """Κεντρική διαχείριση configuration"""
    
    def __init__(self):
        self.app_name = "ΑΚΡΟΠΟΛΙΣ Υπ ΑΡΙΘΜ 84"
        self.app_version = "2.0"
        self.db_path = "lodge_members.db"
        
        # Feature detection
        self.features = self._detect_features()
    
    def _detect_features(self) -> Dict[str, bool]:
        """Αυτόματη ανίχνευση διαθέσιμων features"""
        features = {
            'core': True,  # Core features πάντα enabled
            'tasks': True,  # Tasks πάντα enabled
            'email': False,
            'ai': False
        }
        
        # Check email configuration
        try:
            if hasattr(st, 'secrets') and 'email' in st.secrets:
                required = ['SMTP_SERVER', 'SMTP_PORT', 'SENDER_EMAIL', 'SENDER_PASSWORD']
                if all(key in st.secrets['email'] for key in required):
                    features['email'] = True
        except Exception:
            pass
        
        # Check AI configuration
        try:
            if hasattr(st, 'secrets') and 'ai' in st.secrets:
                if 'ANTHROPIC_API_KEY' in st.secrets['ai']:
                    features['ai'] = True
        except Exception:
            pass
        
        return features
    
    def get_email_config(self) -> Optional[Dict]:
        """Λήψη email configuration"""
        if not self.features['email']:
            return None
        
        try:
            return {
                'smtp_server': st.secrets['email']['SMTP_SERVER'],
                'smtp_port': int(st.secrets['email']['SMTP_PORT']),
                'sender_email': st.secrets['email']['SENDER_EMAIL'],
                'sender_password': st.secrets['email']['SENDER_PASSWORD']
            }
        except Exception:
            return None
    
    def get_ai_config(self) -> Optional[Dict]:
        """Λήψη AI configuration"""
        if not self.features['ai']:
            return None
        
        try:
            return {
                'api_key': st.secrets['ai']['ANTHROPIC_API_KEY']
            }
        except Exception:
            return None
    
    def is_feature_enabled(self, feature: str) -> bool:
        """Έλεγχος αν ένα feature είναι enabled"""
        return self.features.get(feature, False)
    
    def get_feature_status_message(self) -> str:
        """Human-readable status message"""
        enabled = [k for k, v in self.features.items() if v]
        disabled = [k for k, v in self.features.items() if not v]
        
        msg = f"**Ενεργά Features:** {', '.join(enabled)}"
        if disabled:
            msg += f"\n\n**Απενεργοποιημένα:** {', '.join(disabled)}"
        
        return msg

# Singleton instance
_config_instance = None

def get_config() -> Config:
    """Get or create config instance"""
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance
