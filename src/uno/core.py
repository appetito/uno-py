import asyncio
import dataclasses
import json
import logging
from json import JSONDecodeError
import signal

import nats
from nats.aio.msg import Msg
import logfire
from logfire.propagate import attach_context, get_context


logger = logging.getLogger(__name__)


STATUS_OK = "OK"
STATUS_INVALID_REQUEST = "INVALID_REQUEST"
STATUS_INTERNAL_ERROR = "INTERNAL_ERROR"


def handler(endpoint: str):
    """
    Decorator to register a handler for a specific endpoint.

    Args:
        endpoint (str): The endpoint to register the handler for.

    Example:

        class TestService(Service):
            @handler("test")
            async def test_handler(self, request):
                pass

    """
    def decorator(f: callable):
        f.__uno_endpoint__ = endpoint
        return f
    return decorator


class ServiceMeta(type):
    def __new__(cls, name, bases, attrs):
        handlers = {}

        for attr_name, attr_value in attrs.items():
            if hasattr(attr_value, '__uno_endpoint__'):
                endpoint = attr_value.__uno_endpoint__
                # handlers[endpoint] = Handler(endpoint, attr_value) #attr_value
                handlers[endpoint] = attr_name
        # Store the handlers in the class
        attrs['_handlers'] = handlers
        return super().__new__(cls, name, bases, attrs)


class Service(metaclass=ServiceMeta):
    """
    A service is a collection of handlers for different endpoints.

    Args:
        name (str): The name of the service.
        servers (str): The NATS servers to connect to.
    """

    def __init__(self, name: str, servers: str ):
        self.name = name
        self.servers = servers
        self.nc = None
        self._is_running = False

    async def run(self):

        loop = asyncio.get_event_loop()
        loop.add_signal_handler(signal.SIGTERM, self.stop)
        loop.add_signal_handler(signal.SIGINT, self.stop)

        logger.info("Starting service %s", self.name)
        self.nc = await nats.connect(self.servers)
        logger.info("Connected to NATS")
        await self.subscribe_endpoints()
        self._is_running = True
        while self._is_running:
            await asyncio.sleep(1)
        await self.nc.close()
        await asyncio.sleep(2)
        logger.info("Service %s stopped", self.name)

    async def dispatch(self, msg: Msg):
        subject = msg.subject
        endpoint = msg.subject.split(".")[-1]
        handler_attr_name = self._handlers[endpoint]
        handler = getattr(self, handler_attr_name)
        ctx = _extract_ctx(msg)
        with attach_context(ctx):
            try:
                request = json.loads(msg.data)
                logger.debug(f"Handling request to endpoint {subject}, payload: {request}")
                with logfire.span(f"uno handle {subject}") as span:
                    span.set_attribute("rpc.system", "uno")
                    result = await handler(request)
                response = {"result": result, "status": STATUS_OK}
                response_encoded = json.dumps(response).encode()
            except JSONDecodeError as e:
                logger.error(f"Invalid request to endpoint {subject}: {msg.data}")
                response = {"error": str(e), "status": STATUS_INVALID_REQUEST}
                response_encoded = json.dumps(response).encode()
            except Exception as e:
                logger.exception(f"Handler {subject} error")
                response = {"error": str(e), "status": STATUS_INTERNAL_ERROR}
                response_encoded = json.dumps(response).encode()
            await msg.respond(response_encoded)
        # await handler(msg)
        
    def stop(self):
        logger.info("Stopping service %s", self.name)
        self._is_running = False

    async def subscribe_endpoints(self):
        for endpoint, handler in self._handlers.items():
            logger.info("Subscribing to endpoint %s.%s", self.name, endpoint)
            await self.nc.subscribe("{}.{}".format(self.name, endpoint), cb=self.dispatch)

    def endpoint(self, endpoint: str):
        """
        Register a handler for a specific endpoint.

        Args:
            endpoint (str): The endpoint to register the handler for.

        Example:
            svc = Service("test", "nats://localhost:4222")
            @svc.endpoint("test")
            def test_handler(request):
                pass
        """

        logger.info("Registering endpoint %s.%s", self.name, endpoint)
        def decorator(f: callable):
            handler = Handler(endpoint, f)
            self._handlers[endpoint] = handler
            return f
        return decorator


class RequestError(Exception):
    pass


def _extract_ctx(msg: Msg) -> dict:
    ctx = {}
    if msg.headers:
        try:
            ctx = json.loads(msg.header.get("baggage", "{}"))
        except JSONDecodeError:
            ctx = {}
            logger.debug("Invalid baggage header: %s", msg.header.get("baggage", None))
    return ctx


class Client:
    """
    Client for a Uno NATS service.
    """

    def __init__(self, service_name: str, nc: nats.NATS):
        self.name = service_name
        self.nc = nc

    async def request(self, endpoint: str, payload: dict | None = None, timeout: int = 2):
        subject = "{}.{}".format(self.name, endpoint)
        with logfire.span(f"uno call {subject}") as span:
            span.set_attribute("rpc.system", "uno")
            logger.debug("Requesting endpoint %s, payload: %s", subject, payload)
            ctx = get_context()
            headers = {"baggage": json.dumps(ctx)}
            if payload is None:
                payload = {}
            data = json.dumps(payload).encode()
            msg = await self.nc.request(subject, data, timeout=timeout, headers=headers)
            response = json.loads(msg.data.decode())
            if response["status"] != "OK":
                logger.error("Request to %s failed: %s", subject, response["error"])
                raise RequestError(response["error"])
            logger.debug("Response of %s: %s", subject, response)
            return response["result"]


def start_nats_service(name: str, servers: str):
    service = Service(name, servers)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(service.run())