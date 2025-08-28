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

## Configuration

The gateway is configured through a JSON configuration file with the following structure:

```json
{
  "name": "sms-gateway",
  "queues": {
    "sms_queue": {
      "type": "memory",
      "maxsize": 1000
    },
    "integration_queue": {
      "type": "memory",
      "maxsize": 1000
    }
  },
  "sms": {
    "gammu": {
      "enabled": true,
      "name": "sms",
      "port": "/dev/ttyUSB0",
      "connection": "at115200"
    }
  },
  "integration": {
    "telegram": {
      "enabled": true,
      "name": "telegram",
      "token": "your-bot-token"
    }
  },
  "runtime": {
    "poll_delay": 1.0,
    "logging": {
      "default": "INFO",
      "components": {}
    },
    "backoff": {
      "initial_delay": 1.0,
      "max_delay": 60.0,
      "factor": 2.0
    }
  }
}
```

The configuration is split into distinct sections:
- `name`: Gateway instance identifier
- `queues`: Message queue settings for SMS and integration services
- `sms`: SMS service adapters configuration
- `integration`: Integration service adapters (Telegram, Email, etc.)
- `runtime`: System-wide settings including logging configuration

## Testing

The project includes comprehensive tests for all components:

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/services/test_sms.py

# Run with coverage
pytest --cov=sms_gateway
```

Test structure:
- Unit tests for core services
- Integration tests for service combinations
- Mock adapters for external services
- Memory queue tests for message handling

## Dependencies

Core dependencies:
- pydantic: Data validation using Python type annotations
- typing-extensions: Additional typing support
- aiohttp: Async HTTP client/server
- pyserial-asyncio: Async serial port support
- python-gammu: Interface for GSM modems using Gammu library

Development dependencies:
- pytest: Testing framework
- pytest-asyncio: Async test support
- pytest-cov: Coverage reporting
- black: Code formatter
- mypy: Static type checker
- ruff: Fast Python linter

## Service Architecture

The gateway implements a message broker pattern with:

1. Message Services
   - Base message handling service
   - Protocol-specific services (SMS, Telegram, Email)
   - Bi-directional message routing

2. Message Queues
   - In-memory async queue implementation
   - Configurable queue size
   - Message streaming support

3. Adapters
   - Protocol adapters for each service type
   - Stub services for testing
   - Memory queue adapters

4. Features
   - Clean architecture with ports and adapters pattern
   - Structured logging and error handling
   - Support for multiple messaging protocols
   - Separate incoming and outgoing message flows
   - Async/await for efficient I/O handling

## Architecture

See `docs/ARCHITECTURE.md` for detailed architecture documentation.