# Sample email archive for testing

Create a ZIP file containing `.eml` email files and upload it via the web UI.

## Quick test (PowerShell)

```powershell
# Example: zip any .eml files you have
Compress-Archive -Path "C:\path\to\your\emails\*.eml" -DestinationPath ".\test_archive.zip"
```

Then upload `test_archive.zip` at http://localhost:3000/upload

## Minimum archive contents

- At least one `.eml` file
- Files must be valid RFC 822 email format
- Supported extensions inside ZIP: `.eml`, `.msg`, `.txt`, `.mime`
