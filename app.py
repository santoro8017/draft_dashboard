import pandas as pd
import streamlit as st


# Initialize session state
if 'available_players' not in st.session_state:
    df = pd.read_excel(r"Wellesley BBall Players.xlsx")
    df["Player"] = df["Last Name"]+", "+df["First Name"]
    df.drop(columns=["Last Name", "First Name"], inplace=True)
    st.session_state.available_players = df

# Create team lists and DataFrames based on the user input
num_teams = 8
teams = [f'Team{i+1}' for i in range(num_teams)]
for team in teams:
    if team not in st.session_state:
        st.session_state[team] = pd.DataFrame(columns=['Grade', 'MW', 'Player'])

# Display available players table
st.dataframe(st.session_state.available_players)

# Player selection and assignment
player = st.selectbox('Select player:', st.session_state.available_players['Player'].sort_values(ascending = True).values)
team = st.selectbox('Select team:', teams)

if st.button('Assign player'):
    Grade = st.session_state.available_players.query("Player == @player")["Grade"].values
    MW = st.session_state.available_players.query("Player == @player")["MW"].values
    add_player = pd.DataFrame(data={"Grade":Grade, "MW": MW, "Player": [player]})
    st.session_state[team] = pd.concat([st.session_state[team], add_player])

    # Remove assigned player from available players DataFrame
    st.session_state.available_players = st.session_state.available_players[st.session_state.available_players['Player'] != player]

    st.rerun()

# Display assigned players tables for each team
for team in teams:
    with st.expander(team + ' Players'):
        st.dataframe(st.session_state[team])