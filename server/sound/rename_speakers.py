#!/usr/bin/env python3
"""
Rename speaker files with the following mapping:
Speaker1 → Speaker1 (no change)
Speaker2 → Speaker5
Speaker3 → Speaker4
Speaker4 → Speaker3
Speaker5 → Speaker2
"""

import os
from pathlib import Path

# Speaker mapping
SPEAKER_MAP = {
    '1': '1',  # no change
    '2': '5',
    '3': '4',
    '4': '3',
    '5': '2'
}

def main():
    # Directory containing the sound files
    sound_dir = Path(__file__).parent / '2025'

    if not sound_dir.exists():
        print(f"Error: Directory {sound_dir} does not exist")
        return

    # Get all mp3 files
    files = sorted(sound_dir.glob('*.mp3'))

    # First pass: rename to temporary names
    temp_renames = []
    for file in files:
        filename = file.name
        # Parse filename: {number}_Speaker{speaker}.mp3
        if '_Speaker' in filename:
            parts = filename.split('_Speaker')
            number = parts[0]
            old_speaker = parts[1].replace('.mp3', '')

            # Get new speaker number
            new_speaker = SPEAKER_MAP.get(old_speaker)
            if new_speaker and new_speaker != old_speaker:
                temp_name = f"{number}_Speaker{old_speaker}_TEMP.mp3"
                temp_path = sound_dir / temp_name
                print(f"Step 1: {filename} → {temp_name}")
                file.rename(temp_path)
                temp_renames.append((temp_path, number, new_speaker))
            else:
                print(f"Skipping: {filename} (no change needed)")

    # Second pass: rename from temporary to final names
    for temp_path, number, new_speaker in temp_renames:
        final_name = f"{number}_Speaker{new_speaker}.mp3"
        final_path = sound_dir / final_name
        print(f"Step 2: {temp_path.name} → {final_name}")
        temp_path.rename(final_path)

    print(f"\nDone! Renamed {len(temp_renames)} files.")

if __name__ == '__main__':
    main()
