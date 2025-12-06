"""
Puckmon: NHL Game Schedule Viewer
Displays NHL game schedules with ASCII art logos and scores.
"""

import os
import subprocess
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import yaml

try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo


# ==============================
# Constants and Paths
# ==============================
BASE_DIR = os.path.dirname(__file__)
ASSETS_FOLDER = os.path.join(BASE_DIR, "assets")
LOGOS_FOLDER = os.path.join(ASSETS_FOLDER, "logos")
SYMBOLS_FOLDER = os.path.join(ASSETS_FOLDER, "symbols")
NUMERALS_FOLDER = os.path.join(ASSETS_FOLDER, "numerals")
CONFIG_FILE = os.path.join(os.path.dirname(BASE_DIR), "config", "config.yml")

# NHL API endpoints
NHL_STANDINGS_URL = "https://api-web.nhle.com/v1/standings/now"
NHL_SCHEDULE_URL = "https://api-web.nhle.com/v1/schedule/{date}"

# Display settings
LOGO_SPACER_WIDTH = 4
VS_SYMBOL_WIDTH = 20


# ==============================
# Configuration Management
# ==============================
class Config:
    """Manages application configuration from YAML file."""
    
    def __init__(self, config_path: str = CONFIG_FILE):
        """Initialize configuration from file or use defaults."""
        self.config_path = config_path
        self.data = self._load_config()
        self.timezone = self.data.get("timezone", "US/Eastern")
    
    def _load_config(self) -> Dict:
        """Load configuration from YAML file."""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    return yaml.safe_load(f) or {}
            except (yaml.YAMLError, IOError) as e:
                print(f"Warning: Could not load config file: {e}")
        return {}


# ==============================
# API Client
# ==============================
class NHLApiClient:
    """Handles communication with NHL API endpoints."""
    
    @staticmethod
    def fetch_json(url: str) -> Dict:
        """
        Fetch JSON data from a URL using curl.
        
        Args:
            url: The URL to fetch data from
            
        Returns:
            Parsed JSON data as a dictionary
        """
        cmd = f'curl -s -L -X GET "{url}"'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON from {url}: {e}")
            return {}
    
    def get_schedule(self, date: str) -> Dict:
        """
        Fetch NHL schedule for a specific date.
        
        Args:
            date: ISO format date string (YYYY-MM-DD)
            
        Returns:
            Schedule data dictionary
        """
        url = NHL_SCHEDULE_URL.format(date=date)
        return self.fetch_json(url)
    
    def get_standings(self) -> Dict[str, str]:
        """
        Fetch current NHL standings.
        
        Returns:
            Dictionary mapping team names to their records
            Format: {"TeamName": "W-L-OT (pts pts)"}
        """
        data = self.fetch_json(NHL_STANDINGS_URL)
        standings = {}
        
        for team in data.get("standings", []):
            name = team["teamCommonName"]["default"]
            wins = team.get("wins", 0)
            losses = team.get("losses", 0)
            ot = team.get("otLosses", 0)
            points = team.get("points", 0)
            standings[name] = f"{wins}-{losses}-{ot} ({points} pts)"
        
        return standings
    
    def get_live_game(self, game_id: int) -> Optional[Dict]:
        """
        Fetch live game data with current scores and game state.
        
        Args:
            game_id: NHL game ID
            
        Returns:
            Live game data dictionary or None if not available
        """
        url = f"https://api-web.nhle.com/v1/gamecenter/{game_id}/play-by-play"
        try:
            return self.fetch_json(url)
        except Exception:
            return None


