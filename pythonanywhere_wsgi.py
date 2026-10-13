# +-----------------------------------------------------------------------------+
# | PythonAnywhere WSGI Konfiguratsiyasi (CoreAPI)                              |
# |                                                                             |
# | Ushbu fayl tarkibini PythonAnywhere boshqaruv panelidagi "Web" bo‘limida     |
# | joylashgan "WSGI configuration file" havolasini ochib, ichiga joylashtiring: |
# | (/var/www/<username>_pythonanywhere_com_wsgi.py)                            |
# +-----------------------------------------------------------------------------+

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# 1. 'YOUR_USERNAME' o‘rniga o‘zingizning PythonAnywhere foydalanuvchi nomingizni yozing
# Masalan: USERNAME = 'alisher' yoki USERNAME = 'shaxzod'
USERNAME = 'YOUR_USERNAME'

# 2. Loyiha papkasining PythonAnywheredagi to‘liq yo‘li
# Agar loyihani boshqa nomdagi papkaga yuklagan bo‘lsangiz, nomini moslang
PROJECT_DIR = f'/home/{USERNAME}/CoreAPI'

# 3. Loyiha papkasini Python qidiruv yo‘llariga (sys.path) qo‘shish
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

# 4. .env faylidagi maxfiy kalitlar va sozlamalarni yuklash
env_file = Path(PROJECT_DIR) / '.env'
if env_file.exists():
    load_dotenv(env_file)

# 5. Django sozlamalar modulini ko‘rsatish
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'

# 6. Django WSGI dasturini ishga tushirish
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
