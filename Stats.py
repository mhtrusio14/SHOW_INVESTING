import requests
import json
import gspread
import time
import datetime
import pytz
import os

start_time = time.time()

# Google Sheets API setup
creds_json = os.environ['CREDS']
CREDS = json.loads(creds_json)

client = gspread.service_account_from_dict(CREDS)

# Open the spreadsheet
spreadsheet = client.open("MLB Investing")

# Get the Players sheet
players_sheet = spreadsheet.worksheet("Players")

# Get the ESPN Stats sheet
stats_sheet = spreadsheet.worksheet("ESPN Stats")

# Prepare the base URL for API calls
base_url = "https://site.web.api.espn.com/apis/common/v3/sports/baseball/mlb/athletes"

# Define the display names and initialize the list for all player stats
displayNames = [
    "Earned Run Average",
    "Wins",
    "Losses",
    "Saves",
    "Save Opportunities",
    "Games Played",
    "Games Started",
    "Complete Games",
    "Innings pitched",
    "Hits",
    "Runs",
    "Earned runs",
    "Home Runs",
    "Walks",
    "Strikeouts",
    "Opponent Batting Average",
    "OBP",
    "BAA RISP"
]

# Batch read player names and ESPN IDs
player_data = players_sheet.get_all_records()

# Initialize a list for all player stats
all_player_stats = []

# Loop through each player's data
for player in player_data:
    player_name = player['NAME']
    espn_id = player['ESPN_ID']

    url = f"{base_url}/{espn_id}/splits?region=us&lang=en&contentorigin=espn&season=2024&category=pitching"
    api_call = requests.get(url)
    if api_call.status_code == 200:
        api_json = api_call.json()
        try:
            stats = api_json['splitCategories'][0]['splits'][0]['stats']
            obp = api_json['splitCategories'][1]['splits'][0]['stats'][13]
            baa_risp = api_json['splitCategories'][10]['splits'][2]['stats'][12]
            
            # Create a list with the player's name, ESPN ID, and stats
            player_stats = [player_name, espn_id]
            
            stats.append(obp)
            stats.append(baa_risp)   
            # Match the displayNames with the stats in order
            player_stats.extend(stats)
                
            # Append the list to all_player_stats
            all_player_stats.append(player_stats)
            
        except (IndexError, KeyError, TypeError) as e:
            print(f"Error processing stats for {player_name}: {e}")
            continue
    else:
        print(f"Failed to fetch data for {player_name}: HTTP {api_call.status_code}")

# Prepare the headers and the data for batch updating
headers = ['Name', 'ESPN_ID'] + displayNames
all_data = [headers] + all_player_stats

# Batch update the ESPN Stats sheet starting from column B
cell_range = f"B1:{chr(65 + len(headers))}{len(all_data)}"
cell_list = stats_sheet.range(cell_range)

# Flatten the all_data list and fill the cell_list with the data
flat_data = [item for sublist in all_data for item in sublist]
for cell, value in zip(cell_list, flat_data):
    cell.value = value

# Update the cells in a batch
stats_sheet.update_cells(cell_list)

now = datetime.datetime.now()
est = pytz.timezone('US/Eastern')
now_est = now.astimezone(est)

short_date = now_est.strftime("%m/%d/%y")
current_time = now_est.strftime("%I:%M %p")

stats_sheet.update_acell('A1', "Updated: " + short_date + " " + current_time + " EST")

print("--- %s seconds ---" % (time.time() - start_time)) 
