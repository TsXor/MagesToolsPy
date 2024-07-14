from pathlib import Path
from mages_tools.mpk import unpack, repack

import click

@click.group()
def cli():
    pass

@cli.command()
@click.argument('src')
@click.argument('dst')
def upk(src: str, dst: str):
    unpack(Path(src), Path(dst))

@cli.command()
@click.argument('src')
@click.argument('dst')
def rpk(src: str, dst: str):
    repack(Path(src), Path(dst))

cli()
