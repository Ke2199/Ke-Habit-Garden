"""The tkinter interface: a garden page and a habit list page.

Garden page is one picture drawn by Pillow; hovering a flower pops up
a small card with that habit's details. List page is one card per habit
with a checkbox for today's check-in.
"""
import tkinter as tk
from datetime import date, timedelta

from PIL import ImageTk

from . import garden_art
from .repository import GardenRepository

STAGE_NAME = {"seed": "Seed", "sprout": "Sprout", "grow": "Growing",
              "bloom": "Bloom", "wilt": "Wilted"}
DOT_COLOR = {"seed": "#a3a3a3", "sprout": "#86efac", "grow": "#4ade80",
             "bloom": "#f472b6", "wilt": "#9ca3af"}
TAG_STYLE = {"seed": ("#475569", "#f1f5f9"), "sprout": ("#475569", "#f1f5f9"),
             "grow": ("#a16207", "#fef9c3"), "bloom": ("#15803d", "#dcfce7"),
             "wilt": ("#991b1b", "#fee2e2")}
BAR_COLOR = {"wilt": "#d65a5a", "sprout": "#e4a82f", "seed": "#a3a3a3"}
GREEN = "#3b7a57"


# the encouragement sentence at the bottom of the hover card
def tip_msg(habit, flower_label):
    stage = habit.stage()
    if stage == "bloom":
        return f"{flower_label} is in full bloom — keep it up!"
    if stage == "grow":
        return (f"{flower_label} is growing taller — "
                f"{habit.to_bloom()} more check-ins to bloom.")
    if stage == "sprout":
        return "A small sprout just peeked out — keep watering it."
    if stage == "wilt":
        return "I'm wilting — check in to revive me."
    return "A new seed is planted — first check-in sprouts it!"


