# Uno-py

A lightweight microservices framework for building distributed applications with NATS.

## Overview

Uno is a minimalist Python framework that makes it easy to build microservices communicating via [NATS](https://nats.io/). It provides a simple, decorator-based API for defining service endpoints and a client for making requests to those endpoints.

## Features

- Simple service definition with Python decorators
- Automatic request/response JSON serialization and deserialization
- Error handling with appropriate response status codes
- Async/await pattern for efficient I/O operations
- Clean client API for making requests to services

## Installation

```bash
pip install uno
```

## Quick Start

### Creating a Service

```python
import asyncio
from uno import Service

# Create a service named "calculator" connected to a NATS server
calculator = Service("calculator", "nats://localhost:4222")

# Define an endpoint using the decorator
@calculator.endpoint("add")
async def add(request):
    a = request.get("a")
    b = request.get("b")
    if a is None or b is None:
        raise ValueError("Missing required parameters: a, b")
    return a + b

# Run the service
if __name__ == "__main__":
    asyncio.run(calculator.run())
```

### Using the Client

```python
import asyncio
import nats
from uno import Client

async def main():
    # Connect to NATS
    nc = await nats.connect("nats://localhost:4222")
    
    # Create a client for the "calculator" service
    calculator = Client("calculator", nc)
    
    # Make a request to the "add" endpoint
    result = await calculator.request("add", {"a": 5, "b": 3})
    print(f"5 + 3 = {result}")
    
    await nc.close()

if __name__ == "__main__":
    asyncio.run(main())
```

## Error Handling

Uno automatically handles exceptions in your endpoint handlers:

- `JSONDecodeError`: Returns a response with status "INVALID_REQUEST"
- Other exceptions: Returns a response with status "INTERNAL_ERROR" and the exception message

Clients receive these errors as `RequestError` exceptions.

## Advanced Usage

### Custom Middleware

You can extend the `Handler` class to add custom middleware functionality:

```python
from uno import Handler

class LoggingHandler(Handler):
    async def call(self, msg):
        print(f"Request received: {msg.data}")
        await super().call(msg)
        print("Response sent")

# Then use it in your service...
```

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.