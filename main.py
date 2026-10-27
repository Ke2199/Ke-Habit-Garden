"""Habit Garden entry point.

Run:  python main.py
"""
from core.repository import GardenRepository
from core.ui import HabitGardenApp


# entry point: load the data and open the window
def main() -> None:
    repo = GardenRepository()
    HabitGardenApp(repo).run()


if __name__ == "__main__":
    main()
