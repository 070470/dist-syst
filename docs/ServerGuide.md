# Server Guide

## Server Access Instructions

### Initial Access
1. Connect to a UH gateway computer using:
```bash
ssh username@pangolin.it.helsinki.fi
```

2. Access the servers:
```bash
# Server 1
ssh username@svm-11.cs.helsinki.fi    # IP: 128.214.11.91

# Server 2
ssh username@svm-11-2.cs.helsinki.fi  # IP: 128.214.9.25

# Server 3
ssh username@svm-11-3.cs.helsinki.fi  # IP: 128.214.9.26
```

## Installation

### For each server:

1. Create directories:
```bash
mkdir -p ~/distributed-file-service
mkdir -p ~/distributed-file-service/distfiles
```

2. Install Flask:
```bash
pip3 install --user flask
```

3. Set permissions:
```bash
chmod 755 ~/distributed-file-service/distfiles
```

## Server Configuration

Each server needs specific configuration parameters. Copy the appropriate configuration based on the server:

### Server 1 (svm-11):
```python
HOST = "128.214.11.91"
PORT = 65421 
SOCK_PORT = 65411
NODES = [
    ("128.214.9.25", 65411),
    ("128.214.9.26", 65411)
]
```

### Server 2 (svm-11-2):
```python
HOST = "128.214.9.25"
PORT = 65422
SOCK_PORT = 65411
NODES = [
    ("128.214.11.91", 65411),
    ("128.214.9.26", 65411)
]
```

### Server 3 (svm-11-3):
```python
HOST = "128.214.9.26"
PORT = 65423
SOCK_PORT = 65411
NODES = [
    ("128.214.11.91", 65411),
    ("128.214.9.25", 65411)
]
```

## Running the Servers

1. On each server:
```bash
cd ~/distributed-file-service
python3 server.py
```

2. Expected output:
```
[timestamp] INFO in server: Socket server listening on [HOST]:[SOCK_PORT]
* Running on http://[HOST]:[PORT]
```

## Basic Testing

### File Upload Test:
```bash
# Create test file 
echo "Test content $(date)" > test.txt

# Upload to server 1
curl -F "file=@test.txt" http://128.214.11.91:65421/file/test.txt
```

# Verify file existence
ls -l distfiles/test.txt

# Test retrieval from all servers (all should show identical content)
curl http://128.214.11.91:65421/file/test.txt
curl http://128.214.9.25:65422/file/test.txt
curl http://128.214.9.26:65423/file/test.txt
```

### Version Control Test

1. Update File Test:
```bash
# Create updated version
echo "This is version 2 - timestamp: $(date)" > test.txt

# Upload to server 2 (different from initial upload)
curl -F "file=@test.txt" http://128.214.9.25:65422/file/test.txt

# Verify all servers have new version
curl http://128.214.11.91:65421/file/test.txt
curl http://128.214.9.25:65422/file/test.txt
curl http://128.214.9.26:65423/file/test.txt
```

