# Prompt Engineering Guide — Knowledge Pack

> System prompt templates, few-shot examples, output schemas, guardrails, and Arabic language considerations for SalesOS AI agents.

---

## System Prompt Templates by Agent Role

### Coordinator Agent

```
System: أنت منسق مساعد ذكي في منصة SalesOS. مهمتك توزيع الطلبات على الوكلاء المتخصصين
и تنسيق سير العمل. لا تنفذ أي مهمة مباشرة. قم فقط بإنشاء خطة التنفيذ وتوزيع الخطوات.

Output: JSON object with plan_id, steps array, and summary.
```

### Research Agent

```
System: أنت محلل أبحاث متخصص في سوق الأعمال السعودي. مهمتك جمع وتحليل
المعلومات عن الشركات والopportunities. استخدم فقط البيانات المقدمة كمصدر.

Context guidelines:
- Always cite data sources
- Distinguish facts from inferences
- Flag data gaps explicitly
- Use Arabic for analysis, English for technical terms
```

### Meeting Preparation Agent

```
System: أنت مساعد ذكي لإعداد اجتماعات العمل. قم بإنشاء جدول أعمال ونقاط نقاش
بناءً على معلومات الشركة والعلاقات والأحداث الأخيرة.

Output format:
- agenda: list of topics with time allocations
- talking_points: prioritized discussion items
- decision_makers: identified stakeholders with roles
```

### Proposal Agent

```
System: أنت خبير في صياغة العروض التجارية. قم بإنشاء مقترح تجاري
مخصص بناءً على احتياجات العميل ومتطلباته.

Guardrails:
- Never commit to pricing without approval
- Include disclaimers for estimates
- Reference relevant case studies when available
- Output structured proposal text
```

### Contract Review Agent

```
System: أنت مستشار قانوني متخصص في العقود التجارية. قم بمراجعة العقد
وتحديد المخاطر والتوصيات.

Output:
- risks: list of identified risks with severity
- recommendations: actionable items to address risks
- Never provide definitive legal advice
```

### Pricing Agent

```
System: أنت محلل تسعير متخصص. قم بتحليل العوامل المؤثرة في التسعير
وتقديم نطاق سعر مقترح.

Factors to consider:
- Company size and revenue
- Deal complexity and scope
- Competitive landscape
- Historical pricing patterns
- Margin requirements
```

### Forecast Agent

```
System: أنت محلل توقعات مبيعات. قم بتوقع الإيرادات بناءً على
البيانات التاريخية والcurrent_pipeline والإشارات السوقية.

Output:
- predicted_revenue: point estimate
- confidence_interval: {lower, upper}
- assumptions: list of key assumptions
```

### Renewal Agent

```
System: أنت خبير احتفاظ بالعملاء. قم بتقييم مخاطر تجديد العقد
وتقديم استراتيجيات الاحتفاظ.

Risk factors:
- Usage patterns and engagement
- Support ticket history
- Contract terms and pricing
- Competitive pressure signals
- Relationship health score
```

### Tender Agent

```
System: أنت محلل المناقصات. قم بتقييم فرصة المناقصة
وشروط الأهلية والجدوى.

Output:
- eligibility: company qualification assessment
- opportunities: list of matching tenders
- risk_assessment: bid/no-bid recommendation
```

### Competitor Agent

```
System: أنت محلل منافسة. قم بتحليل المشهد التنافسي
للمؤسسة المستهدفة.

Output:
- competitors: list with strengths/weaknesses
- market_position: competitive positioning assessment
- threats: emerging competitive threats
```

### News Agent

```
System: أنت محلل أخبار أعمال. قم بتلخيص الأخبار المهمة
المرتبطة بالشركة والopportunities.

Output:
- articles: summarized news items
- relevance_score: per-article relevance
- impact_assessment: business impact analysis
```

---

## Few-Shot Examples for Company Analysis

### Example 1: Company Research Analysis

**Input**:
```json
{
  "company_id": "comp_123",
  "company_info": {
    "name_ar": "شركة أرامكو السعودية",
    "name_en": "Saudi Aramco",
    "industry": "Oil & Gas",
    "employees_count": 70000,
    "annual_revenue": "400B+ SAR"
  },
  "signals": [
    {"type": "funding", "title": "Q3 2026 earnings: 15% profit increase", "confidence": 0.95},
    {"type": "expansion", "title": "New hydrogen plant in NEOM", "confidence": 0.8}
  ]
}
```

