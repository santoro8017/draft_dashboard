import pandas as pd
import streamlit as st
from openpyxl import load_workbook
import os

def reset_players():
    source_sheet = workbook["original_players"]
    destination_sheet = workbook["available_players"]

    for row_index, row in enumerate(source_sheet.iter_rows()):
        for col_index, cell in enumerate(row):
            destination_sheet.cell(row=row_index + 1, column=col_index + 1).value = cell.value


    workbook.save("draft_data.xlsx")

    return

def reset_teams():
    for team in get_teams():
        del workbook[team]
        workbook.create_sheet(team)
        
    workbook.save("draft_data.xlsx")

    return

def update_available_players_sheet(df):

    with pd.ExcelWriter("draft_data.xlsx", mode='a', engine='openpyxl', if_sheet_exists='replace') as writer:
        df.to_excel(writer, sheet_name="available_players", index=False)

    return

def get_available_players():
    # Read data
    df = pd.read_excel("draft_data.xlsx", sheet_name="available_players")

    return df

def get_team_players(team):
    df = pd.read_excel("draft_data.xlsx", sheet_name=team)

    if not "Grade" in df.columns:
        return pd.DataFrame(columns = ["Grade", "MW", "Player"])
    else:
        return df

def get_teams():
    teams = workbook.sheetnames
    return teams[2:]

def update_team(team, Grade, MW, player):
    sheet = workbook[team]
    
    if not sheet['A1'].value:
        for col_idx, value in enumerate(["Grade", "MW", "Player"], start=1):
             sheet.cell(row=1, column=col_idx, value=value)

    sheet.append([Grade, MW, player])
    workbook.save("draft_data.xlsx")

    return

######
FILE_TO_MONITOR = "draft_data.xlsx"
if 'last_mod_time' not in st.session_state:
    st.session_state.last_mod_time = os.path.getmtime(FILE_TO_MONITOR) if os.path.exists(FILE_TO_MONITOR) else None

current_mod_time = os.path.getmtime(FILE_TO_MONITOR) if os.path.exists(FILE_TO_MONITOR) else None

st.info(f"current_mod_time: {current_mod_time}")
st.info(f"last_mod_time: {st.session_state.last_mod_time}")
st.info(current_mod_time and st.session_state.last_mod_time)
st.info(current_mod_time and st.session_state.last_mod_time and current_mod_time)
if current_mod_time and st.session_state.last_mod_time and current_mod_time > st.session_state.last_mod_time:
    st.session_state.last_mod_time = current_mod_time
    st.rerun() # This will rerun the script
elif current_mod_time and not st.session_state.last_mod_time: # File created after app started
    st.session_state.last_mod_time = current_mod_time
    st.rerun()




st.button("Reset Available Players", on_click=reset_players)
st.button("Reset Teams", on_click=reset_teams)

# Create team lists and DataFrames based on the user input
workbook = load_workbook("draft_data.xlsx")

# Display available players table
st.dataframe(get_available_players())

# Player selection and assignment
player = st.selectbox('Select player:', get_available_players()["Player"].sort_values(ascending = True).values)
team = st.selectbox('Select team:', get_teams())

if st.button('Assign player'):
    available_players = get_available_players()
    Grade = available_players.query("Player == @player")["Grade"].values[0]
    MW = available_players.query("Player == @player")["MW"].values[0]
    player_info = pd.DataFrame(data={"Grade":Grade, "MW": MW, "Player": [player]})

    update_team(team, Grade, MW, player)

    # Remove assigned player from available players DataFrame
    available_players = available_players[available_players['Player'] != player]
    update_available_players_sheet(available_players)

    st.rerun()

# Display assigned players tables for each team
for team in get_teams():
    with st.expander(team + ' players'):
        st.dataframe(get_team_players(team))