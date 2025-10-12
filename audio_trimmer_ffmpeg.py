#!/usr/bin/env python3
"""
Audio Trimmer using FFmpeg
A reliable utility to trim audio files using ffmpeg directly.
"""

import argparse
import os
import sys
import subprocess
from pathlib import Path


class FFmpegAudioTrimmer:
    """Audio trimmer using ffmpeg for maximum compatibility."""
    
    def __init__(self, input_file, output_file=None):
        self.input_file = Path(input_file)
        self.output_file = Path(output_file) if output_file else None
        
        if not self.input_file.exists():
            raise FileNotFoundError(f"Input file not found: {self.input_file}")
    
    def get_audio_info(self):
        """Get basic information about the audio file using ffprobe."""
        try:
            cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format',
                str(self.input_file)
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            import json
            info = json.loads(result.stdout)
            format_info = info['format']
            
            duration = float(format_info['duration'])
            bitrate = int(format_info.get('bit_rate', 0))
            
            return {
                'duration': duration,
                'bitrate': bitrate,
                'format': format_info.get('format_name', 'unknown'),
                'size': int(format_info.get('size', 0))
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
        
        # Generate output filename if not provided
        if self.output_file is None:
            name = self.input_file.stem
            suffix = self.input_file.suffix
            self.output_file = self.input_file.parent / f"{name}_trimmed{suffix}"
        
        # Calculate duration
        duration = end_time - start_time
        
        # Build ffmpeg command
        cmd = [
            'ffmpeg', '-y',  # Overwrite output file
            '-i', str(self.input_file),  # Input file
            '-ss', str(start_time),  # Start time
            '-t', str(duration),  # Duration
            '-c', 'copy',  # Copy without re-encoding (faster)
            str(self.output_file)  # Output file
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return str(self.output_file)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"FFmpeg failed: {e.stderr}")
    
    def print_info(self):
        """Print information about the audio file."""
        info = self.get_audio_info()
        print(f"File: {self.input_file}")
        print(f"Duration: {info['duration']:.2f} seconds ({info['duration']/60:.1f} minutes)")
        print(f"Bitrate: {info['bitrate']} bps")
        print(f"Format: {info['format']}")
        print(f"Size: {info['size']/1024/1024:.1f} MB")


def main():
    """Command line interface for the FFmpeg audio trimmer."""
    parser = argparse.ArgumentParser(
        description="Audio file trimmer using FFmpeg (supports all formats)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python audio_trimmer_ffmpeg.py input.wav --start 10 --end 30
  python audio_trimmer_ffmpeg.py input.mp3 --start 0 --end 60 --output trimmed.wav
  python audio_trimmer_ffmpeg.py input.wav --info
        """
    )
    
    parser.add_argument('input_file', help='Input audio file to trim')
    parser.add_argument('--start', type=float, help='Start time in seconds')
    parser.add_argument('--end', type=float, help='End time in seconds')
    parser.add_argument('--output', '-o', help='Output file path (optional)')
    parser.add_argument('--info', action='store_true', help='Show file information only')
    
    args = parser.parse_args()
    
    try:
        trimmer = FFmpegAudioTrimmer(args.input_file, args.output)
        
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
