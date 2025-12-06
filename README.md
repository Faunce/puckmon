# puckmon
A linux app to monitor NHL scores

## Installation

### Quick Install
```bash
pip install git+https://github.com/Faunce/puckmon.git
```

### Install from Source
```bash
git clone https://github.com/Faunce/puckmon.git
cd puckmon
pip install .
```

### Development Installation
```bash
git clone https://github.com/Faunce/puckmon.git
cd puckmon
pip install -e ".[dev]"
```

## Usage

After installation, run:
```bash
puckmon
```

### Menu Options

1. **Yesterday** - Show games from yesterday
2. **Today** - Show today's games (with live scores)
3. **Tomorrow** - Show tomorrow's schedule
4. **Live games** - Auto-refreshing view of all live games (updates every 10s)
5. **Specify date** - Enter a custom date (MM-DD-YYYY)

## Configuration

The default config will be created at `~/.config/puckmon/config.yml` on first run.

Edit it to set your timezone:
```yaml
timezone: "US/Eastern"
```

Supported timezones: Any valid IANA timezone (e.g., "US/Pacific", "US/Central", "America/Toronto")

## Requirements

- Python 3.9 or higher
- curl (for API requests)
- Internet connection

## Credits
All ascii logos are based upon the NHL logos which I do not own in any way, and do not intend to ever profit from in any way.  This software is free, and will always be free.
The API endpoints used were provided by https://github.com/Zmalski/NHL-API-Reference.  A fantastic collection of public API endpoints from the NHL

## AI Usage 
Claude was used for the ascii formatting portion of this project.  