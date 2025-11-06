# 🎬 Trakt Filler

<div align="center">

**Intelligently fill gaps in your Trakt.tv watch history**

[Features](#-features) • [Installation](#-installation) • [Quick Start](#-quick-start) • [Usage](#-usage) • [Examples](#-examples)

</div>

---

## 📖 Overview

Ever manually marked some episodes as watched on Trakt and now have gaps in your watch history? This tool intelligently fills those gaps by:

- 🧠 Analyzing your actual viewing patterns
- 📅 Using proportional time distribution
- 🛡️ Respecting episode air dates (never marks before it aired)
- ⏰ Using precise timestamps (hours/minutes, not just dates)
- 🎯 Giving you full control over what to fill

### The Problem

You watched episodes 1, 2, 5, 6, and 7 of a show, but forgot to mark episodes 3 and 4. Your Trakt history looks incomplete.

### The Solution

This script intelligently marks episodes 3 and 4 as watched using realistic dates based on:
- When you actually watched episodes 2 and 5
- The episode air dates
- Your viewing patterns for that show

The result looks natural and maintains the integrity of your watch history! ✨

---

## ✨ Features

### Core Functionality

- **🔄 Gap Filling**: Fills missing episodes between your first and last watched episode
- **⬅️ Beginning Filling**: Marks episodes before your first watched episode
- **➡️ Ending Filling**: Marks episodes after your last watched episode
- **🎯 Selective Processing**: Choose exactly which shows to process

### Intelligence

- **📊 Pattern Analysis**: Learns your viewing habits per show
- **⏱️ Proportional Distribution**: Spreads episodes across actual time gaps
- **📺 Air Date Validation**: Never marks episodes as watched before they aired
- **🕐 Time Precision**: Uses hours and minutes for binge-watching scenarios
- **🔒 Safety Buffer**: Adds 12-hour buffer after air date for realism

### User Experience

- **📈 Progress Tracking**: Visual progress bar during analysis
- **🎛️ Flexible Selection**: Multiple selection methods with modifiers
- **✅ Confirmation**: Shows exactly what will change before proceeding
- **🔐 Secure Credentials**: Stores API credentials in separate file
- **📝 Detailed Output**: Clear feedback on what was processed

---

## 🚀 Installation

### Prerequisites

- Python 3.6 or higher
- A Trakt.tv account
- Trakt API application credentials

### Step 1: Clone the Repository

```bash
git clone https://github.com/Judzim/Trakt-filler.git
cd Trakt-filler
```

### Step 2: Install Dependencies

```bash
pip install requests
```

That's it! No other dependencies required.

---

## ⚡ Quick Start

### 1. Get Trakt API Credentials

1. Go to [Trakt API Applications](https://trakt.tv/oauth/applications)
2. Click **"New Application"**
3. Fill in the form:
   - **Name**: Trakt Gap Filler (or any name)
   - **Redirect uri**: `urn:ietf:wg:oauth:2.0:oob`
4. Mark both permissions (checkin, scrobble)
5. Click **"Save App"**
6. Copy your **Client ID** and **Client Secret**

### 2. Authenticate

```bash
python trakt_authenticate.py
```

Follow the prompts to:
- Enter your Client ID and Secret
- Authorize the application in your browser
- Automatically save credentials to `trakt_credentials.txt`

### 3. Run the Gap Filler

```bash
python trakt_gap_filler.py
```

That's it! The script will analyze your watch history and guide you through filling gaps.

---

## 📚 Usage

### Basic Workflow

1. **Analysis**: Script analyzes all your watched shows
2. **Display**: Shows you which shows have missing episodes
3. **Selection**: You choose which shows to process
4. **Confirmation**: Review what will be changed
5. **Processing**: Episodes are marked with intelligent dates

### Selection Syntax

#### Modifiers

- **No modifier** (e.g., `1`): Fill gaps only (default)
- **`b`** (e.g., `1b`): Fill beginning + gaps
- **`e`** (e.g., `1e`): Fill gaps + ending
- **`be`** (e.g., `1be`): Fill beginning + gaps + ending (complete)

#### Selection Methods

| Input | Description |
|-------|-------------|
| `1 3 5` | Fill gaps in shows 1, 3, and 5 |
| `1b` | Fill beginning and gaps for show 1 |
| `1e` | Fill gaps and ending for show 1 |
| `1be` | Complete fill for show 1 |
| `1-3` | Fill gaps for shows 1, 2, and 3 |
| `1-3b` | Fill beginning + gaps for shows 1, 2, and 3 |
| `1b 3e 5be` | Mixed: show 1 (beginning+gaps), show 3 (gaps+ending), show 5 (complete) |
| `all` | Fill gaps for all shows |
| `allbe` | Complete fill for all shows |

---

## 💡 Examples

### Example 1: Simple Gap Filling

**Your Watch History:**
- Breaking Bad: Watched S01E01, S01E02, S01E05, S01E06
- Missing: S01E03, S01E04

**Script Output:**
```
[1] 📺 Breaking Bad
    Watched: 60/62 episodes
    Missing: 2 gaps

Your selection: 1
```

**Result:** S01E03 and S01E04 are marked as watched with dates distributed between when you watched S01E02 and S01E05.

---

### Example 2: Complete Show Filling

**Your Watch History:**
- The Office: Started watching at S02E05, stopped at S05E10
- Missing: S01-S02E04 (beginning) and S05E11-S09E23 (ending)

**Script Output:**
```
[1] 📺 The Office
    Watched: 87/201 episodes
    Missing: 34 before first, 8 gaps, 72 after last

Your selection: 1be
```

**Result:** All episodes are marked as watched:
- Beginning episodes use your viewing pattern, working backward from S02E05
- Gaps are filled proportionally
- Ending episodes use your pattern, working forward from S05E10

---

### Example 3: Multiple Shows with Different Options

```
[1] 📺 Breaking Bad
    Missing: 4 gaps

[2] 📺 Game of Thrones  
    Missing: 15 before first, 3 gaps

[3] 📺 Friends
    Missing: 8 gaps, 20 after last

Your selection: 1 2b 3e
```

**Result:**
- **Breaking Bad**: Gaps only
- **Game of Thrones**: Beginning + gaps
- **Friends**: Gaps + ending

---

### Example 4: Binge Watching Detection

**Your Watch History:**
- Stranger Things S01E01 watched at 2:00 PM
- Stranger Things S01E08 watched at 10:30 PM same day
- Missing: S01E02 through S01E07

**Script Behavior:**
- Detects 8.5-hour gap
- Distributes 6 episodes across that time
- Results in realistic hourly intervals:
  ```
  S01E02: 3:15 PM
  S01E03: 4:30 PM
  S01E04: 5:45 PM
  S01E05: 7:00 PM
  S01E06: 8:15 PM
  S01E07: 9:30 PM
  ```

---

## 🧠 How It Works

### Intelligent Date Calculation

1. **Fetch Watch History**: Gets your actual watch timestamps from Trakt
2. **Analyze Patterns**: Calculates your average viewing interval per show
3. **Identify Missing**: Categorizes episodes as beginning/gaps/ending
4. **Calculate Dates**: 
   - **Gaps**: Proportional distribution between boundaries
   - **Beginning**: Work backward from first watched
   - **Ending**: Work forward from last watched
5. **Validate Air Dates**: Ensures no episode is marked before it aired + 12h buffer
6. **Submit**: Batch uploads to Trakt with precise timestamps

### Air Date Protection

```python
if calculated_date < (air_date + 12_hours):
    use air_date + 12_hours instead
```

This ensures your watch history is always realistic and possible.

---

## 📊 Technical Details

### API Endpoints Used

- `GET /users/{user}/watched/shows` - Fetch watched shows
- `GET /users/{user}/history/shows` - Fetch detailed watch history with timestamps
- `GET /shows/{id}/seasons?extended=episodes` - Fetch episode metadata including air dates
- `POST /sync/history` - Submit watched episodes with custom timestamps

### Date Format

All dates use ISO 8601 format with UTC timezone:
```
2025-11-06T20:30:15Z
```

### Rate Limits

Trakt API allows **1000 requests per 5 minutes** for authenticated users. This script is designed to stay well within these limits.

---

## 📁 Project Structure

```
trakt-gap-filler/
├── trakt_gap_filler.py      # Main script
├── trakt_authenticate.py    # Authentication helper
├── trakt_credentials.txt    # Your credentials (auto-generated)
├── .gitignore               # Excludes credentials from git
└── README.md                # This file
```

---

## 🔒 Security

### Credentials Protection

- Credentials are stored in `trakt_credentials.txt` (not in the code)
- File is automatically excluded from git via `.gitignore`
- Never commit your credentials file to version control

### Disclaimers

1. Don't share your `trakt_credentials.txt` file
2. If credentials are compromised, revoke them at [Trakt Applications](https://trakt.tv/oauth/applications)
3. Consider using environment variables in production environments

---

## 🐛 Troubleshooting

### "401 Unauthorized" Error

**Problem**: Access token expired or invalid

**Solution**: Run `python trakt_authenticate.py` to get a new token

### "404 Not Found" Error

**Problem**: Username incorrect or profile not public

**Solution**: 
1. Check your username in `trakt_credentials.txt`
2. Ensure your watch history is public or you're properly authenticated

---

## 📜 License

This project is licensed under the MIT License - see below for details:

```
MIT License

Copyright (c) 2025

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

</div>
