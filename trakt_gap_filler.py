#!/usr/bin/env python3
"""
Trakt Episode Gap Filler - Complete Edition
Intelligently fills gaps, beginnings, and endings of TV shows.
"""

import requests
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Set, Tuple, Optional

BASE_URL = "https://api.trakt.tv"


def load_credentials(filename='trakt_credentials.txt'):
    """Load credentials from text file."""
    if not os.path.exists(filename):
        print(f"❌ Error: Credentials file '{filename}' not found!")
        print("Please create the file and add your credentials.")
        exit(1)

    credentials = {}
    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                key, value = line.split('=', 1)
                credentials[key.strip()] = value.strip()

    required = ['CLIENT_ID', 'CLIENT_SECRET', 'ACCESS_TOKEN', 'USERNAME']
    missing = [key for key in required if key not in credentials or credentials[key].startswith('YOUR_')]

    if missing:
        print(f"❌ Error: Missing credentials in {filename}:")
        for key in missing:
            print(f"   - {key}")
        print("\nPlease fill in all required credentials.")
        exit(1)

    return credentials


def get_headers(credentials):
    """Generate API headers from credentials."""
    return {
        "Content-Type": "application/json",
        "trakt-api-version": "2",
        "trakt-api-key": credentials['CLIENT_ID'],
        "Authorization": f"Bearer {credentials['ACCESS_TOKEN']}"
    }


def get_watched_shows(headers, username) -> List[Dict]:
    """Get all watched shows with episode details."""
    url = f"{BASE_URL}/users/{username}/watched/shows"
    params = {"extended": "full"}

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()

    return response.json()


def get_watch_history(headers, username) -> Dict:
    """Get detailed watch history with timestamps."""
    url = f"{BASE_URL}/users/{username}/history/shows"
    params = {"limit": 10000}

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()

    history = {}
    for entry in response.json():
        show_id = entry['show']['ids']['trakt']
        episode = entry['episode']
        season_num = episode['season']
        episode_num = episode['number']
        watched_at = entry['watched_at']

        if show_id not in history:
            history[show_id] = {}

        key = (season_num, episode_num)
        if key not in history[show_id] or watched_at > history[show_id][key]:
            history[show_id][key] = watched_at

    return history


def get_all_episodes(headers, show_id: str) -> List[Dict]:
    """Get all episodes for a show with air dates."""
    url = f"{BASE_URL}/shows/{show_id}/seasons"
    params = {"extended": "episodes"}

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()

    episodes = []
    for season in response.json():
        if season['number'] == 0:
            continue
        for episode in season.get('episodes', []):
            episodes.append({
                'season': season['number'],
                'episode': episode['number'],
                'ids': episode['ids'],
                'first_aired': episode.get('first_aired')
            })

    return episodes


def parse_datetime(dt_str: Optional[str]) -> Optional[datetime]:
    """Parse ISO datetime string."""
    if not dt_str:
        return None
    try:
        if dt_str.endswith('Z'):
            dt_str = dt_str[:-1] + '+00:00'
        return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
    except:
        return None


def calculate_average_interval(watch_history: Dict) -> timedelta:
    """Calculate average time between watched episodes."""
    if len(watch_history) < 2:
        return timedelta(days=2)  # Default

    dates = sorted([parse_datetime(dt) for dt in watch_history.values() if dt])
    if len(dates) < 2:
        return timedelta(days=2)

    intervals = []
    for i in range(1, len(dates)):
        interval = dates[i] - dates[i-1]
        if timedelta(0) < interval < timedelta(days=365):  # Ignore huge gaps
            intervals.append(interval)

    if not intervals:
        return timedelta(days=2)

    avg = sum(intervals, timedelta(0)) / len(intervals)
    return avg


