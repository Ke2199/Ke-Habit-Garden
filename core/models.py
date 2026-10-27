"""Data models: what a habit looks like in Python."""


class Habit:

    # build a habit from one row of habits.json
    def __init__(self, d):
        self.id = d["id"]
        self.name = d["name"]
        self.target = d.get("target", "Daily")
        self.flower_symbol = d.get("flower_symbol", "sprout")
        self.short = d.get("short") or self.name.split()[0].lower()
        self.streak = d.get("streak", 0)
        self.best_streak = d.get("best_streak", 0)
        self.growth = d.get("growth", 0)
        self.bloom_threshold = d.get("bloom_threshold", 80)
        self.created_at = d.get("created_at", "")
        self.pos = d.get("pos") or {"left": 50, "top": 60}
        self.archived = d.get("archived", False)

    # figure out which flower picture to show from growth + streak
    def stage(self):
        if self.streak == 0 and self.growth < 80:
            return "wilt"
        if self.growth >= 70:
            return "bloom"
        if self.growth >= 40:
            return "grow"
        if self.growth >= 20:
            return "sprout"
        return "seed"

    # how many check-ins are left before the flower blooms
    def to_bloom(self):
        return max(0, self.bloom_threshold - self.growth)

    # turn the habit back into a dict so we can save it as json
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "target": self.target,
            "flower_symbol": self.flower_symbol,
            "short": self.short,
            "streak": self.streak,
            "best_streak": self.best_streak,
            "growth": self.growth,
            "bloom_threshold": self.bloom_threshold,
            "created_at": self.created_at,
            "pos": self.pos,
            "archived": self.archived,
        }
