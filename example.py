import asyncio
import nats

from logging import config
import logfire

from uno import Service, handler, Client

logfire.configure(
    service_name="example",
)

class ExampleService(Service):

    @handler("test")
    async def test_handler(self, request):
        print("test called, request:", request)
        client = Client("example", self.nc)
        resp = await client.request("inner", request)
        return resp

    @handler("inner")
    async def inner_handler(self, request):
        print("inner called, request:", request)
        return {"message": "OK"}


async def main():
    nc = await nats.connect("nats://localhost:4222")
    svc = ExampleService("example", "nats://localhost:4222")
    example_client = Client("example", nc)

    asyncio.create_task(svc.run())
    await asyncio.sleep(1.5)
    resp = await example_client.request("test", {"foo": "bar"})
    print("response:", resp)
    svc.stop()



if __name__ == "__main__":
    # simple log config:
    config.dictConfig({
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
                "formatter": "default",
            },
        },
        "loggers": {
            "": {
                "handlers": ["console"],
                "level": "DEBUG",    
                "propagate": True,               
            }
        }
    })
    asyncio.run(main())