def find_all_missing_episodes(watched_episodes: Set[tuple], all_episodes: List[Dict], 
                               watch_history: Dict) -> Dict:
    """Find beginning, gaps, and ending episodes."""
    watched_list = sorted(list(watched_episodes))
    episode_map = {(ep['season'], ep['episode']): ep for ep in all_episodes}

    result = {
        'beginning': [],
        'gaps': [],
        'ending': []
    }

    if not watched_list:
        # Nothing watched - all are beginning episodes
        result['beginning'] = all_episodes
        return result

    first_watched = watched_list[0]
    last_watched = watched_list[-1]

    for ep in all_episodes:
        ep_tuple = (ep['season'], ep['episode'])

        if ep_tuple in watched_episodes:
            continue

        # Categorize
        if ep_tuple < first_watched:
            result['beginning'].append(ep)
        elif ep_tuple > last_watched:
            result['ending'].append(ep)
        else:
            # It's a gap
            prev_watched = None
            next_watched = None

            for watched in watched_list:
                if watched < ep_tuple:
                    prev_watched = watched
                elif watched > ep_tuple and next_watched is None:
                    next_watched = watched
                    break

            gap_info = {
                'season': ep['season'],
                'episode': ep['episode'],
                'ids': ep['ids'],
                'first_aired': ep.get('first_aired'),
                'prev_watched': prev_watched,
                'next_watched': next_watched,
                'prev_watched_at': watch_history.get(prev_watched) if prev_watched else None,
                'next_watched_at': watch_history.get(next_watched) if next_watched else None
            }
            result['gaps'].append(gap_info)

    return result


def calculate_intelligent_dates_for_gaps(gaps: List[Dict]) -> List[Dict]:
    """Calculate intelligent dates for gap episodes."""
    if not gaps:
        return gaps

    gap_groups = {}
    for gap in gaps:
        key = (gap['prev_watched'], gap['next_watched'])
        if key not in gap_groups:
            gap_groups[key] = []
        gap_groups[key].append(gap)

    for (prev, next), group_gaps in gap_groups.items():
        prev_date = parse_datetime(group_gaps[0]['prev_watched_at']) if group_gaps[0]['prev_watched_at'] else None
        next_date = parse_datetime(group_gaps[0]['next_watched_at']) if group_gaps[0]['next_watched_at'] else None

        group_gaps.sort(key=lambda x: (x['season'], x['episode']))

        if prev_date and next_date:
            total_gap = next_date - prev_date
            num_episodes = len(group_gaps)
            interval = total_gap / (num_episodes + 1)

            for idx, gap in enumerate(group_gaps, 1):
                proposed_date = prev_date + (interval * idx)
                air_date = parse_datetime(gap['first_aired'])
                if air_date:
                    earliest_possible = air_date + timedelta(hours=12)
                    if proposed_date < earliest_possible:
                        proposed_date = earliest_possible
                    if proposed_date > next_date:
                        proposed_date = next_date - timedelta(minutes=30 * (num_episodes - idx))

                gap['calculated_watched_at'] = proposed_date.isoformat().replace('+00:00', 'Z')

        elif prev_date:
            for idx, gap in enumerate(group_gaps, 1):
                days_offset = idx * 2
                proposed_date = prev_date + timedelta(days=days_offset)
                air_date = parse_datetime(gap['first_aired'])
                if air_date:
                    earliest_possible = air_date + timedelta(hours=12)
                    if proposed_date < earliest_possible:
                        proposed_date = earliest_possible
                gap['calculated_watched_at'] = proposed_date.isoformat().replace('+00:00', 'Z')

        elif next_date:
            for idx, gap in enumerate(reversed(group_gaps), 1):
                days_offset = idx * 2
                proposed_date = next_date - timedelta(days=days_offset)
                air_date = parse_datetime(gap['first_aired'])
                if air_date:
                    earliest_possible = air_date + timedelta(hours=12)
                    if proposed_date < earliest_possible:
                        proposed_date = earliest_possible
                gap['calculated_watched_at'] = proposed_date.isoformat().replace('+00:00', 'Z')

        else:
            for idx, gap in enumerate(group_gaps):
                air_date = parse_datetime(gap['first_aired'])
                if air_date:
                    offset_days = min(idx + 1, 7)
                    proposed_date = air_date + timedelta(days=offset_days, hours=20)
                else:
                    proposed_date = datetime.now() - timedelta(days=len(group_gaps) - idx)
                gap['calculated_watched_at'] = proposed_date.isoformat().replace('+00:00', 'Z')

    return gaps