# ==============================
# ASCII Art Management
# ==============================
class AssetManager:
    """Manages loading and manipulation of ASCII art assets."""
    
    def __init__(self):
        """Initialize asset manager with folder paths."""
        self.logos_folder = LOGOS_FOLDER
        self.symbols_folder = SYMBOLS_FOLDER
        self.numerals_folder = NUMERALS_FOLDER
    
    def load_asset(self, category: str, name: str) -> List[str]:
        """
        Load ASCII art from a text file.
        
        Args:
            category: Asset category ('logos' or 'symbols')
            name: Name of the asset file (without .txt extension)
            
        Returns:
            List of lines containing the ASCII art
        """
        folder_map = {
            "logos": self.logos_folder,
            "symbols": self.symbols_folder
        }
        
        folder = folder_map.get(category)
        if not folder:
            return [f"[Unknown category: {category}]"]
        
        file_path = os.path.join(folder, f"{name}.txt")
        
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    return f.read().splitlines()
            except IOError as e:
                print(f"Error reading asset {name}: {e}")
        
        return [f"[{category} asset not found: {name}]"]
    
    def load_number_ascii(self, number: int) -> List[str]:
        """
        Generate ASCII art representation of a number.
        
        Args:
            number: The number to convert to ASCII art
            
        Returns:
            List of lines containing the ASCII art number
        """
        digits = str(number)
        digit_lines_list = []
        
        # Load ASCII art for each digit
        for digit_char in digits:
            digit_file = os.path.join(self.numerals_folder, f"{digit_char}.txt")
            
            if os.path.exists(digit_file):
                try:
                    with open(digit_file, "r", encoding="utf-8") as f:
                        digit_lines_list.append(f.read().splitlines())
                except IOError:
                    digit_lines_list.append([digit_char])  # Fallback
            else:
                digit_lines_list.append([digit_char])  # Fallback
        
        # Combine digits horizontally
        return self._combine_digits_horizontal(digit_lines_list)
    
    @staticmethod
    def _combine_digits_horizontal(digit_lines_list: List[List[str]]) -> List[str]:
        """
        Combine multiple digit ASCII arts horizontally.
        
        Args:
            digit_lines_list: List of digit line lists
            
        Returns:
            Combined ASCII art lines
        """
        if not digit_lines_list:
            return [""]
        
        max_height = max(len(lines) for lines in digit_lines_list)
        padded_digits = [
            AsciiFormatter.pad_lines(lines, max_height) 
            for lines in digit_lines_list
        ]
        
        combined_lines = []
        for i in range(max_height):
            combined_lines.append(" ".join(digit[i] for digit in padded_digits))
        
        return combined_lines


# ==============================
# ASCII Formatting Utilities
# ==============================
class AsciiFormatter:
    """Utilities for formatting and combining ASCII art."""
    
    @staticmethod
    def pad_lines(lines: List[str], target_height: int, top_padding: int = 0) -> List[str]:
        """
        Pad lines to match a target height for vertical alignment.
        
        Args:
            lines: List of text lines to pad
            target_height: Desired total height
            top_padding: Number of blank lines to add at top
            
        Returns:
            Padded list of lines
        """
        bottom_padding = target_height - len(lines) - top_padding
        return [""] * top_padding + lines + [""] * bottom_padding
    
    @staticmethod
    def get_width(lines: List[str]) -> int:
        """Get the maximum width of a list of lines."""
        return max(len(line) for line in lines) if lines else 0
    
    @staticmethod
    def combine_logos_with_vs(
        logo1: List[str], 
        vs_logo: List[str], 
        logo2: List[str], 
        spacer: int = LOGO_SPACER_WIDTH
    ) -> Tuple[List[str], int, int]:
        """
        Combine two team logos with a 'vs' symbol in the middle.
        
        Args:
            logo1: Away team logo lines
            vs_logo: VS symbol lines
            logo2: Home team logo lines
            spacer: Number of spaces between elements
            
        Returns:
            Tuple of (combined lines, width1, width2)
        """
        # Calculate heights and align vertically
        max_height = max(len(logo1), len(logo2), len(vs_logo))
        vs_top_padding = (max_height - len(vs_logo)) // 2
        
        logo1 = AsciiFormatter.pad_lines(logo1, max_height)
        logo2 = AsciiFormatter.pad_lines(logo2, max_height)
        vs_logo = AsciiFormatter.pad_lines(vs_logo, max_height, top_padding=vs_top_padding)
        
        # Calculate widths
        width1 = AsciiFormatter.get_width(logo1)
        width2 = AsciiFormatter.get_width(logo2)
        vs_width = AsciiFormatter.get_width(vs_logo)
        
        # Combine horizontally
        combined = [
            l1.ljust(width1) + " " * spacer + 
            lv.ljust(vs_width) + " " * spacer + 
            l2.ljust(width2)
            for l1, lv, l2 in zip(logo1, vs_logo, logo2)
        ]
        
        return combined, width1, width2
    
    @staticmethod
    def print_boxed(lines: List[str]) -> None:
        """
        Print lines of text inside a box of '#' characters.
        
        Args:
            lines: List of text lines to display in box
        """
        width = max(len(line) for line in lines) + 4
        print("#" * width)
        for line in lines:
            print("# " + line.ljust(width - 4) + " #")
        print("#" * width)


