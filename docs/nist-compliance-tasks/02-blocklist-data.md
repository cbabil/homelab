# Task 02: Create Blocklist Data Files

## Overview

Create the data files containing common passwords and context-specific words for the blocklist service.

## Files to Create

1. `backend/data/blocklist/common_passwords.txt.gz` - Compressed common passwords
2. `backend/data/blocklist/context_words.txt` - Service-specific words to block

## Requirements

### Common Passwords File

Source from SecLists or similar curated list. Include:
- Top 10,000 most common passwords
- Passwords from major breach corpuses
- Common keyboard patterns

### Context Words File

Application-specific words that shouldn't appear in passwords:
- Service name variations
- Default usernames
- Common tech terms

## Implementation

### Directory Structure

```
backend/
└── data/
    └── blocklist/
        ├── common_passwords.txt.gz
        └── context_words.txt
```

### common_passwords.txt.gz

Download and compress the SecLists common passwords:

```bash
# Download top 10k passwords from SecLists
curl -L https://raw.githubusercontent.com/danielmiessler/SecLists/master/Passwords/Common-Credentials/10k-most-common.txt -o common_passwords.txt

# Compress
gzip common_passwords.txt
mv common_passwords.txt.gz backend/data/blocklist/
```

Alternatively, create manually with known common passwords:

```text
password
123456
12345678
qwerty
abc123
monkey
1234567
letmein
trustno1
dragon
baseball
iloveyou
master
sunshine
ashley
bailey
passw0rd
shadow
123123
654321
superman
qazwsx
michael
football
password1
password123
welcome
jesus
ninja
mustang
password12
...
```

### context_words.txt

Create with service-specific terms:

```text
# Application name variations
tomo
home-lab
tomomanager
assistant

# Common usernames
admin
administrator
root
user
guest
test
demo

# Service-related
server
docker
container
deploy
backup

# Company/brand names (add your own)
anthropic
claude
```

## Script to Generate Blocklist

Create `backend/scripts/generate_blocklist.py`:

```python
#!/usr/bin/env python3
"""
Generate password blocklist from SecLists.
"""

import gzip
import urllib.request
from pathlib import Path

SECLIST_URL = "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Passwords/Common-Credentials/10k-most-common.txt"
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "blocklist"

def download_and_compress():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Download
    print(f"Downloading from {SECLIST_URL}")
    with urllib.request.urlopen(SECLIST_URL) as response:
        passwords = response.read().decode('utf-8')

    # Normalize and dedupe
    password_set = set()
    for line in passwords.splitlines():
        pwd = line.strip().lower()
        if pwd and len(pwd) >= 3:
            password_set.add(pwd)

    # Write compressed
    output_path = OUTPUT_DIR / "common_passwords.txt.gz"
    with gzip.open(output_path, 'wt', encoding='utf-8') as f:
        for pwd in sorted(password_set):
            f.write(pwd + '\n')

    print(f"Written {len(password_set)} passwords to {output_path}")

def create_context_words():
    context_words = [
        # Application
        "tomo", "tomomanager", "assistant",
        # Common usernames
        "admin", "administrator", "root", "user", "guest", "test", "demo",
        # Service terms
        "server", "docker", "container", "deploy", "backup",
    ]

    output_path = OUTPUT_DIR / "context_words.txt"
    with open(output_path, 'w', encoding='utf-8') as f:
        for word in context_words:
            f.write(word + '\n')

    print(f"Written {len(context_words)} context words to {output_path}")

if __name__ == "__main__":
    download_and_compress()
    create_context_words()
```

## File Size Estimates

| File | Uncompressed | Compressed |
|------|--------------|------------|
| common_passwords.txt | ~100KB | ~40KB |
| context_words.txt | ~500B | N/A |

## Acceptance Criteria

- [ ] `backend/data/blocklist/` directory exists
- [ ] `common_passwords.txt.gz` contains at least 10,000 passwords
- [ ] `context_words.txt` contains application-specific terms
- [ ] Files are properly formatted (one entry per line)
- [ ] Blocklist service can load both files successfully
