from datetime import datetime, timezone, timedelta
from typing import Any, Optional

from .schemas import (
    ActivityScore,
    MeetingLoad,
    TimeAllocation,
    WorkIntelligenceResponse,
    WorkRecommendation,
)


ACTIVITY_WEIGHTS = {
    "meeting": {"hours": 1.0, "category": "meeting"},
    "email": {"hours": 0.25, "category": "email"},
    "call": {"hours": 0.5, "category": "call"},
    "task": {"hours": 0.5, "category": "task"},
}

FOCUS_HOURS_PER_DAY = 5.0
WORK_HOURS_PER_DAY = 8.0


class WorkIntelligenceEngine:
    def __init__(self, activity_runtime: Any, logger: Any = None):
        self.activity_runtime = activity_runtime
        self.logger = logger

    async def analyze(
        self, employee_id: str, tenant_id: str, period_days: int = 30
    ) -> WorkIntelligenceResponse:
        now = datetime.now(timezone.utc)
        since = now - timedelta(days=period_days)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=today_start.weekday())

        try:
            items, total = await self.activity_runtime.query(
                tenant_id=tenant_id,
                actor=employee_id,
                since=since,
                limit=500,
            )
        except Exception:
            items = []
            total = 0

        time_alloc = self._compute_time_allocation(items)
        meeting_load = self._compute_meeting_load(items, today_start, week_start)
        activity_score = self._compute_activity_score(items, total, period_days)
        recommendations = self._generate_recommendations(time_alloc, meeting_load, activity_score, total)

        return WorkIntelligenceResponse(
            employee_id=employee_id,
            tenant_id=tenant_id,
            period_days=period_days,
            time_allocation=time_alloc,
            meeting_load=meeting_load,
            activity_score=activity_score,
            recommendations=recommendations,
            generated_at=now,
        )

    def _compute_time_allocation(self, items: list) -> TimeAllocation:
        meeting_hours = 0.0
        email_hours = 0.0
        call_hours = 0.0
        task_hours = 0.0

        for item in items:
            action = (item.get("action") or item.get("action", "")).lower()
            for key, config in ACTIVITY_WEIGHTS.items():
                if action.startswith(key):
                    hours = config["hours"]
                    cat = config["category"]
                    if cat == "meeting":
                        meeting_hours += hours
                    elif cat == "email":
                        email_hours += hours
                    elif cat == "call":
                        call_hours += hours
                    elif cat == "task":
                        task_hours += hours
                    break

        total_tracked = meeting_hours + email_hours + call_hours + task_hours
        focus_hours = max(0.0, FOCUS_HOURS_PER_DAY * 30 - total_tracked)

        return TimeAllocation(
            meeting_hours=round(meeting_hours, 1),
            email_hours=round(email_hours, 1),
            call_hours=round(call_hours, 1),
            task_hours=round(task_hours, 1),
            focus_hours=round(focus_hours, 1),
            total_tracked=round(total_tracked, 1),
        )

    def _compute_meeting_load(self, items: list, today_start: datetime, week_start: datetime) -> MeetingLoad:
        meetings_today = 0
        meetings_this_week = 0
        meetings_this_month = 0
        meeting_hours_this_week = 0.0

        for item in items:
            action = (item.get("action") or "").lower()
            if not action.startswith("meeting"):
                continue
            try:
                ts = item.get("timestamp")
                if isinstance(ts, str):
                    ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
            except (ValueError, AttributeError):
                ts = None

            if ts:
                if ts >= today_start:
                    meetings_today += 1
                if ts >= week_start:
                    meetings_this_week += 1
                    meeting_hours_this_week += 1.0
                if ts >= today_start - timedelta(days=30):
                    meetings_this_month += 1

        avg_per_day = round(meetings_this_month / 30.0, 1) if meetings_this_month > 0 else 0.0
        overbooked = meeting_hours_this_week > WORK_HOURS_PER_DAY * 2

        recommendation = ""
        if overbooked:
            recommendation = "أنت في اجتماعات كثيرة هذا الأسبوع. حاول تخصيص وقت للعمل المركز."
        elif meetings_this_week > 10:
            recommendation = "عدد الاجتماعات مرتفع. فكر في تقليلها لزيادة الإنتاجية."
        elif meetings_this_week > 5:
            recommendation = "جدول اجتماعات متوازن. استمر في الحفاظ على وقت للعمل الفردي."

        return MeetingLoad(
            meetings_today=meetings_today,
            meetings_this_week=meetings_this_week,
            meetings_this_month=meetings_this_month,
            avg_meetings_per_day=avg_per_day,
            total_meeting_hours_this_week=round(meeting_hours_this_week, 1),
            overbooked=overbooked,
            recommendation=recommendation,
        )

    def _compute_activity_score(self, items: list, total: int, period_days: int) -> ActivityScore:
        volume = min(total / (period_days * 5), 1.0) * 100 if period_days > 0 else 0

        action_types = set((item.get("action") or "").split("_")[0] for item in items if item.get("action"))
        variety = min(len(action_types) / 5.0, 1.0) * 100

        now = datetime.now(timezone.utc)
        recent_count = 0
        for item in items[:100]:
            try:
                ts = item.get("timestamp")
                if isinstance(ts, str):
                    ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                if ts and (now - ts).days <= 3:
                    recent_count += 1
            except (ValueError, AttributeError):
                pass
        recency = min(recent_count / 10.0, 1.0) * 100

        daily_counts = {}
        for item in items[:200]:
            try:
                ts = item.get("timestamp")
                if isinstance(ts, str):
                    ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                day_key = ts.strftime("%Y-%m-%d") if ts else "unknown"
                daily_counts[day_key] = daily_counts.get(day_key, 0) + 1
            except (ValueError, AttributeError):
                pass
        active_days = len(daily_counts)
        consistency = min(active_days / (period_days * 0.5), 1.0) * 100 if period_days > 0 else 0

        overall = round((volume * 0.3 + variety * 0.25 + recency * 0.25 + consistency * 0.2), 1)

        if overall >= 80:
            grade = "ممتاز"
        elif overall >= 60:
            grade = "جيد"
        elif overall >= 40:
            grade = "متوسط"
        elif overall >= 20:
            grade = "ضعيف"
        else:
            grade = "منخفض جدًا"

        return ActivityScore(
            overall=overall,
            volume=round(volume, 1),
            variety=round(variety, 1),
            recency=round(recency, 1),
            consistency=round(consistency, 1),
            grade=grade,
        )

    def _generate_recommendations(
        self,
        time_alloc: TimeAllocation,
        meeting_load: MeetingLoad,
        activity_score: ActivityScore,
        total_activities: int,
    ) -> list[WorkRecommendation]:
        recs = []

        if meeting_load.overbooked:
            recs.append(WorkRecommendation(
                type="reduce_meetings",
                title="قلل الاجتماعات",
                description=meeting_load.recommendation,
                priority="high",
                metric=f"{meeting_load.total_meeting_hours_this_week} ساعة هذا الأسبوع",
            ))

        if time_alloc.meeting_hours > time_alloc.focus_hours and time_alloc.meeting_hours > 20:
            recs.append(WorkRecommendation(
                type="meeting_vs_focus",
                title="وقت الاجتماعات يفوق وقت التركيز",
                description=f"{time_alloc.meeting_hours} ساعة اجتماعات مقابل {time_alloc.focus_hours} ساعة تركيز في آخر 30 يوم",
                priority="medium",
                metric=f"{time_alloc.meeting_hours}h اجتماعات / {time_alloc.focus_hours}h تركيز",
            ))

        if total_activities == 0:
            recs.append(WorkRecommendation(
                type="no_activity",
                title="لا توجد نشاطات مسجلة",
                description="ابدأ بتسجيل نشاطاتك اليومية لمتابعة إنتاجيتك",
                priority="high",
                metric="0 نشاط",
            ))
        elif activity_score.overall < 30:
            recs.append(WorkRecommendation(
                type="low_activity",
                title="نشاطات قليلة",
                description=f"نشاطك العام {activity_score.grade}. حاول زيادة التفاعل مع العملاء",
                priority="medium",
                metric=f"{activity_score.overall}/100",
            ))

        if activity_score.variety < 40:
            recs.append(WorkRecommendation(
                type="improve_variety",
                title="نوع النشاطات محدود",
                description="نوع النشاطات المسجلة قليل. حاول تنويع أنشطتك (مكالمات، إيميلات، اجتماعات)",
                priority="medium",
                metric=f"{activity_score.variety}/100",
            ))

        if activity_score.consistency >= 70 and activity_score.overall >= 60:
            recs.append(WorkRecommendation(
                type="on_track",
                title="أداء جيد",
                description="استمر في الحفاظ على وتيرة نشاطك الحالية",
                priority="low",
                metric=f"{activity_score.overall}/100",
            ))

        return recs