# ==============================
# Date Selection
# ==============================
class DateSelector:
    """Handles user input for date selection."""
    
    def __init__(self, timezone: str):
        """Initialize with user's timezone."""
        self.timezone = timezone
    
    def get_schedule_date(self) -> str:
        """
        Prompt user to select a date for the schedule.
        
        Returns:
            ISO format date string (YYYY-MM-DD)
        """
        print("\nWhen do you want to pull schedule info for?")
        print("1. Yesterday")
        print("2. Today")
        print("3. Tomorrow")
        print("4. Live games (refreshing)")
        print("5. Specify date (MM-DD-YYYY)")
        
        choice = input("Enter choice [1-5]: ").strip()
        now_tz = datetime.now(tz=ZoneInfo(self.timezone)).date()
        
        if choice == "1":
            return (now_tz - timedelta(days=1)).isoformat()
        elif choice == "2":
            return now_tz.isoformat()
        elif choice == "3":
            return (now_tz + timedelta(days=1)).isoformat()
        elif choice == "4":
            return "LIVE"  # Special marker for live mode
        elif choice == "5":
            return self._parse_custom_date(now_tz)
        else:
            print("Invalid choice. Defaulting to today.")
            return now_tz.isoformat()
    
    def _parse_custom_date(self, fallback_date) -> str:
        """
        Parse custom date input from user.
        
        Args:
            fallback_date: Date to use if parsing fails
            
        Returns:
            ISO format date string
        """
        user_date = input("Enter date (MM-DD-YYYY): ").strip()
        try:
            dt = datetime.strptime(user_date, "%m-%d-%Y")
            return dt.date().isoformat()
        except ValueError:
            print("Invalid date format. Defaulting to today.")
            return fallback_date.isoformat()