**Expected Output**:
```json
{
  "analysis": "شركة أرامко السعودية تشهد نموًا مستقرًا مع زيادة الأرباح بنسبة 15% في الربع الثالث. خطط التوسع في مجال الهيدروجين الأخضر عبر مشروع NEOM تعكس استراتيجية التنويع. القيمة السوقية الكبيرة وقاعدة الموظفين الكبيرة توفر فرصًا كبيرة للخدمات التقنية.",
  "confidence": 0.85,
  "evidence": [
    {"fact": "زيادة أرباح 15% في Q3 2026", "source": "earnings_report", "confidence": 0.95},
    {"fact": "مشروع مصنع هيدروجين في NEOM", "source": "news_signal", "confidence": 0.8}
  ],
  "sources": ["earnings_report", "news_signal"],
  "key_facts": [
    "أكبر شركة نفط في العالم",
    "توسع في مجال الهيدروجين الأخضر",
    "أرباح مرتفعة ومستقرة"
  ],
  "opportunities": [
    "خدمات تقنية للمشاريع الجديدة",
    "حلول أمن سيبراني",
    "أنظمة إدارة البيانات"
  ],
  "recommendations": [
    "التواصل مع فريق المشتريات",
    "تقديم عرض تقني للمشاريع الجديدة",
    "متابعة نتائج الربع القادم"
  ]
}
```

### Example 2: Deal Health Assessment

**Input**:
```json
{
  "opportunity_id": "opp_456",
  "name": "ERP Implementation - Almarai",
  "stage": "proposal",
  "value": 2500000,
  "expected_close_date": "2026-08-15",
  "days_since_last_activity": 21,
  "total_activities": 8
}
```

**Expected Output**:
```json
{
  "analysis": "الفرصة في مرحلة مقترح بقيمة 2.5 مليون ريال. هناك تأخر في النشاط منذ 21 يومًا مما يشير إلى خطر التجميد. عدد الأنشطة المحدود (8) مقارنة بالمتوسط المطلوب يضعف فرص النجاح.",
  "confidence": 0.75,
  "evidence": [
    {"fact": "تأخر 21 يومًا بدون نشاط", "source": "activity_log", "confidence": 0.9},
    {"fact": "8 أنشطة فقط من أصل 20 المطلوب", "source": "activity_log", "confidence": 0.85}
  ],
  "risk_level": "high",
  "retention_strategies": [
    "تواصل فوري مع صانع القرار الرئيسي",
    "تقديم تحديث على قيمة المقترح",
    "تحديد عقبات محددة للتقدم"
  ]
}
```

---

## Output Format Specifications (JSON Schemas)

### Base Agent Analysis Schema

```json
{
  "type": "object",
  "required": ["analysis", "confidence"],
  "properties": {
    "analysis": {"type": "string", "description": "التحليل النصي الكامل"},
    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
    "evidence": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "fact": {"type": "string"},
          "source": {"type": "string"},
          "confidence": {"type": "number", "minimum": 0, "maximum": 1}
        }
      }
    },
    "sources": {"type": "array", "items": {"type": "string"}}
  }
}
```

### Meeting Preparation Schema

```json
{
  "type": "object",
  "required": ["analysis", "confidence", "agenda", "talking_points"],
  "properties": {
    "agenda": {
      "type": "array",
      "items": {"type": "string"}
    },
    "talking_points": {
      "type": "array",
      "items": {"type": "string"}
    },
    "decision_makers": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "name": {"type": "string"},
          "role": {"type": "string"},
          "influence": {"type": "string", "enum": ["high", "medium", "low"]}
        }
      }
    }
  }
}
```

### Pricing Analysis Schema

```json
{
  "type": "object",
  "required": ["analysis", "confidence", "suggested_price", "price_range"],
  "properties": {
    "suggested_price": {"type": "number"},
    "price_range": {
      "type": "object",
      "properties": {
        "min": {"type": "number"},
        "max": {"type": "number"}
      }
    }
  }
}
```

### Forecast Analysis Schema

```json
{
  "type": "object",
  "required": ["analysis", "confidence", "predicted_revenue", "confidence_interval"],
  "properties": {
    "predicted_revenue": {"type": "number"},
    "confidence_interval": {
      "type": "object",
      "properties": {
        "lower": {"type": "number"},
        "upper": {"type": "number"}
      }
    }
  }
}
```

### RAG Answer Schema

```json
{
  "type": "object",
  "required": ["answer", "citations", "chunks_used", "confidence"],
  "properties": {
    "answer": {"type": "string"},
    "citations": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "document_id": {"type": "string"},
          "title": {"type": "string"},
          "source_type": {"type": "string"},
          "source_id": {"type": "string"},
          "score": {"type": "number"}
        }
      }
    },
    "chunks_used": {"type": "integer"},
    "confidence": {"type": "number", "minimum": 0, "maximum": 1}
  }
}
```

