import click
import asyncio
import os
import nats

from .core import Client

@click.group()
def cli():
    pass


@cli.command()
@click.argument('service')
def probe(service: str):
    click.echo(f'Probing service {service}')
    async def _probe():
        instance_id = os.environ.get("INSTANCE_ID")
        nc = await nats.connect(os.environ.get("NATS_SERVERS"))
        c = Client(service, nc)
        await c.request(f"healthz-{instance_id}")
    
    try:
        asyncio.run(_probe())
    except Exception as e:
        click.echo(f"Probe failed: {e}", err=True)
        exit(1)
    else:
        click.echo("Probe succeeded")


def main():
    cli()

if __name__ == "__main__":
    main()