# ==============================
# Game Display
# ==============================
class GameDisplay:
    """Handles display of individual NHL games."""
    
    def __init__(self, asset_manager: AssetManager, timezone: str):
        """
        Initialize game display.
        
        Args:
            asset_manager: AssetManager instance for loading logos
            timezone: User's timezone for time conversion
        """
        self.assets = asset_manager
        self.timezone = timezone
    
    def display_game(
        self, 
        game: Dict, 
        vs_logo: List[str], 
        standings: Dict[str, str],
        live_data: Optional[Dict] = None
    ) -> None:
        """
        Display a single NHL game with ASCII logos and information.
        
        Args:
            game: Game data dictionary from NHL API
            vs_logo: ASCII art for VS symbol
            standings: Dictionary of team standings
            live_data: Optional live game data for in-progress games
        """
        # Extract team information
        away_team = game["awayTeam"]
        home_team = game["homeTeam"]
        
        away_city = away_team["placeName"]["default"]
        away_name = away_team["commonName"]["default"]
        home_city = home_team["placeName"]["default"]
        home_name = home_team["commonName"]["default"]
        
        # Determine game state
        game_state = game.get("gameState", "FUT")
        
        # Format game time or status
        if game_state in ["LIVE", "CRIT"]:
            game_info = self._format_live_status(live_data) if live_data else "LIVE"
        elif game_state in ["FINAL", "OFF"]:
            game_info = "FINAL"
        else:
            game_info = self._format_game_time(game["startTimeUTC"])
        
        # Build header
        header = [f"{away_name} vs {home_name} ({game_info})"]
        
        # Load and combine logos
        away_logo = self.assets.load_asset("logos", away_name)
        home_logo = self.assets.load_asset("logos", home_name)
        combined_logos, width_away, width_home = AsciiFormatter.combine_logos_with_vs(
            away_logo, vs_logo, home_logo
        )
        
        # Get scores - use live data if available, otherwise use game data
        if live_data:
            away_score = live_data.get("awayTeam", {}).get("score")
            home_score = live_data.get("homeTeam", {}).get("score")
        else:
            away_score = away_team.get("score")
            home_score = home_team.get("score")
        
        # Build information lines below logos
        info_lines = self._build_info_lines(
            away_city, away_name, home_city, home_name,
            away_score, home_score,
            standings, width_away, width_home
        )
        
        # Print complete game box
        AsciiFormatter.print_boxed(header + [""] + combined_logos + [""] + info_lines + [""])
    
    def _format_live_status(self, live_data: Dict) -> str:
        """
        Format live game status with period and time remaining.
        
        Args:
            live_data: Live game data
            
        Returns:
            Formatted status string (e.g., "LIVE - 2nd Period 14:32")
        """
        clock = live_data.get("clock", {})
        period = live_data.get("periodDescriptor", {})
        
        period_num = period.get("number", 1)
        time_remaining = clock.get("timeRemaining", "20:00")
        in_intermission = clock.get("inIntermission", False)
        
        if in_intermission:
            return f"Intermission - After Period {period_num}"
        
        period_label = period.get("periodType", "REG")
        if period_label == "OT":
            return f"LIVE - Overtime {time_remaining}"
        elif period_label == "SO":
            return "LIVE - Shootout"
        else:
            period_names = {1: "1st", 2: "2nd", 3: "3rd"}
            period_str = period_names.get(period_num, f"{period_num}th")
            return f"LIVE - {period_str} Period {time_remaining}"
    
    def _format_game_time(self, start_time_utc: str) -> str:
        """
        Convert UTC game time to local timezone and format.
        
        Args:
            start_time_utc: UTC timestamp string
            
        Returns:
            Formatted string with date and time
        """
        dt_utc = datetime.fromisoformat(start_time_utc.replace("Z", "+00:00"))
        dt_local = dt_utc.astimezone(ZoneInfo(self.timezone))
        
        date_str = dt_local.strftime("%a, %b %d %Y")
        time_str = dt_local.strftime("%I:%M %p")
        
        return f"{date_str} {time_str}"
    
    def _build_info_lines(
        self,
        away_city: str, away_name: str,
        home_city: str, home_name: str,
        away_score: Optional[int], home_score: Optional[int],
        standings: Dict[str, str],
        width_away: int, width_home: int
    ) -> List[str]:
        """
        Build formatted information lines for team names, scores, and records.
        
        Returns:
            List of formatted text lines
        """
        lines = []
        
        # Team names
        away_full_name = f"{away_city} {away_name}"
        home_full_name = f"{home_city} {home_name}"
        lines.append(
            away_full_name.center(width_away) + 
            " " * (LOGO_SPACER_WIDTH + VS_SYMBOL_WIDTH + LOGO_SPACER_WIDTH) + 
            home_full_name.center(width_home)
        )
        lines.append("")  # Blank line
        
        # Scores (if game has started)
        if away_score is not None and home_score is not None:
            lines.extend(self._format_score_lines(
                away_score, home_score, width_away, width_home
            ))
            lines.append("")  # Blank line
        
        # Team records from standings
        away_record = standings.get(away_name, "0-0-0 (0 pts)")
        home_record = standings.get(home_name, "0-0-0 (0 pts)")
        lines.append(
            away_record.center(width_away) + 
            " " * (LOGO_SPACER_WIDTH + VS_SYMBOL_WIDTH + LOGO_SPACER_WIDTH) + 
            home_record.center(width_home)
        )
        lines.append("")  # Blank line
        
        return lines
    
    def _format_score_lines(
        self, 
        away_score: int, 
        home_score: int,
        width_away: int, 
        width_home: int
    ) -> List[str]:
        """
        Format score lines with ASCII art numbers.
        
        Returns:
            List of formatted score lines
        """
        away_score_lines = self.assets.load_number_ascii(away_score)
        home_score_lines = self.assets.load_number_ascii(home_score)
        
        # Ensure both scores have same height
        score_height = max(len(away_score_lines), len(home_score_lines))
        away_score_lines = AsciiFormatter.pad_lines(away_score_lines, score_height)
        home_score_lines = AsciiFormatter.pad_lines(home_score_lines, score_height)
        
        # Combine scores with proper spacing
        score_lines = []
        for a_line, h_line in zip(away_score_lines, home_score_lines):
            score_lines.append(
                a_line.center(width_away) + 
                " " * (LOGO_SPACER_WIDTH + VS_SYMBOL_WIDTH + LOGO_SPACER_WIDTH) + 
                h_line.center(width_home)
            )
        
        return score_lines


