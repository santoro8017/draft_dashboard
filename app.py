# --------------------------------------------------------------
# 1️⃣ Imports (including watchdog)
# --------------------------------------------------------------
import time
import threading
from pathlib import Path

import pandas as pd
import streamlit as st
from openpyxl import load_workbook
from watchdog.events import FileSystemEventHandler, EVENT_TYPE_MODIFIED
from watchdog.observers import Observer

# --------------------------------------------------------------
# 2️⃣ Constants & helpers
# --------------------------------------------------------------

EXCEL_PATH = Path("draft_data.xlsx")

# --------------------------------------------------------------
# 3️⃣ Watchdog event handler
# --------------------------------------------------------------

class DraftFileHandler(FileSystemEventHandler):
    """
    Fires when draft_data.xlsx is *modified*.
    A tiny debounce (default 0.5 s) prevents the handler from
    reacting to the many rapid events that some editors emit.
    """

    def __init__(self, debounce_seconds: float = 0.5):
        super().__init__()
        self._last_event = 0
        self.debounce = debounce_seconds

    def on_any_event(self, event):
        # We only care about modifications to the exact file
        if (
            event.is_directory
            or event.event_type != EVENT_TYPE_MODIFIED
            or Path(event.src_path) != EXCEL_PATH.resolve()
        ):
            return

        now = time.time()

        if now - self._last_event < self.debounce:
            # Skip duplicate events that happen within the debounce window
            return

        self._last_event = now

        # Tell Streamlit that the file changed
        st.session_state["draft_file_changed"] = True

        # Optional: write a tiny log line to the console (helps debugging)
        print(f"[watchdog] {EXCEL_PATH.name} modified – flag set")

# --------------------------------------------------------------
# 4️⃣ Start the observer (once per session)
# --------------------------------------------------------------
@st.cache_resource(show_spinner=False)
def start_observer() -> Observer:
    """
    Creates the observer, attaches the handler and starts the thread.
    The `@st.cache_resource` decorator guarantees that this runs only
    once per user session (even though Streamlit reruns the script on
    every interaction).
    """

    event_handler = DraftFileHandler()
    observer = Observer()
    observer.schedule(event_handler, str(EXCEL_PATH.parent), recursive=False)
    observer.start()

    return observer

# Kick‑off the observer as soon as the script is imported
observer = start_observer()

# --------------------------------------------------------------
# 5️⃣ Utility functions (unchanged – just moved after imports)
# --------------------------------------------------------------
def reset_players():
    source_sheet = workbook["original_players"]
    destination_sheet = workbook["available_players"]
    for row_index, row in enumerate(source_sheet.iter_rows()):
        for col_index, cell in enumerate(row):
            destination_sheet.cell(row=row_index + 1,
                                   column=col_index + 1).value = cell.value
    workbook.save(EXCEL_PATH)

    return

def reset_teams():
    for team in get_teams():
        del workbook[team]
        workbook.create_sheet(team)
    workbook.save(EXCEL_PATH)

    return

def update_available_players_sheet(df):
    with pd.ExcelWriter(EXCEL_PATH, mode='a', engine='openpyxl',
                        if_sheet_exists='replace') as writer:
        df.to_excel(writer, sheet_name="available_players", index=False)

    return

def get_available_players():
    return pd.read_excel(EXCEL_PATH, sheet_name="available_players")

def get_team_players(team):
    df = pd.read_excel(EXCEL_PATH, sheet_name=team)
    if "Grade" not in df.columns:
        return pd.DataFrame(columns=["Grade", "MW", "Player"])

    return df

def get_teams():
    # workbook is re‑loaded each time we call this, see note below
    return workbook.sheetnames[2:]

def update_team(team, Grade, MW, player):
    sheet = workbook[team]
    if not sheet['A1'].value:
        for col_idx, value in enumerate(["Grade", "MW", "Player"], start=1):
            sheet.cell(row=1, column=col_idx, value=value)

    sheet.append([Grade, MW, player])
    workbook.save(EXCEL_PATH)

    return

# --------------------------------------------------------------
# 6️⃣ React to a file‑change flag (reload workbook & UI)
# --------------------------------------------------------------
if "draft_file_changed" not in st.session_state:
    # First run – initialise the flag
    st.session_state["draft_file_changed"] = False

if st.session_state["draft_file_changed"]:
    # The file was edited somewhere else – reload everything
    st.session_state["draft_file_changed"] = False   # reset flag

    # Re‑load the workbook *after* the external edit
    workbook = load_workbook(EXCEL_PATH)

    # Force a full UI refresh (keeps the UI in sync)
    st.experimental_rerun()

# --------------------------------------------------------------
# 7️⃣ Load the workbook for the *current* run
# --------------------------------------------------------------

# (If the file was just changed, the `st.experimental_rerun()` above

# will reload the script and execute this line again with a fresh copy.)

workbook = load_workbook(EXCEL_PATH)

# --------------------------------------------------------------
# 8️⃣ Streamlit UI (unchanged – just moved after the watchdog logic)
# --------------------------------------------------------------

st.title("🏈 Draft Manager")

# Reset buttons

col1, col2 = st.columns(2)
col1.button("Reset Available Players", on_click=reset_players)
col2.button("Reset Teams", on_click=reset_teams)

# Show the master table of available players
st.subheader("📊 Available Players")
st.dataframe(get_available_players())

# Player selection & assignment
player = st.selectbox(
    'Select player:',
    get_available_players()["Player"].sort_values().values,
    key="player_select"

)

team = st.selectbox(
    'Select team:',
    get_teams(),
    key="team_select"
)

if st.button('Assign player'):
    available_players = get_available_players()

    # Grab the row for the chosen player
    row = available_players.query("Player == @player").iloc[0]
    Grade, MW = row["Grade"], row["MW"]

    # Write to the team sheet
    update_team(team, Grade, MW, player)

    # Remove from the master list & write back
    available_players = available_players[available_players['Player'] != player]
    update_available_players_sheet(available_players)

    # Immediately refresh the UI so the new state is visible
    st.rerun()

# Show each team's roster
st.subheader("🗂️ Team Rosters")

for tm in get_teams():
    with st.expander(f"{tm} players"):
        st.dataframe(get_team_players(tm))

# --------------------------------------------------------------
# 9️⃣ Clean‑up (optional – for local dev)
# --------------------------------------------------------------

# When the app shuts down (e.g. on Ctrl‑C) you may want to stop the observer.
# Streamlit doesn't expose a dedicated shutdown hook, but you can rely on
# Python's atexit module if you run the script locally.

import atexit

atexit.register(lambda: observer.stop() or observer.join())