def calculate_dates_for_beginning(episodes: List[Dict], first_watched_date: Optional[str], 
                                   avg_interval: timedelta) -> List[Dict]:
    """Calculate dates for episodes before first watched."""
    episodes.sort(key=lambda x: (x['season'], x['episode']))

    if first_watched_date:
        anchor_date = parse_datetime(first_watched_date)
    else:
        # No watch history, use most recent air date + some time
        latest_air = None
        for ep in reversed(episodes):
            air_date = parse_datetime(ep['first_aired'])
            if air_date:
                latest_air = air_date
                break
        anchor_date = latest_air + timedelta(days=30) if latest_air else datetime.now()

    # Work backwards from first watched
    for idx, ep in enumerate(reversed(episodes), 1):
        offset = avg_interval * idx
        proposed_date = anchor_date - offset

        air_date = parse_datetime(ep['first_aired'])
        if air_date:
            earliest_possible = air_date + timedelta(hours=12)
            if proposed_date < earliest_possible:
                proposed_date = earliest_possible

        ep['calculated_watched_at'] = proposed_date.isoformat().replace('+00:00', 'Z')

    return episodes


def calculate_dates_for_ending(episodes: List[Dict], last_watched_date: Optional[str], 
                                avg_interval: timedelta) -> List[Dict]:
    """Calculate dates for episodes after last watched."""
    episodes.sort(key=lambda x: (x['season'], x['episode']))

    if last_watched_date:
        anchor_date = parse_datetime(last_watched_date)
    else:
        # No watch history, use earliest air date
        earliest_air = None
        for ep in episodes:
            air_date = parse_datetime(ep['first_aired'])
            if air_date:
                earliest_air = air_date
                break
        anchor_date = earliest_air - timedelta(days=30) if earliest_air else datetime.now() - timedelta(days=365)

    # Work forwards from last watched
    for idx, ep in enumerate(episodes, 1):
        offset = avg_interval * idx
        proposed_date = anchor_date + offset

        air_date = parse_datetime(ep['first_aired'])
        if air_date:
            earliest_possible = air_date + timedelta(hours=12)
            if proposed_date < earliest_possible:
                proposed_date = earliest_possible

        ep['calculated_watched_at'] = proposed_date.isoformat().replace('+00:00', 'Z')

    return episodes


def mark_episodes_watched(headers, episodes: List[Dict], show_title: str) -> bool:
    """Mark episodes as watched."""
    if not episodes:
        return True

    episode_data = []
    for ep in episodes:
        watched_at = ep.get('calculated_watched_at')
        if not watched_at:
            watched_at = datetime.now().isoformat() + "Z"

        episode_data.append({
            "watched_at": watched_at,
            "ids": ep['ids']
        })

    payload = {"episodes": episode_data}
    url = f"{BASE_URL}/sync/history"
    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 201:
        result = response.json()
        added = result.get('added', {}).get('episodes', 0)
        print(f"  ✓ Successfully marked {added} episodes as watched for '{show_title}'")
        return True
    else:
        print(f"  ✗ Failed: {response.status_code}")
        return False


