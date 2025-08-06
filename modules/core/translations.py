#!/usr/bin/env python3
"""
Translation system for AVA OLO
Provides UI translations for all supported languages
"""

TRANSLATIONS = {
    'en': {
        # Landing Page
        'landing_title': 'AVA OLO',
        'landing_subtitle': 'Intelligent Agricultural Assistant',
        'sign_in_with_whatsapp': 'Sign In with WhatsApp',
        'new_with_ava': 'New with AVA OLO',
        'access_dashboard': 'Access your dashboard with:',
        'feature_weather': 'Real-time weather monitoring',
        'feature_cava': 'CAVA AI agricultural assistant',
        'feature_tools': 'Farm management tools',
        'feature_tracking': 'Field & crop tracking',
        
        # Sign In Page
        'sign_in_title': 'Sign In',
        'sign_in_subtitle': 'Agricultural Virtual Assistant Optimizing Land Operations',
        'whatsapp_label': 'WhatsApp Number',
        'whatsapp_placeholder': 'e.g., +359888123456',
        'password_label': 'Password',
        'password_placeholder': 'Enter your password',
        'sign_in_button': 'Sign In',
        'no_account': "Don't have an account?",
        'register_link': 'Register here',
        'forgot_password': 'Forgot password?',
        
        # Register Page
        'register_title': 'Create Account',
        'register_subtitle': 'Agricultural Virtual Assistant Optimizing Land Operations',
        'first_name_label': 'First Name',
        'first_name_placeholder': 'Enter your first name',
        'last_name_label': 'Last Name',
        'last_name_placeholder': 'Enter your last name',
        'email_label': 'Email',
        'email_placeholder': 'your@email.com',
        'confirm_password_label': 'Confirm Password',
        'confirm_password_placeholder': 'Re-enter your password',
        'register_button': 'Create Account',
        'have_account': 'Already have an account?',
        'signin_link': 'Sign in here',
        
        # Dashboard
        'dashboard_weather': 'Weather',
        'dashboard_chat': 'AVA Assistant',
        'dashboard_fields': 'Fields',
        'dashboard_messages': 'Messages',
        'dashboard_welcome_chat': 'Welcome to AVA!',
        'dashboard_chat_subtitle': 'Your agricultural assistant is here to help',
        'dashboard_ask_placeholder': 'Ask AVA about your farm...',
        'dashboard_send': 'Send',
        'dashboard_weather_unavailable': 'Weather data temporarily unavailable',
        'dashboard_24h_forecast': '24-Hour Forecast',
        'dashboard_5day_forecast': '5-Day Forecast',
        'dashboard_add_field': 'Add Field',
        'dashboard_no_fields': 'No fields added yet',
        'dashboard_field_area': 'Area',
        'dashboard_field_crop': 'Crop',
        'dashboard_field_last_task': 'Last Task',
        'dashboard_total_area': 'Total Area',
        'dashboard_total_fields': 'Total Fields',
        'dashboard_tasks': 'Tasks',
        
        # Common
        'error_invalid_whatsapp': 'Please enter a valid WhatsApp number',
        'error_invalid_password': 'Incorrect password',
        'error_no_account': 'No account found with this WhatsApp number',
        'error_passwords_mismatch': 'Passwords do not match',
        'error_password_too_short': 'Password must be at least 8 characters',
        'welcome': 'Welcome',
        'loading': 'Loading...',
    },
    
    'sl': {  # Slovenian
        # Landing Page
        'landing_title': 'AVA OLO',
        'landing_subtitle': 'Inteligentni kmetijski asistent',
        'sign_in_with_whatsapp': 'Prijavite se z WhatsApp',
        'new_with_ava': 'Novi pri AVA OLO',
        'access_dashboard': 'Dostopajte do svoje nadzorne plošče z:',
        'feature_weather': 'Spremljanje vremena v realnem času',
        'feature_cava': 'CAVA AI kmetijski asistent',
        'feature_tools': 'Orodja za upravljanje kmetije',
        'feature_tracking': 'Sledenje poljem in pridelkom',
        
        # Sign In Page
        'sign_in_title': 'Prijava',
        'sign_in_subtitle': 'Dobrodošli nazaj v AVA OLO',
        'whatsapp_label': 'WhatsApp številka',
        'whatsapp_placeholder': 'npr. +38640123456',
        'password_label': 'Geslo',
        'password_placeholder': 'Vnesite svoje geslo',
        'sign_in_button': 'Prijava',
        'no_account': 'Nimate računa?',
        'register_link': 'Registrirajte se tukaj',
        'forgot_password': 'Pozabljeno geslo?',
        
        # Register Page
        'register_title': 'Ustvari račun',
        'register_subtitle': 'Pridružite se portalu AVA OLO za kmete',
        'first_name_label': 'Ime',
        'first_name_placeholder': 'Vnesite svoje ime',
        'last_name_label': 'Priimek',
        'last_name_placeholder': 'Vnesite svoj priimek',
        'email_label': 'E-pošta',
        'email_placeholder': 'vas@email.com',
        'confirm_password_label': 'Potrdi geslo',
        'confirm_password_placeholder': 'Ponovno vnesite geslo',
        'register_button': 'Ustvari račun',
        'have_account': 'Že imate račun?',
        'signin_link': 'Prijavite se tukaj',
        
        # Dashboard
        'dashboard_weather': 'Vreme',
        'dashboard_chat': 'AVA Asistent',
        'dashboard_fields': 'Polja',
        'dashboard_messages': 'Sporočila',
        'dashboard_welcome_chat': 'Dobrodošli v AVA!',
        'dashboard_chat_subtitle': 'Vaš kmetijski asistent je tukaj, da vam pomaga',
        'dashboard_ask_placeholder': 'Vprašajte AVA o vaši kmetiji...',
        'dashboard_send': 'Pošlji',
        'dashboard_weather_unavailable': 'Vremenski podatki trenutno niso na voljo',
        'dashboard_24h_forecast': '24-urna napoved',
        'dashboard_5day_forecast': '5-dnevna napoved',
        'dashboard_add_field': 'Dodaj polje',
        'dashboard_no_fields': 'Še ni dodanih polj',
        'dashboard_field_area': 'Površina',
        'dashboard_field_crop': 'Pridelek',
        'dashboard_field_last_task': 'Zadnje opravilo',
        'dashboard_total_area': 'Skupna površina',
        'dashboard_total_fields': 'Skupno polj',
        'dashboard_tasks': 'Opravila',
        
        # Common
        'error_invalid_whatsapp': 'Prosimo, vnesite veljavno WhatsApp številko',
        'error_invalid_password': 'Napačno geslo',
        'error_no_account': 'Ni najdenega računa s to WhatsApp številko',
        'error_passwords_mismatch': 'Gesli se ne ujemata',
        'error_password_too_short': 'Geslo mora imeti vsaj 8 znakov',
        'welcome': 'Dobrodošli',
        'loading': 'Nalaganje...',
    },
    
    'bg': {  # Bulgarian
        # Landing Page
        'landing_title': 'AVA OLO',
        'landing_subtitle': 'Интелигентен земеделски асистент',
        'sign_in_with_whatsapp': 'Влезте с WhatsApp',
        'new_with_ava': 'Нов в AVA OLO',
        'access_dashboard': 'Достъп до вашето табло с:',
        'feature_weather': 'Наблюдение на времето в реално време',
        'feature_cava': 'CAVA AI земеделски асистент',
        'feature_tools': 'Инструменти за управление на фермата',
        'feature_tracking': 'Проследяване на полета и култури',
        
        # Sign In Page
        'sign_in_title': 'Вход',
        'sign_in_subtitle': 'Добре дошли отново в AVA OLO',
        'whatsapp_label': 'WhatsApp номер',
        'whatsapp_placeholder': 'напр. +359888123456',
        'password_label': 'Парола',
        'password_placeholder': 'Въведете паролата си',
        'sign_in_button': 'Вход',
        'no_account': 'Нямате акаунт?',
        'register_link': 'Регистрирайте се тук',
        'forgot_password': 'Забравена парола?',
        
        # Register Page
        'register_title': 'Създаване на акаунт',
        'register_subtitle': 'Присъединете се към портала за фермери AVA OLO',
        'first_name_label': 'Име',
        'first_name_placeholder': 'Въведете вашето име',
        'last_name_label': 'Фамилия',
        'last_name_placeholder': 'Въведете вашата фамилия',
        'email_label': 'Имейл',
        'email_placeholder': 'вашият@имейл.com',
        'confirm_password_label': 'Потвърдете паролата',
        'confirm_password_placeholder': 'Въведете отново паролата',
        'register_button': 'Създай акаунт',
        'have_account': 'Вече имате акаунт?',
        'signin_link': 'Влезте тук',
        
        # Common
        'error_invalid_whatsapp': 'Моля, въведете валиден WhatsApp номер',
        'error_invalid_password': 'Грешна парола',
        'error_no_account': 'Няма намерен акаунт с този WhatsApp номер',
        'error_passwords_mismatch': 'Паролите не съвпадат',
        'error_password_too_short': 'Паролата трябва да е поне 8 символа',
        'welcome': 'Добре дошли',
        'loading': 'Зареждане...',
    },
    
    'hr': {  # Croatian
        # Landing Page
        'landing_title': 'AVA OLO',
        'landing_subtitle': 'Inteligentni poljoprivredni asistent',
        'sign_in_with_whatsapp': 'Prijavite se s WhatsApp',
        'new_with_ava': 'Novi u AVA OLO',
        'access_dashboard': 'Pristupite svojoj kontrolnoj ploči s:',
        'feature_weather': 'Praćenje vremena u stvarnom vremenu',
        'feature_cava': 'CAVA AI poljoprivredni asistent',
        'feature_tools': 'Alati za upravljanje farmom',
        'feature_tracking': 'Praćenje polja i usjeva',
        
        # Sign In Page
        'sign_in_title': 'Prijava',
        'sign_in_subtitle': 'Dobrodošli natrag u AVA OLO',
        'whatsapp_label': 'WhatsApp broj',
        'whatsapp_placeholder': 'npr. +385911234567',
        'password_label': 'Lozinka',
        'password_placeholder': 'Unesite svoju lozinku',
        'sign_in_button': 'Prijava',
        'no_account': 'Nemate račun?',
        'register_link': 'Registrirajte se ovdje',
        'forgot_password': 'Zaboravljena lozinka?',
        
        # Register Page
        'register_title': 'Stvori račun',
        'register_subtitle': 'Pridružite se AVA OLO portalu za poljoprivrednike',
        'first_name_label': 'Ime',
        'first_name_placeholder': 'Unesite svoje ime',
        'last_name_label': 'Prezime',
        'last_name_placeholder': 'Unesite svoje prezime',
        'email_label': 'E-pošta',
        'email_placeholder': 'vaš@email.com',
        'confirm_password_label': 'Potvrdi lozinku',
        'confirm_password_placeholder': 'Ponovno unesite lozinku',
        'register_button': 'Stvori račun',
        'have_account': 'Već imate račun?',
        'signin_link': 'Prijavite se ovdje',
        
        # Common
        'error_invalid_whatsapp': 'Molimo unesite valjan WhatsApp broj',
        'error_invalid_password': 'Pogrešna lozinka',
        'error_no_account': 'Nema pronađenog računa s ovim WhatsApp brojem',
        'error_passwords_mismatch': 'Lozinke se ne podudaraju',
        'error_password_too_short': 'Lozinka mora imati najmanje 8 znakova',
        'welcome': 'Dobrodošli',
        'loading': 'Učitavanje...',
    },
    
    'de': {  # German
        # Landing Page
        'landing_title': 'AVA OLO',
        'landing_subtitle': 'Intelligenter Landwirtschaftsassistent',
        'sign_in_with_whatsapp': 'Mit WhatsApp anmelden',
        'new_with_ava': 'Neu bei AVA OLO',
        'access_dashboard': 'Zugriff auf Ihr Dashboard mit:',
        'feature_weather': 'Echtzeit-Wetterüberwachung',
        'feature_cava': 'CAVA KI-Landwirtschaftsassistent',
        'feature_tools': 'Farm-Management-Tools',
        'feature_tracking': 'Feld- und Ernteverfolgung',
        
        # Sign In Page
        'sign_in_title': 'Anmelden',
        'sign_in_subtitle': 'Willkommen zurück bei AVA OLO',
        'whatsapp_label': 'WhatsApp-Nummer',
        'whatsapp_placeholder': 'z.B. +43664123456',
        'password_label': 'Passwort',
        'password_placeholder': 'Passwort eingeben',
        'sign_in_button': 'Anmelden',
        'no_account': 'Noch kein Konto?',
        'register_link': 'Hier registrieren',
        'forgot_password': 'Passwort vergessen?',
        
        # Register Page
        'register_title': 'Konto erstellen',
        'register_subtitle': 'Treten Sie dem AVA OLO Bauernportal bei',
        'first_name_label': 'Vorname',
        'first_name_placeholder': 'Geben Sie Ihren Vornamen ein',
        'last_name_label': 'Nachname',
        'last_name_placeholder': 'Geben Sie Ihren Nachnamen ein',
        'email_label': 'E-Mail',
        'email_placeholder': 'ihre@email.com',
        'confirm_password_label': 'Passwort bestätigen',
        'confirm_password_placeholder': 'Passwort erneut eingeben',
        'register_button': 'Konto erstellen',
        'have_account': 'Haben Sie bereits ein Konto?',
        'signin_link': 'Hier anmelden',
        
        # Common
        'error_invalid_whatsapp': 'Bitte geben Sie eine gültige WhatsApp-Nummer ein',
        'error_invalid_password': 'Falsches Passwort',
        'error_no_account': 'Kein Konto mit dieser WhatsApp-Nummer gefunden',
        'error_passwords_mismatch': 'Passwörter stimmen nicht überein',
        'error_password_too_short': 'Passwort muss mindestens 8 Zeichen lang sein',
        'welcome': 'Willkommen',
        'loading': 'Wird geladen...',
    },
    
    'it': {  # Italian
        # Landing Page
        'landing_title': 'AVA OLO',
        'landing_subtitle': 'Assistente agricolo intelligente',
        'sign_in_with_whatsapp': 'Accedi con WhatsApp',
        'new_with_ava': 'Nuovo su AVA OLO',
        'access_dashboard': 'Accedi alla tua dashboard con:',
        'feature_weather': 'Monitoraggio meteo in tempo reale',
        'feature_cava': 'CAVA assistente agricolo AI',
        'feature_tools': 'Strumenti di gestione agricola',
        'feature_tracking': 'Tracciamento campi e colture',
        
        # Sign In Page
        'sign_in_title': 'Accedi',
        'sign_in_subtitle': 'Bentornato su AVA OLO',
        'whatsapp_label': 'Numero WhatsApp',
        'whatsapp_placeholder': 'es. +393331234567',
        'password_label': 'Password',
        'password_placeholder': 'Inserisci la tua password',
        'sign_in_button': 'Accedi',
        'no_account': 'Non hai un account?',
        'register_link': 'Registrati qui',
        'forgot_password': 'Password dimenticata?',
        
        # Register Page
        'register_title': 'Crea account',
        'register_subtitle': 'Unisciti al portale agricoltori AVA OLO',
        'first_name_label': 'Nome',
        'first_name_placeholder': 'Inserisci il tuo nome',
        'last_name_label': 'Cognome',
        'last_name_placeholder': 'Inserisci il tuo cognome',
        'email_label': 'Email',
        'email_placeholder': 'tua@email.com',
        'confirm_password_label': 'Conferma password',
        'confirm_password_placeholder': 'Reinserisci la password',
        'register_button': 'Crea account',
        'have_account': 'Hai già un account?',
        'signin_link': 'Accedi qui',
        
        # Common
        'error_invalid_whatsapp': 'Inserisci un numero WhatsApp valido',
        'error_invalid_password': 'Password errata',
        'error_no_account': 'Nessun account trovato con questo numero WhatsApp',
        'error_passwords_mismatch': 'Le password non corrispondono',
        'error_password_too_short': 'La password deve essere di almeno 8 caratteri',
        'welcome': 'Benvenuto',
        'loading': 'Caricamento...',
    }
}

class TranslationDict:
    """Wrapper to allow both dict and attribute access to translations"""
    def __init__(self, translations):
        self._translations = translations
    
    def __getattr__(self, key):
        """Allow attribute-style access (t.key)"""
        return self._translations.get(key, f'[{key}]')
    
    def __getitem__(self, key):
        """Allow dict-style access (t['key'])"""
        return self._translations.get(key, f'[{key}]')
    
    def get(self, key, default=None):
        """Dict-like get method"""
        return self._translations.get(key, default)
    
    def __bool__(self):
        """Return True if translations exist"""
        return bool(self._translations)
    
    def __repr__(self):
        return f"TranslationDict({list(self._translations.keys())[:5]}...)"

def get_translations(language_code: str = 'en'):
    """Get translations for a specific language"""
    trans_dict = TRANSLATIONS.get(language_code, TRANSLATIONS['en'])
    return TranslationDict(trans_dict)