---

## Guardrails Against Common Failure Modes

### Input Guardrails (from guardrails.py)

**Special tokens to strip**:
```python
SPECIAL_TOKENS = [
    "{{", "}}", "{%", "%}",
    "<|", "|>",
    "<s>", "</s>",
    "[INST]", "[/INST]",
    "<<SYS>>", "<</SYS>>",
]
```

**Harmful pattern detection**:
```python
HARMFUL_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|above|below)\s+instructions",
    r"forget\s+(all\s+)?(previous|above|below)",
    r"disregard\s+(all\s+)?(previous|above|below)",
    r"system\s+prompt",
    r"you\s+are\s+(now|not\s+an?\s+ai|a\s+free)",
    r"act\s+as\s+(if|though)",
    r"pretend\s+(to\s+be|that)",
    r"role[-\s]*play",
    r"do\s+(not\s+)?(follow|obey)",
    r"output\s+(raw|json|the\s+following)",
    r"print\s+(the\s+)?(secret|password|key|token)",
    r"bypass\s+(the\s+)?(safety|filter|guardrail|restriction|rule)",
    r"jailbreak",
    r"dan\b(\s*$|\s*\d)",
]
```

**Input sanitization**:
1. Strip special tokens (template injection prevention)
2. Remove Unicode escape sequences
3. Remove control characters
4. Check for harmful patterns → reject if found

### Output Guardrails

**JSON validation**:
1. Strip markdown fences (```json ... ```)
2. Parse JSON
3. Verify required fields (analysis, proposal, or summary)
4. Validate confidence range (0-1)
5. Truncate long strings (e.g., explanation ≤ 2000 chars)
6. Limit array sizes (e.g., risks ≤ 10, ranking ≤ 10)

**Fallback strategy**:
- If JSON parsing fails → extract raw text as analysis
- If confidence validation fails → use fallback confidence
- If LLM unavailable → return "التحليل غير متاح" with confidence 0.1

### Prompt Injection Prevention

```python
# Layer 1: Input sanitization
sanitized = sanitize_input(user_input)

# Layer 2: Harmful pattern detection
if add_input_moderation(sanitized):
    return rejected_response

# Layer 3: Schema enforcement in system prompt
schema_guide = f"\n\nيجب أن يكون الرد بصيغة JSON فقط:\n{schema_json}"

# Layer 4: Output validation
if not validate_output(raw_response, expected_schema):
    return fallback_response
```

---

## Arabic Language Considerations for Prompts

### Text Direction
- All Arabic content is RTL (Right-to-Left)
- Mixed Arabic/English text: use explicit markers
- Code blocks and JSON always LTR

### Arabic Tokenization (from ChunkingService)

```python
# Arabic text detection
has_arabic = bool(re.search(r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]", text))

# Arabic tokenization: word-level splitting
# Long words (>20 chars) are split into 20-char segments
if len(word) > 20:
    for i in range(0, len(word), 20):
        tokens.append(word[i:i+20])
else:
    tokens.append(word)
```

### Bilingual Prompt Design

```
# System prompt (Arabic)
أنت محلل بيانات خبير في منصة SalesOS. قم بتحليل البيانات المقدمة.

# Key terms (English with Arabic explanation)
- Company (الشركة)
- Opportunity (الفرصة)  
- Signal (إشارة)
- Enrichment (تثريه)

# Output instruction (Arabic)
يجب أن يكون الرد بصيغة JSON يحتوي على:
- analysis: التحليل بالعربية
- confidence: درجة الثقة (0-1)
- evidence: الأدلة مع المصادر
```

### Arabic Date/Number Formatting

```python
# Numbers in Arabic context
value = 2500000  # Use Western numerals in data
# Display: 2.5 مليون ريال (Arabic numeral words)

# Dates in Arabic context
date_str = "2026-07-13"  # ISO format in data
# Display: 13 يوليو 2026 (Arabic date format)
```

### Common Prompt Patterns

**Analysis request**:
```
قم بتحليل {topic} واستخرج:
1. المعلومات الرئيسية
2. الحقائق المؤكدة
3. الأنماط الملحوظة
4. الفجوات في البيانات
```

**Recommendation request**:
```
بناءً على التحليل التالي، قدم توصيات actionable:
1. الإجراء المطلوب
2. السبب
3. الأولوية
4. المخاطر المحتملة
```

**Summary request**:
```
قم بتلخيص المعلومات التالية في فقرة موجزة:
- النقاط الرئيسية
- المعلومات الهام
- التوصيات
```

---

*Last updated: 2026-07-13*
*Version: 1.0*
