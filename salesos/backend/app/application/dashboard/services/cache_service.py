STALE_TIME = {
    "mission-center": 60,
    "decision-queue": 60,
    "intelligence-feed": 30,
    "ai-brief": 300,
    "market-pulse": 120,
    "recent-activity": 60,
}


class CacheService:
    @staticmethod
    def get_stale_time(widget_id: str) -> int:
        return STALE_TIME.get(widget_id, 60)
