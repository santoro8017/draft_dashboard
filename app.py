import pandas as pd
import streamlit as st

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from gspread_dataframe import set_with_dataframe

def reset_players():
    source_worksheet = spreadsheet.worksheet("original_players")
    destination_worksheet = spreadsheet.worksheet("available_players")

    # Read all data from the source worksheet
    data_to_copy = source_worksheet.get_all_values()

    # Write the data to the destination worksheet, starting from cell A1
    destination_worksheet.update('A1', data_to_copy)

    return

def reset_teams():
    for team in get_teams(all_worksheets):
        worksheet = spreadsheet.worksheet(team)
        worksheet.clear()
        empty_data = worksheet.get_all_values()
        worksheet.update('A1', empty_data)

    return

def update_available_players_sheet(df):
    destination_worksheet = spreadsheet.worksheet("available_players")
    set_with_dataframe(destination_worksheet, df, include_column_header=True)

    return

def get_available_players():
    worksheet = spreadsheet.worksheet("available_players") # Or by index: worksheet = spreadsheet.get_worksheet(0)

    # Read data
    df = pd.DataFrame(worksheet.get_all_records())

    return df

def get_team_players(team):
    worksheet = spreadsheet.worksheet(team)
    df = pd.DataFrame(worksheet.get_all_records())

    if not "Grade" in df.columns:
        return pd.DataFrame(columns = ["Grade", "MW", "Player"])
    else:
        return df

def get_teams(all_worksheets):
    teams = [ws.title for ws in all_worksheets]
    return teams[2:]

def update_team(team, df):
    worksheet = spreadsheet.worksheet(team)
    set_with_dataframe(worksheet, df, include_column_header=True)

    return
######
# def update_teams(all_worksheets):
    
#     for team in teams[2:]:
#         if team not in st.session_state:
#             st.session_state[team] = pd.DataFrame(columns=['Grade', 'MW', 'Player'])
    
#     return 

# Use service account credentials
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('.streamlit\draft-476301-7b548ab053cb.json', scope)

client = gspread.authorize(creds)

# Open the spreadsheet by name or ID
spreadsheet = client.open("draft_data")
st.button("Reset Available Players", on_click=reset_players)
st.button("Reset Teams", on_click=reset_teams)

# Initialize session state
# if 'available_players' not in st.session_state:
#     # Select a worksheet
#     reset_players()
#     df = get_available_players()

#     df["Player"] = df["Last Name"]+", "+df["First Name"]
#     df.drop(columns=["Last Name", "First Name"], inplace=True)

#     st.session_state.available_players = df

# Create team lists and DataFrames based on the user input
all_worksheets = spreadsheet.worksheets()

# Display available players table
st.dataframe(get_available_players())

# Player selection and assignment
player = st.selectbox('Select player:', get_available_players()["Player"].sort_values(ascending = True).values)
team = st.selectbox('Select team:', get_teams(all_worksheets))

if st.button('Assign player'):
    available_players = get_available_players()
    Grade = available_players.query("Player == @player")["Grade"].values
    MW = available_players.query("Player == @player")["MW"].values
    player_info = pd.DataFrame(data={"Grade":Grade, "MW": MW, "Player": [player]})

    updated_team_players = pd.concat([get_team_players(team), player_info])
    update_team(team, updated_team_players)

    # Remove assigned player from available players DataFrame
    available_players = available_players[available_players['Player'] != player]
    update_available_players_sheet(available_players)

    st.rerun()

# Display assigned players tables for each team
for team in get_teams(all_worksheets):
    with st.expander(team + ' Players'):
        st.dataframe(get_team_players(team))