class HabitGardenApp:

    # build the window: top bar, stats strip and the page container
    def __init__(self, repo: GardenRepository):
        self.repo = repo
        self.page = "garden"
        self._photo = None
        self._boxes = []        # flower positions, for the hover card
        self.tip = None         # the floating hover card

        self.root = tk.Tk()
        self.root.title("Habit Garden")
        self.root.geometry("1020x800")
        self.root.configure(bg="#f8fafc")

        # top bar: brand on the left, page buttons on the right
        top = tk.Frame(self.root, bg="white")
        top.pack(fill="x")
        tk.Label(top, text="🌱 Habit Garden", bg="white", fg="#1f2937",
                 font=("Helvetica", 15, "bold")).pack(side="left",
                                                      padx=16, pady=10)
        # labels used as buttons: macOS tk.Button always shows a border
        self.btn_list = tk.Label(top, text="📋 List", bg="white",
                                 fg="#1f2937", padx=12, pady=4)
        self.btn_list.pack(side="right", padx=(4, 16))
        self.btn_list.bind("<Button-1>", lambda e: self.show_list())
        self.btn_garden = tk.Label(top, text="🌳 Garden", bg="white",
                                   fg="#1f2937", padx=12, pady=4)
        self.btn_garden.pack(side="right")
        self.btn_garden.bind("<Button-1>", lambda e: self.show_garden())

        # stats strip under the top bar
        self.stats_var = tk.StringVar()
        tk.Label(self.root, textvariable=self.stats_var, bg="#f0fdf4",
                 fg="#374151", font=("Helvetica", 11),
                 pady=8).pack(fill="x")

        self.container = tk.Frame(self.root, bg="#f8fafc")
        self.container.pack(fill="both", expand=True)

        self.show_garden()

    # make the current page's button look pressed (light grey background)
    def _mark_page(self):
        on, off = "#f3f4f6", "white"
        self.btn_garden.config(bg=on if self.page == "garden" else off)
        self.btn_list.config(bg=on if self.page == "list" else off)

    # remove everything from the current page
    def _clear(self):
        for c in self.container.winfo_children():
            c.destroy()
        self.tip = None

    # ---------- garden page ----------

    # draw the garden picture and the legend bar under it
    def show_garden(self):
        self.page = "garden"
        self._mark_page()
        self._clear()
        s = self.repo.stats()
        self.stats_var.set(
            f"Today completion {s['completion']}%    "
            f"Garden weather {s['weather']}    "
            f"Bloom rate {s['bloom']}/{len(self.repo.habits())}    "
            f"Longest streak {s['longest']} days")

        emojis = {f["symbol"]: f["emoji"] for f in self.repo.flowers()}
        img, self._boxes = garden_art.render(self.repo.habits(),
                                             s["weather"], emojis)
        self._photo = ImageTk.PhotoImage(img)
        label = tk.Label(self.container, image=self._photo, bd=0)
        label.pack()
        label.bind("<Motion>", self._on_move)
        label.bind("<Leave>", lambda e: self._hide_tip())

        # floating hover card, hidden until the mouse is over a flower
        self._make_tip()

        # bottom bar: stage legend + checked summary
        bar = tk.Frame(self.container, bg="white")
        bar.pack(fill="x", padx=16, pady=8)
        legend = tk.Frame(bar, bg="white")
        legend.pack(side="left", padx=12, pady=8)
        for key, name in STAGE_NAME.items():
            tk.Label(legend, text="●", fg=DOT_COLOR[key],
                     bg="white").pack(side="left")
            tk.Label(legend, text=name + "  ", fg="#6b7280",
                     bg="white", font=("Helvetica", 10)).pack(side="left")
        tk.Label(bar, text=f"Checked {s['done']}    To check {s['left']}",
                 bg="white", fg="#374151",
                 font=("Helvetica", 11)).pack(side="right", padx=12)

    # build the floating detail card (hidden until a flower is hovered)
    def _make_tip(self):
        self.tip = tk.Frame(self.container, bg="white",
                            highlightbackground="#e5e7eb",
                            highlightthickness=1)
        title = tk.Frame(self.tip, bg="white")
        title.pack(fill="x", padx=12, pady=(10, 4))
        self.tip_emoji = tk.Label(title, bg="white", font=("Helvetica", 14))
        self.tip_emoji.pack(side="left")
        self.tip_name = tk.Label(title, bg="white",
                                 font=("Helvetica", 13, "bold"))
        self.tip_name.pack(side="left", padx=6)

        self.tip_streak = self._tip_row("Streak")
        self.tip_stage = self._tip_row("Growth stage")
        self.tip_bar = tk.Canvas(self.tip, height=8, width=216,
                                 bg="#e5e7eb", highlightthickness=0)
        self.tip_bar.pack(padx=12, pady=6)
        self.tip_tobloom = self._tip_row("Check-ins to bloom")
        self.tip_msg = tk.Label(self.tip, bg="#f0fdf4", fg=GREEN,
                                font=("Helvetica", 10), wraplength=200,
                                justify="left", padx=8, pady=6)
        self.tip_msg.pack(fill="x", padx=12, pady=(4, 12))

    # one "label ... value" line in the card, returns the value label
    def _tip_row(self, label):
        row = tk.Frame(self.tip, bg="white")
        row.pack(fill="x", padx=12, pady=2)
        tk.Label(row, text=label, bg="white", fg="#6b7280",
                 font=("Helvetica", 11)).pack(side="left")
        value = tk.Label(row, bg="white", fg="#1f2937",
                         font=("Helvetica", 11, "bold"))
        value.pack(side="right")
        return value

    # fill the card with one habit's details
    def _fill_tip(self, h):
        flower = self.repo.flower(h.flower_symbol)
        emoji = flower["emoji"] if flower else "🌸"
        label = flower["label"] if flower else "Flower"
        stage = h.stage()
        self.tip_emoji.config(text=emoji)
        self.tip_name.config(text=h.name)
        self.tip_streak.config(text=f"{h.streak} days")
        self.tip_stage.config(text=STAGE_NAME[stage])
        self.tip_bar.delete("all")
        self.tip_bar.create_rectangle(0, 0, 2.16 * h.growth, 8,
                                      fill=BAR_COLOR.get(stage, GREEN),
                                      width=0)
        self.tip_tobloom.config(
            text="Bloomed" if stage == "bloom" else f"{h.to_bloom()} times")
        self.tip_msg.config(text=tip_msg(h, label))

    # show the detail card when the mouse is over a flower
    def _on_move(self, event):
        for x1, y1, x2, y2, h in self._boxes:
            if x1 <= event.x <= x2 and y1 <= event.y <= y2:
                self._fill_tip(h)
                self.tip.place(x=min(event.x + 16, 740),
                               y=max(event.y - 20, 10))
                return
        self._hide_tip()

    # hide the hover card
    def _hide_tip(self):
        if self.tip is not None:
            self.tip.place_forget()

    # ---------- list page ----------

    # show one card per habit, three cards per row
    def show_list(self):
        self.page = "list"
        self._mark_page()
        self._clear()
        s = self.repo.stats()
        habits = self.repo.habits()
        self.stats_var.set(f"Today check-in      "
                           f"Checked {s['done']} / {len(habits)}")

        grid = tk.Frame(self.container, bg="#f8fafc")
        grid.pack(pady=12)
        for i, h in enumerate(habits):
            self._card(grid, h).grid(row=i // 3, column=i % 3,
                                     padx=10, pady=10, sticky="n")

        # button that opens the "new habit" form
        new_button = tk.Label(self.container, text="+ New Habit",
                              bg="white", fg=GREEN, padx=12, pady=6,
                              font=("Helvetica", 11, "bold"))
        new_button.pack(pady=8)
        new_button.bind("<Button-1>", lambda e: self._new_habit_dialog())

        tk.Label(self.container,
                 text="Tick a habit to see the garden weather update.",
                 bg="#f8fafc", fg="#6b7280",
                 font=("Helvetica", 10)).pack(pady=8)

    # build one habit card: icon, name, goal, checkbox, bar, tag
    def _card(self, parent, habit):
        card = tk.Frame(parent, bg="white", width=300, height=170,
                        highlightbackground="#e5e7eb",
                        highlightthickness=1, bd=0)
        card.pack_propagate(False)

        top = tk.Frame(card, bg="white")
        top.pack(fill="x", padx=14, pady=(14, 6))
        flower = self.repo.flower(habit.flower_symbol)
        tk.Label(top, text=flower["emoji"] if flower else "🌸",
                 bg="#f0fdf4", font=("Helvetica", 18),
                 padx=8, pady=6).pack(side="left")
        title = tk.Frame(top, bg="white")
        title.pack(side="left", padx=10)
        tk.Label(title, text=habit.name, bg="white", fg="#1f2937",
                 font=("Helvetica", 12, "bold")).pack(anchor="w")
        tk.Label(title, text=f"Goal: {habit.target}", bg="white",
                 fg="#6b7280", font=("Helvetica", 9)).pack(anchor="w")
        checked = tk.IntVar(value=int(self.repo.is_checked(habit.id)))
        tk.Checkbutton(top, variable=checked, bg="white",
                       activebackground="white",
                       command=lambda h=habit: self.toggle(h)
                       ).pack(side="right")

        tk.Label(card, bg="white", fg="#6b7280", font=("Helvetica", 9),
                 text=f"Streak {habit.streak} days     "
                      f"Growth {habit.growth}%     "
                      f"To bloom {habit.to_bloom()} times"
                 ).pack(padx=14, anchor="w")

        bar = tk.Canvas(card, height=8, width=272, bg="#e5e7eb",
                        highlightthickness=0)
        bar.pack(padx=14, pady=6, anchor="w")
        color = BAR_COLOR.get(habit.stage(), GREEN)
        bar.create_rectangle(0, 0, 2.72 * habit.growth, 8,
                             fill=color, width=0)

        fg, bg = TAG_STYLE[habit.stage()]
        tk.Label(card, text=STAGE_NAME[habit.stage()], fg=fg, bg=bg,
                 font=("Helvetica", 9, "bold"),
                 padx=8, pady=2).pack(padx=14, anchor="w")

        # small "History" link at the bottom-right of the card
        history = tk.Label(card, text="History", bg="white",
                           fg="#6b7280", font=("Helvetica", 9))
        history.pack(padx=14, pady=(0, 10), anchor="e")
        history.bind("<Button-1>",
                     lambda e, h=habit: self._history_dialog(h))
        return card

    # ---------- actions ----------

    # flip today's check-in for this habit and refresh the page
    def toggle(self, habit):
        if self.repo.is_checked(habit.id):
            self.repo.uncheck(habit.id)
        else:
            self.repo.check_in(habit.id)
        self.refresh()

    # ---------- dialogs ----------

    # open a small window to type in a new habit
    def _new_habit_dialog(self):
        win = tk.Toplevel(self.root)
        win.title("New Habit")
        win.geometry("460x520")
        win.configure(bg="white")

        form = tk.Frame(win, bg="white")
        form.pack(padx=24, pady=18, fill="both", expand=True)

        tk.Label(form, text="New Habit", bg="white", fg="#1f2937",
                 font=("Helvetica", 17, "bold")).pack(anchor="w")

        tk.Label(form, text="Habit name (e.g. Meditate 10 min)",
                 bg="white", fg="#6b7280",
                 font=("Helvetica", 11)).pack(anchor="w", pady=(14, 2))
        name_entry = tk.Entry(form, width=40, font=("Helvetica", 11))
        name_entry.pack(fill="x", ipady=4)

        tk.Label(form, text="Goal (e.g. 10 minutes / day)",
                 bg="white", fg="#6b7280",
                 font=("Helvetica", 11)).pack(anchor="w", pady=(12, 2))
        goal_entry = tk.Entry(form, width=40, font=("Helvetica", 11))
        goal_entry.pack(fill="x", ipady=4)

        tk.Label(form, text="Choose a flower", bg="white", fg="#6b7280",
                 font=("Helvetica", 11)).pack(anchor="w", pady=(14, 4))

        # flower tiles: click one to pick it, the picked one
        # gets a green border
        chosen = tk.StringVar()
        tiles = {}

        def choose(symbol):
            chosen.set(symbol)
            for s, t in tiles.items():
                if s == symbol:          # picked: thick green border
                    t.config(highlightbackground=GREEN,
                             highlightthickness=2)
                else:                    # not picked: thin grey border
                    t.config(highlightbackground="#e5e7eb",
                             highlightthickness=1)

        flower_grid = tk.Frame(form, bg="white")
        flower_grid.pack(anchor="w")
        row, col = 0, 0
        first_symbol = None
        for f in self.repo.flowers():
            if f["symbol"] == "wilted":
                continue        # nobody wants to plant a wilted flower
            if first_symbol is None:
                first_symbol = f["symbol"]
            tile = tk.Frame(flower_grid, bg="#f8fafc", padx=6, pady=5,
                            highlightbackground="#e5e7eb",
                            highlightthickness=1)
            tile.grid(row=row, column=col, padx=4, pady=4)
            tk.Label(tile, text=f["emoji"], bg="#f8fafc",
                     font=("Helvetica", 18)).pack()
            tk.Label(tile, text=f["label"], bg="#f8fafc", fg="#6b7280",
                     font=("Helvetica", 9)).pack()
            tile.bind("<Button-1>",
                      lambda e, s=f["symbol"]: choose(s))
            tiles[f["symbol"]] = tile
            col += 1
            if col == 5:        # five tiles per row, like the design
                row, col = row + 1, 0
        choose(first_symbol)     # the first flower is picked at the start

        buttons = tk.Frame(win, bg="white")
        buttons.pack(side="right", padx=24, pady=(0, 18))
        cancel = tk.Label(buttons, text="Cancel", bg="white", fg="#1f2937",
                          padx=16, pady=5, font=("Helvetica", 11),
                          highlightbackground="#e5e7eb",
                          highlightthickness=1)
        cancel.pack(side="left", padx=6)
        cancel.bind("<Button-1>", lambda e: win.destroy())
        save = tk.Label(buttons, text="Save", bg=GREEN, fg="white",
                        padx=16, pady=5, font=("Helvetica", 11, "bold"))
        save.pack(side="left")
        save.bind("<Button-1>",
                  lambda e: self._save_new_habit(win, name_entry,
                                                 goal_entry, chosen))

    # read the form, check it is filled, save and close the window
    def _save_new_habit(self, win, name_entry, goal_entry, chosen):
        name = name_entry.get().strip()
        if not name:            # nothing typed, so do not save
            return
        goal = goal_entry.get().strip()
        if not goal:
            goal = "Every day"
        self.repo.add_habit(name, goal, chosen.get())
        win.destroy()
        self.refresh()

    # open a window to edit the last 30 days of check-ins
    def _history_dialog(self, habit):
        win = tk.Toplevel(self.root)
        win.title(f"{habit.name} - Last 30 days")
        win.geometry("560x500")
        win.configure(bg="white")

        tk.Label(win, text="Last 30 days", bg="white", fg="#1f2937",
                 font=("Helvetica", 17, "bold")).pack(anchor="w", padx=24,
                                                      pady=(18, 0))
        tk.Label(win, text=f"Tick a day to change {habit.name}'s check-in:",
                 bg="white", fg="#6b7280",
                 font=("Helvetica", 11)).pack(anchor="w", padx=24,
                                              pady=(4, 8))

        grid = tk.Frame(win, bg="white")
        grid.pack(padx=20, pady=6)

        # weekday header row: one column per weekday, Monday first
        weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for col, name in enumerate(weekdays):
            tk.Label(grid, text=name, bg="white", fg="#9ca3af",
                     font=("Helvetica", 9, "bold"),
                     width=8).grid(row=0, column=col)

        # collect the last 30 days, oldest first
        today = date.today()
        days = []
        for i in range(29, -1, -1):
            days.append(today - timedelta(days=i))

        # put each day under its own weekday, pad the first week
        row, col = 1, days[0].weekday()
        for day in days:
            day_str = day.isoformat()      # e.g. "2026-10-31"
            var = tk.BooleanVar(
                value=self.repo.is_checked_on(habit.id, day_str))
            tk.Checkbutton(
                grid, text=day.strftime("%m-%d"), variable=var,
                bg="white", fg="#374151", activebackground="white",
                font=("Helvetica", 10), anchor="w", width=8,
                highlightthickness=0,
                command=lambda h=habit, d=day_str, v=var:
                    self._change_day(h, d, v.get())
            ).grid(row=row, column=col, sticky="w", padx=3, pady=2)
            col += 1
            if col == 7:                    # week is full, new row
                row, col = row + 1, 0

        # big green "Close" button, same style as "Save"
        buttons = tk.Frame(win, bg="white")
        buttons.pack(side="right", padx=24, pady=(0, 18))
        close = tk.Label(buttons, text="Close", bg=GREEN, fg="white",
                         padx=20, pady=6, font=("Helvetica", 12, "bold"))
        close.pack()
        close.bind("<Button-1>", lambda e: win.destroy())

    # save one day's check-in change and refresh the pages
    def _change_day(self, habit, day, done):
        self.repo.set_checked(habit.id, day, done)
        self.refresh()

    # redraw whichever page is showing
    def refresh(self):
        if self.page == "list":
            self.show_list()
        else:
            self.show_garden()

    # start the tkinter event loop
    def run(self):
        self.root.mainloop()
