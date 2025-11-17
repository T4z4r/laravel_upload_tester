# Laravel Upload Tester

A Python GUI tool for testing file upload vulnerabilities in Laravel applications, focusing on extension bypass and path traversal attacks.

## Features

- Test remote Laravel applications via URL
- Test local Laravel projects by starting a development server
- Extension bypass testing with various file extensions
- Path traversal testing with common payloads
- User-friendly GUI interface

## Requirements

- Python 3.x
- PHP (for local server testing)
- Laravel project (for local testing)

## Installation

1. Clone or download the repository.
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

Run the script:
```
python laravel_upload_tester.py
```

### Remote Testing
1. Select "Remote (URL)" mode.
2. Enter the base URL of the Laravel application.
3. Enter the upload endpoint (e.g., /upload).
4. Choose a file to upload.
5. Select test type: Extension Bypass or Path Traversal.
6. Click "Start Testing".

### Local Testing
1. Select "Local (Folder)" mode.
2. Browse and select the Laravel project folder.
3. Click "Start Server" to launch the Laravel development server.
4. Follow the same steps as remote testing.

## Disclaimer

This tool is for educational and security testing purposes only. Use responsibly and only on systems you have permission to test.