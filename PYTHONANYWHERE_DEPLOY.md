# CoreAPI — PythonAnywhere-ga Deploy Qilish Qo‘llanmasi

Ushbu qo‘llanma orqali CoreAPI loyihasini **PythonAnywhere** bepul yoki pullik xostingiga 10 daqiqada muammosiz joylashtirishingiz (deploy qilishingiz) mumkin.

---

## 1-qadam. PythonAnywhere-da loyihani yuklash

1. PythonAnywhere boshqaruv paneliga kiring va **Consoles** bo‘limidan **Bash** konsolini oching.
2. Loyihani yuklab oling (Git orqali yoki ZIP arxiv yuklab):
   ```bash
   cd ~
   git clone <sizning-github-repo-havolangiz> CoreAPI
   ```
   *Yoki ZIP fayl yuklagan bo‘lsangiz:*
   ```bash
   cd ~
   unzip CoreAPI.zip -d CoreAPI
   ```
3. Loyiha papkasiga kiring:
   ```bash
   cd ~/CoreAPI
   ```

---

## 2-qadam. Virtual muhit (Virtualenv) yaratish va paketlarni o‘rnatish

PythonAnywhere Bash konsolida quyidagi buyruqlarni bajaring:

```bash
# 1. Python 3.10 da virtual muhit yaratish
mkvirtualenv --python=python3.10 coreapi-venv

# (Agar virtual muhit faollashmagan bo‘lsa: workon coreapi-venv)

# 2. Pip-ni yangilash
pip install --upgrade pip

# 3. Barcha kerakli kutubxonalarni o‘rnatish
pip install -r requirements.txt
```

---

## 3-qadam. `.env` faylini sozlash

Loyiha papkasida maxfiy sozlamalar faylini yarating:

```bash
cp .env.example .env
nano .env
```

`.env` ichida quyidagi qatorlarni o‘zingizga moslang:
```env
DJANGO_SECRET_KEY=maxfiy-uzun-tasodifiy-kalit-yozing
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=yourusername.pythonanywhere.com,127.0.0.1,localhost
DJANGO_CSRF_TRUSTED_ORIGINS=https://yourusername.pythonanywhere.com

AI_PROVIDER_TYPE=groq
AI_PROVIDER_API_KEY=gsk_sizning_groq_api_kalitingiz
AI_PROVIDER_MODEL=openai/gpt-oss-20b
AI_PROVIDER_TIMEOUT=60
AI_RATE_LIMIT=20/minute
```
*Saqlash uchun: `Ctrl + O`, keyin `Enter`, chiqish uchun `Ctrl + X` bosing.*

---

## 4-qadam. Ma’lumotlar bazasi va Statik fayllarni yig‘ish

Bash konsolida quyidagilarni bajaring:

```bash
# Migratsiyalarni qo‘llash
python manage.py migrate

# CSS, JS va dizayn fayllarini yagona staticfiles papkasiga yig‘ish
python manage.py collectstatic --noinput
```

---

## 5-qadam. PythonAnywhere "Web" bo‘limini sozlash

PythonAnywhere veb-interfeysida yuqori menyudagi **Web** bo‘limiga o‘ting:

### A. Yangi Web App yaratish (agar yaratilmagan bo‘lsa)
1. **"Add a new web app"** tugmasini bosing.
2. Domen nomi: `yourusername.pythonanywhere.com` (Next bosing).
3. Freymvork tanlash: **Manual configuration** ni tanlang (Django ni tanlamang!).
4. Python versiyasi: **Python 3.10** ni tanlang va Next bosing.

---

### B. Kod va Virtualenv yo‘llarini kiritish
Ochilgan sahifadagi bo‘limlarni quyidagicha to‘ldiring:

1. **Code:**
   - **Source code:** `/home/<yourusername>/CoreAPI`
   - **Working directory:** `/home/<yourusername>/CoreAPI`
   - **WSGI configuration file:** Ushbu havolani bosing (masalan, `/var/www/<yourusername>_pythonanywhere_com_wsgi.py`).
     - Ichidagi barcha yozuvlarni tozalang.
     - Loyihamizdagi `pythonanywhere_wsgi.py` fayli tarkibini ko‘chirib qo‘ying.
     - `USERNAME = 'YOUR_USERNAME'` qatoridagi `'YOUR_USERNAME'` o‘rniga o‘zingizning PythonAnywhere foydalanuvchi nomingizni yozing.
     - Sahifaning yuqori o‘ng burchagidagi **Save** tugmasini bosing.

2. **Virtualenv:**
   - Havolani bosing va quyidagi yo‘lni kiriting:
     ```
     /home/<yourusername>/.virtualenvs/coreapi-venv
     ```
   - Ko‘k belgi (galochka) paydo bo‘lib, to‘g‘ri qabul qilinganini tasdiqlaydi.

3. **Static files (Dizayn va uslublar to‘g‘ri ochilishi uchun SHART):**
   - **URL:** `/static/`
   - **Directory:** `/home/<yourusername>/CoreAPI/staticfiles`

4. **Security:**
   - **Force HTTPS:** Tugmasini **Enabled** (yoqilgan) holatiga o‘tkazing.

---

## 6-qadam. Serverni qayta ishga tushirish (Reload)

Sahifaning eng yuqori qismidagi yashil rangli **"Reload <yourusername>.pythonanywhere.com"** tugmasini bosing!

Tabriklaymiz! Endi brauzerda `https://<yourusername>.pythonanywhere.com` manziliga kirsangiz:
- CoreAPI veb-sayti
- Interaktiv API Playground
- `/docs/` — To‘liq hujjatlar
- `/api/swagger/` — OpenAPI Swagger UI
- `POST /api/v1/chat/` — AI REST API endpointi

to‘liq va xavfsiz ishlayotgan bo‘ladi.
