"""
NexusKV Interactive CLI & Cluster Management Tool
=================================================

Provides interactive REPL, cluster health checks, key-value lookup,
and node administrative controls using Click and Rich terminal formatting.
"""

import click
from rich.console import Console
from rich.table import Table
from nexus_core.database import NexusDatabase

console = Console()

@click.group()
def main():
    """NexusKV Distributed Database CLI Tool"""
    pass

@main.command()
@click.option("--key", "-k", required=True, help="Key to fetch")
def get(key: str):
    """Retrieve value for a key"""
    db = NexusDatabase()
    found, val = db.get(key.encode("utf-8"))
    if found and val is not None:
        console.print(f"[bold green]FOUND:[/bold green] {key} => [cyan]{val.decode('utf-8')}[/cyan]")
    else:
        console.print(f"[bold red]NOT FOUND:[/bold red] Key {key} does not exist")
    db.close()

@main.command()
@click.option("--key", "-k", required=True, help="Key to set")
@click.option("--value", "-v", required=True, help="Value to set")
def put(key: str, value: str):
    """Insert or update a key-value pair"""
    db = NexusDatabase()
    db.put(key.encode("utf-8"), value.encode("utf-8"))
    console.print(f"[bold green]SUCCESS:[/bold green] Set {key} => {value}")
    db.close()

@main.command()
def status():
    """View cluster node topology and storage health"""
    db = NexusDatabase()
    info = db.get_cluster_status()

    table = Table(title="NexusKV Node Status")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="magenta")

    for k, v in info.items():
        table.add_row(str(k), str(v))

    console.print(table)
    db.close()

if __name__ == "__main__":
    main()
