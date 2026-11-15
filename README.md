# Geo Surveying AI – مجلد واحد متكامل (GeoMasaha Pro)

جميع ملفات الواجهة الأمامية والخادم الخلفي مجمّعة في **هذا المجلد الواحد فقط** بدون أي مجلدات فرعية، وجاهزة للتشغيل المباشر.

## محتويات المجلد (16 ملفاً)
- **ملفات الواجهة الأمامية (تُضاف لموقع GitHub Pages):**
  1. `index-ai-snippet.html`: كود زر التبويب وقسم `Geo Surveying AI` لإضافته في `index.html`.
  2. `geomasaha-ai.js`: ملف البرمجة التفاعلي للواجهة.
- **ملفات الخادم الخلفي (Python FastAPI):**
  3. `main.py`: نقطة تشغيل الخادم.
  4. `routes.py`: روابط API ونظام الحصص وبوابات الدفع.
  5. `ai_orchestrator.py`: منسق الذكاء الاصطناعي (Gemini).
  6. `cad_engine.py`: محرك إنشاء لوحات AutoCAD (`DXF`).
  7. `gis_engine.py`: محرك الخرائط والتحليل المكاني (`GeoPandas / PyProj`).
  8. `surveying_calc.py`: الحاسبة المساحية (ميزانية، ترافيرس، UTM).
  9. `file_analyzer.py`: محلل ملفات Excel, CSV, PDF, DXF والصور.
  10. `database.py`: قاعدة البيانات والاشتراكات.
  11. `config.py` و `security.py`: الإعدادات والحماية.
  12. `requirements.txt` و `.env.example` و `test_geomasaha_ai.py`.

## خطوات التشغيل السريعة
```bash
pip install -r requirements.txt
cp .env.example .env
# ضع مفتاح GEMINI_API_KEY داخل .env
uvicorn main:app --host 0.0.0.0 --port 8000
```
