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
        return bool(self._records.get(logic.today_str(), {})
                    .get(str(habit_id)))

    # numbers for the top stats bar
    def stats(self):
        return logic.garden_stats(self.habits(), self._records)

    # ---- write ----

    # mark one habit as done today, then save
    def check_in(self, habit_id):
        day = self._records.setdefault(logic.today_str(), {})
        day[str(habit_id)] = True
        logic.recompute(self._habits[habit_id], self._records)
        self._save_checkins()
        self._save_habits()

    # cancel today's check-in for one habit, then save
    def uncheck(self, habit_id):
        day = self._records.get(logic.today_str(), {})
        day.pop(str(habit_id), None)
        logic.recompute(self._habits[habit_id], self._records)
        self._save_checkins()
        self._save_habits()
