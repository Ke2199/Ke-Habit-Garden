"""Repository: the middle layer between the UI and the data files.

The UI never touches JSON directly, it only calls the methods below.
"""
from . import storage
from . import logic
from .models import Habit


class GardenRepository:

    # set up empty caches and load everything from disk
    def __init__(self):
        self._habits = {}       # id -> Habit
        self._records = {}      # date -> {habit_id: True}
        self._flowers = {}      # symbol -> flower dict
        self.reload()

    # load the three json files and refresh every habit
    def reload(self):
        data = storage.load("habits.json", {"habits": []})
        for d in data["habits"]:
            self._habits[d["id"]] = Habit(d)
        self._records = storage.load("checkins.json",
                                     {"records": {}})["records"]
        for f in storage.load("flowers.json", {"flowers": []})["flowers"]:
            self._flowers[f["symbol"]] = f
        for h in self._habits.values():
            logic.recompute(h, self._records)
        self._save_habits()

    # save the habit list back to habits.json
    def _save_habits(self):
        storage.save("habits.json",
                     {"habits": [h.to_dict() for h in self.habits()]})

    # save the check-in records back to checkins.json
    def _save_checkins(self):
        storage.save("checkins.json", {"records": self._records})

    # ---- read ----

    # all active habits, ordered by id
    def habits(self):
        return sorted((h for h in self._habits.values() if not h.archived),
                      key=lambda h: h.id)

    # the whole flower catalog as a list of dicts
    def flowers(self):
        return list(self._flowers.values())

    # look up one flower by its symbol, e.g. "rose"
    def flower(self, symbol):
        return self._flowers.get(symbol)

    # is this habit already checked today?
    def is_checked(self, habit_id):
        return self.is_checked_on(habit_id, logic.today_str())

    # numbers for the top stats bar
    def stats(self):
        return logic.garden_stats(self.habits(), self._records)

    # ---- write ----

    # mark one habit as done today, then save
    def check_in(self, habit_id):
        self.set_checked(habit_id, logic.today_str(), True)

    # cancel today's check-in for one habit, then save
    def uncheck(self, habit_id):
        self.set_checked(habit_id, logic.today_str(), False)

    # add a new habit and save it to habits.json
    def add_habit(self, name, target, flower_symbol):
        # pick the next free id number
        if self._habits:
            new_id = max(self._habits) + 1
        else:
            new_id = 1
        # ready-made spots in the garden, so flowers do not overlap
        slots = [(50, 62), (20, 40), (70, 42), (58, 74),
                 (36, 58), (84, 52), (26, 44), (50, 62)]
        left, top = slots[len(self._habits) % len(slots)]
        habit = Habit({
            "id": new_id,
            "name": name,
            "target": target,
            "flower_symbol": flower_symbol,
            "created_at": logic.today_str(),
            "pos": {"left": left, "top": top},
        })
        self._habits[new_id] = habit
        self._save_habits()
        return habit

    # check whether a habit was done on one day, day like "2026-10-31"
    def is_checked_on(self, habit_id, day):
        return bool(self._records.get(day, {}).get(str(habit_id)))

    # change one day's check-in and recalculate the habit
    def set_checked(self, habit_id, day, done):
        if done:
            self._records.setdefault(day, {})[str(habit_id)] = True
        else:
            self._records.get(day, {}).pop(str(habit_id), None)
        logic.recompute(self._habits[habit_id], self._records)
        self._save_checkins()
        self._save_habits()