# ==============================
# Main Application
# ==============================
class PuckmonApp:
    """Main application class for NHL schedule viewer."""
    
    def __init__(self):
        """Initialize the Puckmon application."""
        self.config = Config()
        self.api_client = NHLApiClient()
        self.assets = AssetManager()
        self.date_selector = DateSelector(self.config.timezone)
        self.game_display = GameDisplay(self.assets, self.config.timezone)
    
    def run(self) -> None:
        """Run the main application loop."""
        # Get date from user
        schedule_date = self.date_selector.get_schedule_date()
        
        # Check if user wants live mode
        if schedule_date == "LIVE":
            self.run_live_mode()
        else:
            self.display_schedule(schedule_date)
    
    def display_schedule(self, schedule_date: str) -> None:
        """
        Display schedule for a specific date.
        
        Args:
            schedule_date: ISO format date string
        """
        # Fetch schedule and standings
        schedule = self.api_client.get_schedule(schedule_date)
        standings = self.api_client.get_standings()
        
        # Load VS symbol once
        vs_logo = self.assets.load_asset("symbols", "vs")
        
        # Display all games for the selected date
        games_found = False
        for game_day in schedule.get("gameWeek", []):
            if game_day.get("date") != schedule_date:
                continue
            
            for game in game_day.get("games", []):
                # Check if game is live or finished - fetch live data
                game_state = game.get("gameState", "FUT")
                live_data = None
                
                if game_state in ["LIVE", "CRIT", "FINAL", "OFF"]:
                    game_id = game.get("id")
                    if game_id:
                        live_data = self.api_client.get_live_game(game_id)
                
                self.game_display.display_game(game, vs_logo, standings, live_data)
                games_found = True
        
        if not games_found:
            print(f"\nNo games found for {schedule_date}")
    
    def run_live_mode(self) -> None:
        """
        Run live mode - continuously refresh scores for games in progress.
        Refreshes every 10 seconds.
        """
        print("\n" + "="*80)
        print("LIVE GAME MODE - Refreshing every 10 seconds")
        print("Press Ctrl+C to exit")
        print("="*80 + "\n")
        
        try:
            while True:
                # Get today's date
                today = datetime.now(tz=ZoneInfo(self.config.timezone)).date().isoformat()
                
                # Fetch current schedule and standings
                schedule = self.api_client.get_schedule(today)
                standings = self.api_client.get_standings()
                vs_logo = self.assets.load_asset("symbols", "vs")
                
                # Find and display only live games
                live_games = []
                for game_day in schedule.get("gameWeek", []):
                    if game_day.get("date") != today:
                        continue
                    
                    for game in game_day.get("games", []):
                        game_state = game.get("gameState", "FUT")
                        if game_state in ["LIVE", "CRIT"]:
                            live_games.append(game)
                
                if not live_games:
                    print("\nNo live games at the moment.")
                    print("Checking again in 10 seconds...\n")
                else:
                    # Clear screen for refresh (works on Unix/Linux/Mac)
                    self._clear_screen()
                    
                    print("\n" + "="*80)
                    print(f"LIVE GAMES - Updated at {datetime.now(tz=ZoneInfo(self.config.timezone)).strftime('%I:%M:%S %p')}")
                    print("="*80 + "\n")
                    
                    # Display each live game with current scores
                    for game in live_games:
                        game_id = game.get("id")
                        live_data = None
                        
                        if game_id:
                            live_data = self.api_client.get_live_game(game_id)
                        
                        self.game_display.display_game(game, vs_logo, standings, live_data)
                
                # Wait 10 seconds before next refresh
                time.sleep(10)
                
        except KeyboardInterrupt:
            print("\n\nExiting live mode...")
    
    def _clear_screen(self) -> None:
        """Clear the terminal screen."""
        # Works for Unix/Linux/Mac
        os.system('clear' if os.name == 'posix' else 'cls')


# ==============================
# Entry Point
# ==============================
def main():
    """Application entry point."""
    app = PuckmonApp()
    app.run()


if __name__ == "__main__":
    main()