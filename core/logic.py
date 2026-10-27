"""Business logic: streaks, growth and garden weather."""
from datetime import date, datetime, timedelta

GROW_UP = 10        # growth gained per check-in day
GROW_DOWN = 15      # growth lost when a streak breaks


# today's date as a string like "2026-10-08"
def today_str():
    return date.today().isoformat()


# turn a "2026-10-08" string into a real date we can do math with
def _day(d):
    return datetime.strptime(d, "%Y-%m-%d").date()


# count how many days in a row the habit was checked, up to today
def current_streak(habit_id, records):
    streak = 0
    cur = _day(today_str())
    # today not checked yet -> the day is not over, start from yesterday
    if not records.get(today_str(), {}).get(str(habit_id)):
        cur -= timedelta(days=1)
    while records.get(cur.isoformat(), {}).get(str(habit_id)):
        streak += 1
        cur -= timedelta(days=1)
    return streak


# recalc streak and growth for one habit from the check-in history
def recompute(habit, records):
    old = habit.streak
    habit.streak = current_streak(habit.id, records)
    habit.best_streak = max(habit.best_streak, habit.streak)
    habit.growth += (habit.streak - old) * GROW_UP
    if habit.streak == 0 and old > 0:       # streak broke
        habit.growth -= GROW_DOWN
    habit.growth = max(0, min(100, habit.growth))


# turn today's completion % into the garden weather
def weather_from(pct):
    if pct >= 90:
        return "sunny"
    if pct >= 70:
        return "cloudy"
    if pct >= 40:
        return "rainy"
    return "stormy"


# collect the numbers shown in the top stats bar
def garden_stats(habits, records):
    day = records.get(today_str(), {})
    done = 0
    bloom = 0
    longest = 0
    for h in habits:
        if day.get(str(h.id)):
            done += 1
        if h.stage() == "bloom":
            bloom += 1
        longest = max(longest, h.best_streak)
    pct = round(done / len(habits) * 100) if habits else 0
    return {"completion": pct, "done": done, "left": len(habits) - done,
            "bloom": bloom, "longest": longest,
            "weather": weather_from(pct)}