def parse_selection(input_str: str, max_num: int) -> List[Tuple[int, str]]:
    """Parse selection with b/e/be modifiers. Returns [(show_num, modifier)]."""
    selected = []

    try:
        parts = input_str.strip().split()
        for part in parts:
            if '-' in part and not any(x in part for x in ['b', 'e']):
                # Range without modifier
                start, end = part.split('-')
                start, end = int(start), int(end)
                if start < 1 or end > max_num or start > end:
                    print(f"⚠️  Invalid range: {part}")
                    continue
                for num in range(start, end + 1):
                    selected.append((num, ''))
            else:
                # Single number with possible modifier
                modifier = ''
                num_str = part

                if part.endswith('be'):
                    modifier = 'be'
                    num_str = part[:-2]
                elif part.endswith('b'):
                    modifier = 'b'
                    num_str = part[:-1]
                elif part.endswith('e'):
                    modifier = 'e'
                    num_str = part[:-1]

                # Handle range with modifier (e.g., 1-3b)
                if '-' in num_str:
                    start, end = num_str.split('-')
                    start, end = int(start), int(end)
                    if start < 1 or end > max_num or start > end:
                        print(f"⚠️  Invalid range: {part}")
                        continue
                    for num in range(start, end + 1):
                        selected.append((num, modifier))
                else:
                    num = int(num_str)
                    if num < 1 or num > max_num:
                        print(f"⚠️  Invalid: {part}")
                        continue
                    selected.append((num, modifier))

    except ValueError as e:
        print(f"❌ Error parsing: {e}")
        return []

    return selected


