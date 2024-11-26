import pandas as pd
import numpy as np
from itertools import combinations
from random import sample
import gdown

url = 'insert url here'
output = 'Fotbal.xlsx'
gdown.download(url, output, quiet=False)
print()

# Load data into a DataFrame
data = pd.read_excel('Fotbal.xlsx', sheet_name='Jucatori')

# Calculating Overall based on stats
ponderi = pd.read_excel('Fotbal.xlsx', sheet_name='Ponderi', index_col=0)

def calcul_overall(jucator, ponderi):
    suma_ponderi = ponderi.loc[jucator['Pozitie']].sum()
    bonus_inform = jucator['INFORM'] if jucator['INFORM'] != 0 else 0

    overall = round(
        ((jucator['PAC'] * ponderi.loc[jucator['Pozitie'], 'PAC'] +
          jucator['SHO'] * ponderi.loc[jucator['Pozitie'], 'SHO'] +
          jucator['PAS'] * ponderi.loc[jucator['Pozitie'], 'PAS'] +
          jucator['DRI'] * ponderi.loc[jucator['Pozitie'], 'DRI'] +
          jucator['DEF'] * ponderi.loc[jucator['Pozitie'], 'DEF'] +
          jucator['PHY'] * ponderi.loc[jucator['Pozitie'], 'PHY']) / suma_ponderi) + bonus_inform,
        0)
    return overall

data['Overall'] = data.apply(calcul_overall, axis=1, ponderi=ponderi)

# Selecting players with 'Prezenta' marked as 1
available_players = data[data['Prezenta'] == 1]

# Sorting by 'Overall' to balance teams
sorted_players = available_players.sort_values(by='Overall', ascending=False)

def check_balance(teams):
    averages = [np.mean([player['Overall'] for player in team]) for team in teams]
    return max(averages) - min(averages) <= 0.25

def generate_balanced_teams(sorted_players, n_teams=3, team_size=5, max_attempts=100000):
    all_players = sorted_players.to_dict('records')
    best_combination = None
    min_difference = float('inf')

    for _ in range(max_attempts):
        players_list = sample(all_players, n_teams * team_size)
        teams = [players_list[i:i + team_size] for i in range(0, len(players_list), team_size)]
        if check_balance(teams):
            averages = [np.mean([player['Overall'] for player in team]) for team in teams]
            difference = max(averages) - min(averages)
            if difference < min_difference:
                min_difference = difference
                best_combination = teams
            break

    return best_combination

def teams_are_too_similar(teams_v1, teams_v2, max_same_players):
    # Convert team lists to sets for comparison
    for team_v1 in teams_v1:
        for team_v2 in teams_v2:
            common_players = set([player['Nume'] for player in team_v1]) & set([player['Nume'] for player in team_v2])
            if len(common_players) > max_same_players:
                return True
    return False

# Generate two sets of teams with an additional check for similarity
teams_v1 = generate_balanced_teams(sorted_players)

# Regenerate the second set if teams are too similar to the first set, with a max attempt limit
max_attempts = 200  # Set the maximum number of attempts before relaxing the restriction
attempt_count = 0
max_same_players = 2  # Initial restriction: no more than 2 same players per team

teams_v2 = generate_balanced_teams(sorted_players)
while teams_are_too_similar(teams_v1, teams_v2, max_same_players):
    attempt_count += 1
    if attempt_count >= max_attempts and max_same_players == 2:
        print(f"Relaxing restriction from {max_same_players} to 3 same players after {attempt_count} attempts.")
        max_same_players = 3  # Relax the restriction to 3 same players
        attempt_count = 0
    elif attempt_count >= max_attempts:
        print(f"Could not generate distinct teams after {attempt_count} attempts with 2 same players restriction.")
        break
    teams_v2 = generate_balanced_teams(sorted_players)

def create_team_list(teams):
    team_list = []
    screenshot_list = []
    if teams:
        for i, team in enumerate(teams, 1):
            team_overall = np.mean([player['Overall'] for player in team])
            team_list.append(["Team {}".format(i), "Overall", "{:.2f}".format(team_overall)])
            for player in team:
                team_list.append([' ', player['Nume'], player['Overall']])
            team_list.append([' ', ' ', ' '])

        for i, team in enumerate(teams, 1):
            screenshot_list.append(["Team {}".format(i), " "])
            for player in team:
                screenshot_list.append([' ', player['Nume']])
            screenshot_list.append([' ', ' '])
    else:
        print("No balanced teams could be found.")

    return pd.DataFrame(team_list, columns=['Team', 'Name', 'Overall']), pd.DataFrame(screenshot_list, columns=['Team', 'Name'])

# Create two variants for both with and without overalls
teams_v1_df, screenshot_v1_df = create_team_list(teams_v1)
teams_v2_df, screenshot_v2_df = create_team_list(teams_v2)

# Create empty column with the correct number of rows for spacing
empty_col = pd.DataFrame([''] * len(teams_v1_df), columns=[' '])

# Combine the two sets of teams side by side for "with overalls" and "without overalls", adding space between them
combined_with_overall = pd.concat([teams_v1_df, empty_col, teams_v2_df], axis=1)
combined_without_overall = pd.concat([screenshot_v1_df, empty_col, screenshot_v2_df], axis=1)

# Print the side-by-side result
print("Teams with Overalls (Variant 1 vs Variant 2): \n")
print(combined_with_overall)

print("\nTeams without Overalls (Variant 1 vs Variant 2): \n")
print(combined_without_overall)
