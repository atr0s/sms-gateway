# SMS Gateway Daemon

A Python daemon that handles bi-directional message routing between SMS, Telegram, and Email services.

## Requirements

- Python 3.11 or newer

## Installation

### Option 1: Using Poetry (Recommended)

Poetry provides dependency isolation and better dependency management:

1. Install Poetry if you haven't already:
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

2. Clone and install:
```bash
# Clone the repository
git clone <repository-url>
cd sms-gateway

# Install dependencies
poetry install

# Activate the virtual environment
poetry shell
```

### Option 2: Using pip with virtualenv

1. Create and activate a virtual environment:
```bash
# Create virtualenv
python -m venv venv

# Activate it (Linux/Mac)
source venv/bin/activate
# OR Windows
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Option 3: Direct pip install

For quick testing, you can install directly (not recommended for development):
```bash
pip install -r requirements.txt
```

## Running the Daemon

After installation, you can run the daemon:

```bash
# If using Poetry
poetry run python -m sms_gateway.daemon

# If using virtualenv or direct pip
python -m sms_gateway.daemon
```

The daemon will:
- Initialize stub incoming and outgoing services
- Create in-memory message queues
- Send a test message through the outgoing service
- Check for random incoming messages (1/10 chance per second)

Press Ctrl+C to stop the daemon.

## Dependencies

Core dependencies:
- pydantic: Data validation using Python type annotations
- typing-extensions: Additional typing support

Development dependencies:
- pytest: Testing framework
- black: Code formatter
- mypy: Static type checker
- ruff: Fast Python linter

## Current Features

- Clean architecture with ports and adapters pattern
- In-memory message queue implementation
- Stub services for testing
- Structured logging
- Support for multiple adapters (SMS, Telegram, Email)
- Separate incoming and outgoing message flows

## Architecture

See `docs/ARCHITECTURE.md` for detailed architecture documentation.