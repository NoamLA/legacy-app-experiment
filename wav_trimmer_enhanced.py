#!/usr/bin/env python3
"""
Enhanced WAV File Trimmer
A utility to trim audio files (including compressed formats) using pydub.
"""

import argparse
import os
import sys
from pathlib import Path

try:
    from pydub import AudioSegment
    from pydub.utils import which
except ImportError:
    print("Error: pydub is required for this enhanced trimmer.")
    print("Install it with: pip install pydub")
    print("You may also need ffmpeg: brew install ffmpeg (on macOS)")
    sys.exit(1)


class EnhancedAudioTrimmer:
    """Enhanced audio trimmer using pydub for better format support."""
    
    def __init__(self, input_file, output_file=None):
        self.input_file = Path(input_file)
        self.output_file = Path(output_file) if output_file else None
        
        if not self.input_file.exists():
            raise FileNotFoundError(f"Input file not found: {self.input_file}")
    
    def get_audio_info(self):
        """Get basic information about the audio file."""
        try:
            audio = AudioSegment.from_file(str(self.input_file))
            duration = len(audio) / 1000.0  # Convert from milliseconds to seconds
            
            return {
                'duration': duration,
                'sample_rate': audio.frame_rate,
                'channels': audio.channels,
                'sample_width': audio.sample_width,
                'format': self.input_file.suffix.lower()
            }
        except Exception as e:
            raise ValueError(f"Could not read audio file: {e}")
    
    def trim(self, start_time, end_time):
        """
        Trim the audio file from start_time to end_time.
        
        Args:
            start_time (float): Start time in seconds
            end_time (float): End time in seconds
        """
        # Get audio info
        info = self.get_audio_info()
        
        # Validate times
        if start_time < 0:
            raise ValueError("Start time cannot be negative")
        if end_time > info['duration']:
            raise ValueError(f"End time ({end_time}s) exceeds file duration ({info['duration']:.2f}s)")
        if start_time >= end_time:
            raise ValueError("Start time must be less than end time")
        
        # Load the audio file
        audio = AudioSegment.from_file(str(self.input_file))
        
        # Convert times to milliseconds
        start_ms = int(start_time * 1000)
        end_ms = int(end_time * 1000)
        
        # Trim the audio
        trimmed_audio = audio[start_ms:end_ms]
        
        # Generate output filename if not provided
        if self.output_file is None:
            name = self.input_file.stem
            suffix = self.input_file.suffix
            self.output_file = self.input_file.parent / f"{name}_trimmed{suffix}"
        
        # Export the trimmed audio
        trimmed_audio.export(str(self.output_file), format="wav")
        
        return str(self.output_file)
    
    def print_info(self):
        """Print information about the audio file."""
        info = self.get_audio_info()
        print(f"File: {self.input_file}")
        print(f"Duration: {info['duration']:.2f} seconds")
        print(f"Sample Rate: {info['sample_rate']} Hz")
        print(f"Channels: {info['channels']}")
        print(f"Sample Width: {info['sample_width']} bytes")
        print(f"Format: {info['format']}")


def main():
    """Command line interface for the enhanced audio trimmer."""
    parser = argparse.ArgumentParser(
        description="Enhanced audio file trimmer (supports multiple formats)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python wav_trimmer_enhanced.py input.wav --start 10 --end 30
  python wav_trimmer_enhanced.py input.mp3 --start 0 --end 60 --output trimmed.wav
  python wav_trimmer_enhanced.py input.wav --info
        """
    )
    
    parser.add_argument('input_file', help='Input audio file to trim')
    parser.add_argument('--start', type=float, help='Start time in seconds')
    parser.add_argument('--end', type=float, help='End time in seconds')
    parser.add_argument('--output', '-o', help='Output file path (optional)')
    parser.add_argument('--info', action='store_true', help='Show file information only')
    
    args = parser.parse_args()
    
    try:
        trimmer = EnhancedAudioTrimmer(args.input_file, args.output)
        
        if args.info:
            trimmer.print_info()
            return
        
        if args.start is None or args.end is None:
            print("Error: Both --start and --end times are required for trimming")
            print("Use --info to see file information")
            sys.exit(1)
        
        print(f"Trimming {args.input_file} from {args.start}s to {args.end}s...")
        output_file = trimmer.trim(args.start, args.end)
        print(f"Trimmed audio saved to: {output_file}")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
