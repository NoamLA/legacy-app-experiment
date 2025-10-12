#!/usr/bin/env python3
"""
Simple WAV File Trimmer
A utility to trim WAV audio files based on start and end times.
"""

import argparse
import os
import sys
from pathlib import Path
import wave
import struct


class WAVTrimmer:
    """Simple WAV file trimmer using built-in wave module."""
    
    def __init__(self, input_file, output_file=None):
        self.input_file = Path(input_file)
        self.output_file = Path(output_file) if output_file else None
        
        if not self.input_file.exists():
            raise FileNotFoundError(f"Input file not found: {self.input_file}")
        
        if not self.input_file.suffix.lower() == '.wav':
            raise ValueError("Input file must be a WAV file")
    
    def get_audio_info(self):
        """Get basic information about the WAV file."""
        with wave.open(str(self.input_file), 'rb') as wav_file:
            frames = wav_file.getnframes()
            sample_rate = wav_file.getframerate()
            duration = frames / sample_rate
            channels = wav_file.getnchannels()
            sample_width = wav_file.getsampwidth()
            
            return {
                'frames': frames,
                'sample_rate': sample_rate,
                'duration': duration,
                'channels': channels,
                'sample_width': sample_width
            }
    
    def trim(self, start_time, end_time):
        """
        Trim the WAV file from start_time to end_time.
        
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
        
        # Calculate frame positions
        start_frame = int(start_time * info['sample_rate'])
        end_frame = int(end_time * info['sample_rate'])
        
        # Generate output filename if not provided
        if self.output_file is None:
            name = self.input_file.stem
            suffix = self.input_file.suffix
            self.output_file = self.input_file.parent / f"{name}_trimmed{suffix}"
        
        # Read and write the trimmed audio
        with wave.open(str(self.input_file), 'rb') as input_wav:
            with wave.open(str(self.output_file), 'wb') as output_wav:
                # Set output parameters
                output_wav.setnchannels(info['channels'])
                output_wav.setsampwidth(info['sample_width'])
                output_wav.setframerate(info['sample_rate'])
                
                # Seek to start position
                input_wav.setpos(start_frame)
                
                # Read and write the trimmed section
                frames_to_read = end_frame - start_frame
                frames_read = 0
                
                while frames_read < frames_to_read:
                    # Read in chunks to handle large files
                    chunk_size = min(1024, frames_to_read - frames_read)
                    frames = input_wav.readframes(chunk_size)
                    if not frames:
                        break
                    output_wav.writeframes(frames)
                    frames_read += len(frames) // (info['channels'] * info['sample_width'])
        
        return str(self.output_file)
    
    def print_info(self):
        """Print information about the WAV file."""
        info = self.get_audio_info()
        print(f"File: {self.input_file}")
        print(f"Duration: {info['duration']:.2f} seconds")
        print(f"Sample Rate: {info['sample_rate']} Hz")
        print(f"Channels: {info['channels']}")
        print(f"Sample Width: {info['sample_width']} bytes")
        print(f"Total Frames: {info['frames']}")


def main():
    """Command line interface for the WAV trimmer."""
    parser = argparse.ArgumentParser(
        description="Simple WAV file trimmer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python wav_trimmer.py input.wav --start 10 --end 30
  python wav_trimmer.py input.wav --start 0 --end 60 --output trimmed.wav
  python wav_trimmer.py input.wav --info
        """
    )
    
    parser.add_argument('input_file', help='Input WAV file to trim')
    parser.add_argument('--start', type=float, help='Start time in seconds')
    parser.add_argument('--end', type=float, help='End time in seconds')
    parser.add_argument('--output', '-o', help='Output file path (optional)')
    parser.add_argument('--info', action='store_true', help='Show file information only')
    
    args = parser.parse_args()
    
    try:
        trimmer = WAVTrimmer(args.input_file, args.output)
        
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
