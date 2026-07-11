# SalesOS Expansion — Architecture

> Post-v1.0 — Next Horizons
> Last Updated: 2026-07-11

---

## 1. 📱 Mobile (PWA)

| المكون | الوصف |
|--------|-------|
| Service Worker | Caching static assets + API responses |
| Manifest | اسم التطبيق، الأيقونات، splash screen |
| Push Notifications | إشعارات NBA + المهام |
| Touch | تحسين اللمس للجوال |
| Responsive | Grid → Single column للشاشات الصغيرة |

### التنفيذ
```bash
npm install next-pwa
# إضافة next-pwa إلى next.config.js
# إنشاء public/manifest.json
```

---

## 2. 🤖 AI Agents

| الـ Agent | الوظيفة | يبني على |
|-----------|---------|---------|
| Sales Agent | يتصرف نيابة عن المندوب | NBA Engine |
| Meeting Agent | يجهز إيجاز الاجتماع | Meeting Intelligence |
| Email Agent | يقترح ردود ذكية | Email Intelligence |
| Signal Agent | يراقب الإشارات وينبه | Signals Feed |

### التنفيذ
- LLM integration (OpenAI / Anthropic)
- RAG pipeline مع Company DNA
- Agent Memory (سجل القرارات السابقة)

---

## 3. 🌍 i18n (English)

| الملف | الوصف |
|-------|-------|
| `locales/ar.json` | جميع النصوص بالعربية |
| `locales/en.json` | جميع النصوص بالإنجليزية |
| `useTranslation()` | Hook للتبديل بين اللغات |

### الـ Widgets المتأثرة
جميع الـ 51 ويدجت — النصوص الثابتة تحتاج إلى استخراج إلى ملفات locales.

---

## 4. 🔌 MCP (Model Context Protocol)

| التكامل | الوصف |
|---------|-------|
| Odoo ERP | مزامنة الشركات والعملاء |
| Power BI | تصدير التقارير |
| Slack | إشعارات الفرق |
| Google Drive | ربط المستندات |

### التنفيذ
```typescript
interface MCPConnection {
  name: string
  type: string
  status: 'connected' | 'disconnected' | 'error'
  lastSync?: string
  entities: number
}
```
