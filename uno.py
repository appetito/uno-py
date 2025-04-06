import asyncio
import dataclasses
import json
import logging
from json import JSONDecodeError

import nats


logger = logging.getLogger(__name__)


@dataclasses.dataclass
class Endpoint:
    endpoint: str
    handler: callable


class Handler:
    def __init__(self, handler: callable):
        self.handler = handler

    async def call(self, msg):
        try:
            request = json.loads(msg.data)
            result = await self.handler(request)
            response = {"result": result, "status": "OK"}
            response_encoded = json.dumps(response).encode()
        except JSONDecodeError as e:
            logger.error(f"Nats handler {self.handler} invalid request: {msg.data}")
            response = {"error": str(e), "status": "INVALID_REQUEST"}
            response_encoded = json.dumps(response).encode()
        except Exception as e:
            logger.exception(f"Nats handler {self.handler} error")
            response = {"error": str(e), "status": "INTERNAL_ERROR"}
            response_encoded = json.dumps(response).encode()
        await msg.respond(response_encoded)


class Service:

    __endpoints = []

    def __init__(self, name: str, servers: str):
        self.name = name
        self.servers = servers
        self.nc = None

    async def run(self):
        self.nc = await nats.connect(self.servers)
        logger.info("Connected to nats %s", self.__endpoints)
        await self.subscribe_endpoints()
        while True:
            await asyncio.sleep(1)

    async def subscribe_endpoints(self):
        for ep in self.__endpoints:
            logger.info("Subscribing to endpoint %s.%s", self.name, ep.endpoint)
            await self.nc.subscribe("{}.{}".format(self.name, ep.endpoint), cb=ep.handler.call)


    @classmethod
    def endpoint(cls, endpoint: str):
        logger.info("Registering endpoint %s.%s", self.name, endpoint)
        def decorator(f: callable):
            ep = Endpoint(endpoint, Handler(f))
            cls.__endpoints.append(ep)
            return f
        return decorator



def start_nats_service(name: str, servers: str):
    service = NatsService(name, servers)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(service.run())
