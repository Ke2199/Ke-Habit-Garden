# Habit Garden

A habit-tracking app where every habit grows a flower — keep checking in and your garden blooms.

Mid-term (Week 5-6): the data layer (JSON storage + models + logic) is done,
and the garden comes alive — Pillow draws each flower at the right stage from the data.

## Run (macOS)

```bash
brew install python python-tk              # python + tkinter (for the UI)
which python3                              # must be $(brew --prefix)/bin/python3, NOT /usr/bin/python3
"$(brew --prefix)/bin/python3" -m venv .venv   # virtual environment from the brew python
.venv/bin/python -c "import tkinter"       # sanity check: no error means tk is there
.venv/bin/pip install -r requirements.txt  # pillow (draws the garden)
.venv/bin/python main.py                   # start the app
```

## Layout

```
habit_garden/
├── main.py              # entry point
├── requirements.txt     # pillow
└── core/                # data layer + UI
    ├── storage.py       # JSON read/write
    ├── models.py        # data models
    ├── logic.py         # streak / growth / weather math
    ├── repository.py    # the API the UI uses
    ├── garden_art.py    # draws the garden picture with Pillow
    ├── ui.py            # tkinter interface (garden + list pages)
    └── data/
        ├── habits.json      # habit list
        ├── checkins.json    # check-in history
        └── flowers.json     # flower catalog
```

## Build a Mac app (no Python needed to run)

```bash
.venv/bin/pip install pyinstaller
.venv/bin/pyinstaller --noconfirm --windowed --name "Habit Garden" \
  --add-data "core/data:core/data" main.py
```

The result is `dist/Habit Garden.app` — double-click to launch, or copy it to
another Mac. Check-ins are stored in `~/Library/Application Support/HabitGarden`
(seeded from `core/data/` on first launch).

Notes:
- The app is unsigned, so the first launch needs right-click → Open, or
  `xattr -dr com.apple.quarantine "dist/Habit Garden.app"`.
- A build only runs on the same chip family it was built on (Apple Silicon
  builds need an Apple Silicon Mac).

## Rules

- Each check-in: growth +10; broken streak: growth -15 (clamped 0~100)
- growth >= 70 bloom, >= 40 grow, >= 20 sprout, < 20 seed
- streak = 0 and not bloomed -> wilted
- today's completion >= 90% sunny, >= 70% cloudy, >= 40% rainy, else stormy
