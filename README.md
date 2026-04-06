# 🛡️ PyAnalyzer — Python kodi tahlil tizimi

Python dastur kodida sintaksis xatolari va xavfsizlik zaifliklarini aniqlash uchun yaratilgan **Full-stack MVP tizim**.

## Arxitektura

```
pyanalyzer/
├── backend/                   # FastAPI backend qismi
│   ├── app/
│   │   ├── main.py            # Ilovaning asosiy kirish nuqtasi + CORS + loglash
│   │   ├── routers/
│   │   │   ├── analyze_text.py    # POST /analyze/text
│   │   │   ├── analyze_file.py    # POST /analyze/file
│   │   │   ├── analyze_zip.py     # POST /analyze/zip
│   │   │   └── analyze_github.py  # POST /analyze/github
│   │   ├── services/
│   │   │   ├── syntax_checker.py   # AST asosida sintaksis tahlili
│   │   │   ├── security_checker.py # Xavfsizlik muammolarini aniqlash
│   │   │   ├── file_handler.py     # Vaqtinchalik fayllar bilan ishlash
│   │   │   ├── zip_handler.py      # ZIP arxivlarini ochish
│   │   │   ├── github_cloner.py    # GitHub repozitoriyasini klonlash va .py fayllarni topish
│   │   │   ├── report_generator.py # Tahlil natijalarini yig‘ish
│   │   │   └── ai_explainer.py     # (Kelajakda AI integratsiyasi uchun)
│   │   └── models/
│   │       └── analysis_result.py  # Pydantic modellari
│   ├── logs/                  # system.log va errors.log
│   ├── temp/                  # Avtomatik tozalanadigan vaqtinchalik fayllar
│   ├── requirements.txt
│   └── Dockerfile
└── frontend/
    └── index.html             # React SPA (bitta fayl, build jarayoni kerak emas)
```

## Tez ishga tushirish (Quick Start)

### 1. Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API hujjatlari quyidagi manzilda mavjud:
http://localhost:8000/docs

### 2. Frontend

`frontend/index.html` faylini brauzer orqali ochish kifoya.
Hech qanday build jarayoni talab qilinmaydi — React CDN orqali ishlaydi.

Yoki server orqali ishga tushirish mumkin:

```bash
cd frontend
python -m http.server 3000
```

So‘ng brauzerda oching:
http://localhost:3000

### 3. Docker (faqat Backend)

```bash
cd backend
docker build -t pyanalyzer-api .
docker run -p 8000:8000 pyanalyzer-api
```

## API Endpointlar

| Method | Endpoint        | Tavsifi                                       |
| ------ | --------------- | --------------------------------------------- |
| POST   | /analyze/text   | Python kodini matn sifatida tahlil qilish     |
| POST   | /analyze/file   | `.py` fayl yuklab tahlil qilish               |
| POST   | /analyze/zip    | `.zip` arxivni yuklab tahlil qilish           |
| POST   | /analyze/github | GitHub repozitoriyasini klonlab tahlil qilish |
| GET    | /health         | Tizim holatini tekshirish                     |

## Xavfsizlik aniqlashlari

Tizim quyidagi xavfli kodlarni aniqlaydi:

* `eval()` va `exec()` ishlatilishi — **Yuqori xavf**
* `subprocess` moduli ishlatilishi — **Yuqori / O‘rta xavf**
* Kod ichida yozilgan parollar, API kalitlar, tokenlar — **Yuqori xavf**
* `__import__()` orqali dinamik import — **O‘rta xavf**
* `open()` orqali fayl operatsiyalari — **Past xavf**
* Sintaksis xatolari — **Yuqori daraja**

## So‘rov namunasi

```bash
curl -X POST http://localhost:8000/analyze/text \
  -H "Content-Type: application/json" \
  -d '{"code": "eval(input())\npassword=\"abc123\""}'
```

## Log fayllari

* `backend/logs/system.log` — tizimdagi barcha hodisalar
* `backend/logs/errors.log` — faqat xatolar

## Kelajakda: AI integratsiyasi

`app/services/ai_explainer.py` fayli kelajakda **AI API** bilan ulanish uchun tayyorlangan.

Masalan:

* muammolarni tabiiy tilda tushuntirish
* kodni qanday tuzatish bo‘yicha tavsiyalar
* xavfsizlik darajasini baholash
