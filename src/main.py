import asyncio
import typer
import logging
import json
import os
from typing import Optional
from pathlib import Path
from rich.console import Console
from rich.logging import RichHandler

from src.pipeline import run_lead_pipeline
from src.modules.export.exporter import export_to_csv, export_to_excel

# Setup Rich Logging
logging.basicConfig(
    level="INFO",
    format="%(message)s",
    datefmt="[%X]",
    handlers=[
        RichHandler(rich_tracebacks=True),
        logging.FileHandler("scraper.log", encoding="utf-8")
    ]
)
logger = logging.getLogger("leadscraper")

app = typer.Typer(help="LeadScraper CLI - AI-Powered Lead Generation")
console = Console()

@app.command()
def scrape(
    domain: str = typer.Argument(..., help="The target domain to scrape (e.g. example.com)"),
    name: Optional[str] = typer.Option(None, help="Person name for pattern prediction (e.g. 'John Doe')"),
    output: str = typer.Option("leads", help="Output filename base (without extension)"),
    format: str = typer.Option("csv", help="Output format: csv, json, excel")
):
    """
    Scrape and verify emails for a single domain.
    """
    console.print(f"[bold green]Starting scraping for {domain}...[/bold green]")
    
    results = asyncio.run(run_lead_pipeline(domain, name))
    
    if not results:
        console.print("[bold red]No leads found or pipeline failed.[/bold red]")
        return
        
    save_results(results, output, format)

from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskID
from rich.table import Table

# ... imports ...

@app.command()
def bulk(
    file: Path = typer.Argument(..., exists=True, help="Path to text file with domains (one per line)"),
    output: str = typer.Option("bulk_leads", help="Output filename base"),
    format: str = typer.Option("csv", help="Output format: csv, json, excel")
):
    """
    Bulk scrape multiple domains from a file (Sequential processing).
    """
    domains = file.read_text().splitlines()
    domains = [d.strip() for d in domains if d.strip()]
    
    console.print(f"[bold green]Found {len(domains)} domains to process.[/bold green]")
    
    all_results = []
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console
    ) as progress:
        task = progress.add_task("[cyan]Processing domains...", total=len(domains))
        
        for domain in domains:
            progress.update(task, description=f"[cyan]Scraping {domain}...")
            
            try:
                # Run pipeline for each domain
                domain_results = asyncio.run(run_lead_pipeline(domain))
                all_results.extend(domain_results)
                
            except Exception as e:
                console.print(f"[bold red]Error processing {domain}: {e}[/bold red]")
            
            progress.advance(task)
            
    if all_results:
        print_summary_table(all_results)
        save_results(all_results, output, format)
    else:
        console.print("[yellow]No results found in bulk process.[/yellow]")

def print_summary_table(results: list):
    """Prints a summary table of the findings."""
    table = Table(title="Lead Generation Summary")
    table.add_column("Email", style="cyan")
    table.add_column("Domain", style="magenta")
    table.add_column("Status", style="green")
    table.add_column("SMTP", style="yellow")
    
    for item in results:
        smtp_status = str(item.get("verification", {}).get("smtp", "N/A"))
        status_color = "green" if item['status'] == 'valid' else "red"
        if item['status'] == 'catch_all': status_color = "yellow"
        
        table.add_row(
            item.get("email", "Unknown"),
            item.get("domain", "Unknown"),
            f"[{status_color}]{item.get('status', 'Unknown')}[/{status_color}]",
            smtp_status
        )
    
    console.print(table)

def save_results(results: list, filename_base: str, format: str):


    """Helper to save results in requested format."""
    console.print(f"\n[bold green]Saving {len(results)} results...[/bold green]")
    
    if "json" in format:
        file_path = f"{filename_base}.json"
        with open(file_path, "w") as f:
            json.dump(results, f, indent=2)
        console.print(f"Saved to {file_path}")
        
    if "csv" in format:
        file_path = f"{filename_base}.csv"
        export_to_csv(results, file_path)
        console.print(f"Saved to {file_path}")
        
    if "excel" in format or "xlsx" in format:
        file_path = f"{filename_base}.xlsx"
        export_to_excel(results, file_path)
        console.print(f"Saved to {file_path}")

if __name__ == "__main__":
    app()
