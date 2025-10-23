#!/usr/bin/env python3
"""
Play audio files to specific channels on multi-channel audio interface.

This script plays MP3 (or WAV) files to a specific output channel on the
UMC1820 audio interface (or any multi-channel device).

Usage:
    # List available audio devices
    uv run playSound.py --list

    # Play sound on channel 3 (default)
    uv run playSound.py sound/creepy-whistles-66703.mp3

    # Play sound on a specific channel
    uv run playSound.py sound/creepy-whistles-66703.mp3 --channel 5

    # Specify device by name or index
    uv run playSound.py sound/file.mp3 --device "UMC1820" --channel 3
"""

import sys
import argparse
import numpy as np
import sounddevice as sd
import soundfile as sf


def list_audio_devices():
    """List all available audio devices."""
    print("\n" + "=" * 80)
    print("AVAILABLE AUDIO DEVICES")
    print("=" * 80)
    devices = sd.query_devices()
    for idx, device in enumerate(devices):
        print(f"\n[{idx}] {device['name']}")
        print(f"    Max Input Channels:  {device['max_input_channels']}")
        print(f"    Max Output Channels: {device['max_output_channels']}")
        print(f"    Default Sample Rate: {device['default_samplerate']} Hz")
    print("\n")


def find_device_by_name(name):
    """Find device index by name (partial match)."""
    devices = sd.query_devices()
    for idx, device in enumerate(devices):
        if name.lower() in device['name'].lower():
            return idx
    return None


def play_audio_to_channel(audio_file, channel=3, device=None):
    """
    Play audio file to a specific output channel.

    Args:
        audio_file: Path to audio file (MP3, WAV, etc.)
        channel: Output channel number (1-indexed)
        device: Device name or index (None = default device)
    """
    print(f"Loading audio file: {audio_file}")

    # Load audio file with soundfile
    data, sample_rate = sf.read(audio_file, dtype='float32')

    # Handle stereo/mono
    if len(data.shape) == 2:  # Stereo
        num_input_channels = data.shape[1]
        # Mix to mono
        samples = data.mean(axis=1)
    else:  # Mono
        num_input_channels = 1
        samples = data

    duration = len(samples) / sample_rate

    print(f"Audio info:")
    print(f"  Duration: {duration:.2f} seconds")
    print(f"  Sample rate: {sample_rate} Hz")
    print(f"  Input channels: {num_input_channels}")

    # Find device
    device_idx = None
    if device is not None:
        if isinstance(device, int):
            device_idx = device
        else:
            device_idx = find_device_by_name(device)
            if device_idx is None:
                print(f"Error: Device '{device}' not found")
                print("Use --list to see available devices")
                return

    # Get device info
    if device_idx is not None:
        device_info = sd.query_devices(device_idx)
        print(f"\nUsing device: {device_info['name']}")
        print(f"  Output channels available: {device_info['max_output_channels']}")
        max_channels = device_info['max_output_channels']
    else:
        default_device = sd.query_devices(kind='output')
        print(f"\nUsing default output device: {default_device['name']}")
        max_channels = default_device['max_output_channels']

    # Validate channel number
    if channel < 1 or channel > max_channels:
        print(f"Error: Channel {channel} is out of range (1-{max_channels})")
        return

    print(f"\nPlaying on channel {channel}...")

    # Create multi-channel output array
    # All channels silent except the target channel
    num_channels = max_channels
    output = np.zeros((len(samples), num_channels), dtype=np.float32)

    # Put audio data in the specified channel (convert to 0-indexed)
    output[:, channel - 1] = samples

    # Play audio
    sd.play(output, samplerate=sample_rate, device=device_idx)
    sd.wait()  # Wait for playback to finish

    print("Playback complete!")


def main():
    parser = argparse.ArgumentParser(
        description='Play audio files to specific channels on multi-channel audio interface',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        'audio_file',
        nargs='?',
        help='Path to audio file (MP3, WAV, etc.)'
    )

    parser.add_argument(
        '--channel', '-c',
        type=int,
        default=3,
        help='Output channel number (default: 3)'
    )

    parser.add_argument(
        '--device', '-d',
        help='Audio device name or index (default: system default)'
    )

    parser.add_argument(
        '--list', '-l',
        action='store_true',
        help='List all available audio devices'
    )

    args = parser.parse_args()

    # List devices if requested
    if args.list:
        list_audio_devices()
        return

    # Require audio file if not listing
    if not args.audio_file:
        parser.print_help()
        print("\nError: audio_file is required (unless using --list)")
        sys.exit(1)

    # Play audio
    try:
        play_audio_to_channel(
            args.audio_file,
            channel=args.channel,
            device=args.device
        )
    except FileNotFoundError:
        print(f"Error: File not found: {args.audio_file}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