def main():
    """Main function."""
    print("=" * 70)
    print("Trakt Episode Gap Filler - Complete Edition")
    print("=" * 70)
    print()

    credentials = load_credentials()
    headers = get_headers(credentials)
    username = credentials['USERNAME']
    print(f"✓ Authenticated as: {username}")
    print()

    print("Fetching watch history...")
    try:
        watch_history_raw = get_watch_history(headers, username)
        print(f"✓ Loaded watch history")
    except:
        print(f"⚠️  Could not fetch detailed history")
        watch_history_raw = {}

    print("Fetching watched shows...")
    try:
        watched_shows = get_watched_shows(headers, username)
    except requests.exceptions.HTTPError as e:
        print(f"❌ Error: {e}")
        return

    print(f"Found {len(watched_shows)} watched shows")
    print()

    shows_with_missing = []

    print("Analyzing shows for gaps...")
    total = len(watched_shows)
    for idx, show_data in enumerate(watched_shows, 1):
        # Progress bar
        percent = (idx / total) * 100
        bar_length = 40
        filled = int(bar_length * idx / total)
        bar = '█' * filled + '-' * (bar_length - filled)
        print(f'\r[{bar}] {percent:.0f}% ({idx}/{total})', end='', flush=True)

        show = show_data['show']
        show_title = show['title']
        show_id = show['ids']['trakt']

        watched_episodes = set()
        for season in show_data['seasons']:
            season_num = season['number']
            for episode in season['episodes']:
                episode_num = episode['number']
                watched_episodes.add((season_num, episode_num))

        all_episodes = get_all_episodes(headers, show_id)
        show_history = watch_history_raw.get(show_id, {})

        missing = find_all_missing_episodes(watched_episodes, all_episodes, show_history)

        if missing['beginning'] or missing['gaps'] or missing['ending']:
            # Calculate average interval for this show
            avg_interval = calculate_average_interval(show_history)

            # Get first and last watched dates
            first_watched_date = None
            last_watched_date = None
            if show_history:
                sorted_dates = sorted(show_history.values())
                first_watched_date = sorted_dates[0] if sorted_dates else None
                last_watched_date = sorted_dates[-1] if sorted_dates else None

            shows_with_missing.append({
                'title': show_title,
                'show_id': show_id,
                'missing': missing,
                'watched_count': len(watched_episodes),
                'total_count': len(all_episodes),
                'avg_interval': avg_interval,
                'first_watched_date': first_watched_date,
                'last_watched_date': last_watched_date
            })

    print()  # New line after progress
    print()

    if not shows_with_missing:
        print("✓ No missing episodes found!")
        return

    print("=" * 70)
    print(f"Found {len(shows_with_missing)} show(s) with missing episodes:")
    print("=" * 70)
    print()

    for idx, show in enumerate(shows_with_missing, 1):
        print(f"[{idx}] 📺 {show['title']}")
        print(f"    Watched: {show['watched_count']}/{show['total_count']} episodes")

        parts = []
        if show['missing']['beginning']:
            parts.append(f"{len(show['missing']['beginning'])} before first")
        if show['missing']['gaps']:
            parts.append(f"{len(show['missing']['gaps'])} gaps")
        if show['missing']['ending']:
            parts.append(f"{len(show['missing']['ending'])} after last")

        print(f"    Missing: {', '.join(parts)}")
        print()

    print("=" * 70)
    print()
    print("Select shows to fill:")
    print("  - Gaps only: 1 3 5")
    print("  - With beginning: 1b 3b")
    print("  - With ending: 1e 3e")
    print("  - Beginning + gaps + ending: 1be 3be")
    print("  - Range: 1-3 or 1-3be")
    print("  - Mixed: 1b 3 5-7e")
    print("  - All with all parts: allbe")
    print("  - Cancel: leave empty")
    print()

    selection_input = input("Your selection: ").strip().lower()

    if not selection_input or selection_input == 'cancel':
        print("\nCancelled.")
        return

    # Handle special 'all' cases
    if selection_input.startswith('all'):
        modifier = selection_input[3:] if len(selection_input) > 3 else ''
        selected = [(i, modifier) for i in range(1, len(shows_with_missing) + 1)]
    else:
        selected = parse_selection(selection_input, len(shows_with_missing))

    if not selected:
        print("\n❌ No valid shows selected.")
        return

    # Prepare episodes to mark
    to_process = []
    for show_num, modifier in selected:
        show = shows_with_missing[show_num - 1]
        episodes_to_mark = []

        # Determine what to include
        include_beginning = 'b' in modifier
        include_gaps = True  # Always include gaps
        include_ending = 'e' in modifier

        if include_beginning and show['missing']['beginning']:
            beginning_eps = calculate_dates_for_beginning(
                show['missing']['beginning'].copy(),
                show['first_watched_date'],
                show['avg_interval']
            )
            episodes_to_mark.extend(beginning_eps)

        if include_gaps and show['missing']['gaps']:
            gap_eps = calculate_intelligent_dates_for_gaps(show['missing']['gaps'].copy())
            episodes_to_mark.extend(gap_eps)

        if include_ending and show['missing']['ending']:
            ending_eps = calculate_dates_for_ending(
                show['missing']['ending'].copy(),
                show['last_watched_date'],
                show['avg_interval']
            )
            episodes_to_mark.extend(ending_eps)

        if episodes_to_mark:
            to_process.append({
                'show': show,
                'episodes': episodes_to_mark,
                'modifier': modifier,
                'show_num': show_num
            })

    # Confirmation
    print()
    print("=" * 70)
    print(f"Will mark {sum(len(p['episodes']) for p in to_process)} episodes:")
    print("=" * 70)
    for item in to_process:
        mod_text = f" ({item['modifier']})" if item['modifier'] else ""
        print(f"  [{item['show_num']}] {item['show']['title']}{mod_text}: {len(item['episodes'])} episodes")
    print()

    confirm = input("Proceed? (yes/no): ").strip().lower()
    if confirm not in ['yes', 'y']:
        print("\nCancelled.")
        return

    print()
    print("=" * 70)
    print("Marking episodes as watched...")
    print("=" * 70)
    print()

    success_count = 0
    for item in to_process:
        print(f"Processing: {item['show']['title']}")
        if mark_episodes_watched(headers, item['episodes'], item['show']['title']):
            success_count += 1

    print()
    print("=" * 70)
    print(f"✓ Done! Successfully processed {success_count}/{len(to_process)} show(s).")
    print("=" * 70)


if __name__ == "__main__":
    main()
