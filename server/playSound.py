#!/usr/bin/env python3
"""
Play audio files to specific channels on multi-channel audio interface.

This script plays MP3 (or WAV) files to specific output channels on the
UMC1820 audio interface (or any multi-channel device). Can play up to 8
different sounds simultaneously on different channels.

Usage:
    # List available audio devices
    uv run playSound.py --list

    # Play single sound on channel 3
    uv run playSound.py sound/file1.mp3:3 --device "UMC1820"

    # Play multiple sounds simultaneously on different channels
    uv run playSound.py sound/file1.mp3:1 sound/file2.mp3:3 sound/file3.mp3:5 --device "UMC1820"

    # Play up to 8 sounds at once
    uv run playSound.py file1.mp3:1 file2.mp3:2 file3.mp3:3 file4.mp3:4 file5.mp3:5 --device "UMC1820"
"""

import sys
import argparse
import signal
import numpy as np
import sounddevice as sd
import soundfile as sf


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully."""
    print("\n\nPlayback interrupted by user")
    sd.stop()  # Stop any playing audio
    print("Audio stopped. Exiting...")
    sys.exit(0)


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


def play_audio_to_channels(audio_specs, device=None, normalize=False):
    """
    Play multiple audio files to specific output channels simultaneously.

    Args:
        audio_specs: List of (audio_file, channel) tuples
        device: Device name or index (None = default device)
        normalize: If True, normalize all audio to the same peak level
    """
    if len(audio_specs) > 8:
        print(f"Warning: Maximum 8 simultaneous sounds supported. Using first 8.")
        audio_specs = audio_specs[:8]

    print(f"\nLoading {len(audio_specs)} audio file(s)...")
    if normalize:
        print("Volume normalization: ENABLED")

    # Load all audio files
    loaded_audio = []
    max_sample_rate = 0

    for audio_file, channel in audio_specs:
        print(f"\n  [{channel}] {audio_file}")

        try:
            # Load audio file with soundfile
            data, sample_rate = sf.read(audio_file, dtype='float32')

            # Handle stereo/mono - mix to mono
            if len(data.shape) == 2:  # Stereo
                samples = data.mean(axis=1)
            else:  # Mono
                samples = data

            duration = len(samples) / sample_rate
            print(f"      Duration: {duration:.2f}s, Sample rate: {sample_rate} Hz")

            loaded_audio.append({
                'samples': samples,
                'sample_rate': sample_rate,
                'channel': channel,
                'file': audio_file
            })

            max_sample_rate = max(max_sample_rate, sample_rate)

        except Exception as e:
            print(f"      Error loading file: {e}")
            continue

    if not loaded_audio:
        print("Error: No audio files loaded successfully")
        return

    # Resample all audio to the highest sample rate if needed
    for audio in loaded_audio:
        if audio['sample_rate'] != max_sample_rate:
            # Simple resampling by repeating/skipping samples
            ratio = max_sample_rate / audio['sample_rate']
            new_length = int(len(audio['samples']) * ratio)
            audio['samples'] = np.interp(
                np.linspace(0, len(audio['samples']) - 1, new_length),
                np.arange(len(audio['samples'])),
                audio['samples']
            )
            audio['sample_rate'] = max_sample_rate

    # Normalize audio levels if requested
    if normalize and loaded_audio:
        print("\nNormalizing audio levels...")
        target_peak = 0.9  # Target peak level (90% of max to avoid clipping)

        for audio in loaded_audio:
            current_peak = np.abs(audio['samples']).max()
            if current_peak > 0:
                # Calculate gain to reach target peak
                gain = target_peak / current_peak
                audio['samples'] = audio['samples'] * gain
                print(f"  [{audio['channel']}] {audio['file']}")
                print(f"      Peak: {current_peak:.3f} -> {target_peak:.3f} (gain: {gain:.2f}x)")

    # Find the longest audio duration
    max_length = max(len(audio['samples']) for audio in loaded_audio)

    print(f"\nTotal playback duration: {max_length / max_sample_rate:.2f} seconds")

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

    # Validate all channel numbers
    channels_used = []
    for audio in loaded_audio:
        channel = audio['channel']
        if channel < 1 or channel > max_channels:
            print(f"Error: Channel {channel} is out of range (1-{max_channels})")
            return
        channels_used.append(channel)

    print(f"\nPlaying on channel(s): {', '.join(map(str, sorted(channels_used)))}")
    print("Press Ctrl+C to stop playback")

    # Set up signal handler for graceful interruption
    signal.signal(signal.SIGINT, signal_handler)

    # Create multi-channel output array (all channels start silent)
    output = np.zeros((max_length, max_channels), dtype=np.float32)

    # Mix each audio file into its designated channel
    for audio in loaded_audio:
        channel_idx = audio['channel'] - 1  # Convert to 0-indexed
        samples = audio['samples']

        # Pad with silence if shorter than max_length
        if len(samples) < max_length:
            padded = np.zeros(max_length, dtype=np.float32)
            padded[:len(samples)] = samples
            samples = padded

        # Add to the output channel
        output[:, channel_idx] = samples

    # Play audio
    try:
        sd.play(output, samplerate=max_sample_rate, device=device_idx)
        sd.wait()  # Wait for playback to finish
        print("\nPlayback complete!")
    except KeyboardInterrupt:
        # This might not be reached due to signal handler, but just in case
        sd.stop()
        print("\nPlayback interrupted")
        sys.exit(0)


def main():
    parser = argparse.ArgumentParser(
        description='Play audio files to specific channels on multi-channel audio interface. '
                    'Supports playing up to 8 sounds simultaneously.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List available devices
  %(prog)s --list

  # Play single sound on channel 3
  %(prog)s sound/file.mp3:3 --device UMC1820

  # Play multiple sounds simultaneously
  %(prog)s sound/sound1.mp3:1 sound/sound2.mp3:3 sound/sound3.mp3:5 --device UMC1820
"""
    )

    parser.add_argument(
        'audio_specs',
        nargs='*',
        help='Audio file(s) with channel in format: file.mp3:channel (e.g., sound.mp3:3)'
    )

    parser.add_argument(
        '--device', '-d',
        help='Audio device name or index (default: system default)'
    )

    parser.add_argument(
        '--normalize', '-n',
        action='store_true',
        help='Normalize audio levels to equalize volume across all sounds'
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

    # Require at least one audio spec if not listing
    if not args.audio_specs:
        parser.print_help()
        print("\nError: At least one audio file specification required (unless using --list)")
        print("Format: file.mp3:channel (e.g., sound/creepy.mp3:3)")
        sys.exit(1)

    # Parse audio specifications
    audio_specs = []
    for spec in args.audio_specs:
        if ':' not in spec:
            print(f"Error: Invalid format '{spec}'. Must be file:channel (e.g., sound.mp3:3)")
            sys.exit(1)

        parts = spec.rsplit(':', 1)  # Split on last colon to handle paths with colons
        if len(parts) != 2:
            print(f"Error: Invalid format '{spec}'. Must be file:channel")
            sys.exit(1)

        file_path = parts[0]
        try:
            channel = int(parts[1])
        except ValueError:
            print(f"Error: Invalid channel number '{parts[1]}' in '{spec}'")
            sys.exit(1)

        audio_specs.append((file_path, channel))

    # Play audio
    try:
        play_audio_to_channels(audio_specs, device=args.device, normalize=args.normalize)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
