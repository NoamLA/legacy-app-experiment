# WAV File Trimmer

A simple Python utility to trim WAV audio files based on start and end times.

## Features

- ✅ Trim WAV files with precise start/end times
- ✅ Command-line interface
- ✅ File information display
- ✅ Error handling and validation
- ✅ No external dependencies (uses built-in `wave` module)
- ✅ Automatic output filename generation

## Usage

### Basic Trimming
```bash
python wav_trimmer.py input.wav --start 10 --end 30
```

### Custom Output File
```bash
python wav_trimmer.py input.wav --start 0 --end 60 --output trimmed.wav
```

### Show File Information
```bash
python wav_trimmer.py input.wav --info
```

## Examples

### Trim from 10 seconds to 30 seconds
```bash
python wav_trimmer.py recording.wav --start 10 --end 30
# Output: recording_trimmed.wav
```

### Trim first minute with custom output name
```bash
python wav_trimmer.py long_audio.wav --start 0 --end 60 --output first_minute.wav
```

### Check audio file details
```bash
python wav_trimmer.py audio.wav --info
```

## Command Line Options

- `input_file`: Input WAV file to trim (required)
- `--start`: Start time in seconds (required for trimming)
- `--end`: End time in seconds (required for trimming)
- `--output, -o`: Output file path (optional)
- `--info`: Show file information only

## Error Handling

The script includes validation for:
- File existence
- WAV file format
- Valid time ranges
- Start time < end time
- End time within file duration

## Requirements

- Python 3.6+
- No external dependencies (uses built-in modules only)

**📅 Last Updated:** December 19, 2024
