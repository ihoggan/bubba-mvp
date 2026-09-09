#!/usr/bin/env python3
"""
Bubba MVP - RDR Troubleshooting Engine
Main entry point for the CLI.

Usage:
  python main.py list              # List available rules
  python main.py search <keywords> # Search for rules
  python main.py start <rule_id>   # Start troubleshooting with a rule
"""

from pathlib import Path
from typing import Optional
import json
from datetime import datetime

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm

from src.engine import RDREngine
from src.models import ConversationState, QuestionType

app = typer.Typer(
    name="bubba",
    help="Bubba: AI-powered troubleshooting assistant",
    no_args_is_help=True
)
console = Console()

# Global state
engine: Optional[RDREngine] = None
state: Optional[ConversationState] = None


def get_engine(rules_file: Path = Path("data/rdr_rules.json")) -> RDREngine:
    """Get or create the RDR engine."""
    global engine
    if engine is None:
        if not rules_file.exists():
            console.print(f"[red]✗ Rules file not found: {rules_file}[/red]")
            raise typer.Exit(1)
        
        console.print(f"[cyan]Loading {len(list(json.load(open(rules_file))))} rules...[/cyan]")
        engine = RDREngine(rules_file)
        console.print(f"[green]✓ Ready[/green]\n")
    
    return engine


@app.command()
def list(category: Optional[str] = None):
    """List available troubleshooting rules."""
    eng = get_engine()
    
    if category:
        rules = eng.list_rules_by_category(category)
        title = f"Rules in '{category}'"
    else:
        rules = list(eng.rules.values())
        title = f"All {len(rules)} Rules"

    table = Table(title=title)
    table.add_column("Rule ID", style="cyan", no_wrap=True)
    table.add_column("Name", style="green")
    table.add_column("Category", style="magenta")
    table.add_column("Recurrence", style="yellow")

    for rule in sorted(rules, key=lambda r: (r.category, r.rule_id)):
        if not category or rule.category == category:
            table.add_row(
                rule.rule_id,
                rule.name[:40],
                rule.category,
                str(rule.recurrence)
            )

    console.print()
    console.print(table)
    console.print()


@app.command()
def search(keywords: str):
    """Search for rules by keyword."""
    eng = get_engine()
    
    kw_list = keywords.split()
    results = eng.find_rules(kw_list)
    
    if not results:
        console.print(f"[yellow]⚠ No rules matching: {keywords}[/yellow]\n")
        return
    
    console.print(f"\n[green]✓ Found {len(results)} rule(s):[/green]\n")
    for rule in results:
        console.print(f"  [cyan]{rule.rule_id:15}[/cyan] {rule.name}")
        if rule.tags:
            console.print(f"    Tags: {', '.join(rule.tags)}")
        console.print()


@app.command()
def start(rule_id: str):
    """Start a guided troubleshooting session."""
    global state
    eng = get_engine()
    
    rule = eng.get_rule(rule_id)
    if not rule:
        console.print(f"[red]✗ Rule '{rule_id}' not found[/red]")
        raise typer.Exit(1)

    # Welcome
    console.print(f"\n[bold cyan]{'='*50}[/bold cyan]")
    console.print(f"[bold cyan]  {rule.name}[/bold cyan]")
    console.print(f"[bold cyan]{'='*50}[/bold cyan]\n")
    
    if rule.description:
        console.print(f"[dim]{rule.description}[/dim]\n")

    # Initialize session
    state = ConversationState(
        session_id=f"session-{datetime.now().isoformat()}",
        rule_id=rule_id,
        current_question_id=rule.entry_point
    )

    # Question loop
    while True:
        question = eng.get_question(rule_id, state.current_question_id)
        if not question:
            console.print("[red]✗ Question not found[/red]")
            break

        # Display question
        console.print(f"[bold]Q{question.seq}: {question.text}[/bold]")
        
        if question.help_text:
            console.print(f"[dim]💡 {question.help_text}[/dim]")

        # Get input
        if question.type == QuestionType.YES_NO:
            answer = Prompt.ask("[yellow]Your answer[/yellow]", choices=["yes", "no"])
        elif question.type == QuestionType.CHOICE:
            answer = Prompt.ask(
                "[yellow]Your answer[/yellow]",
                choices=question.choices or [""],
                default=question.choices[0] if question.choices else ""
            )
        else:
            answer = Prompt.ask("[yellow]Your answer[/yellow]")

        # Process
        state.operator_answers[question.id] = answer
        state.path_taken.append(question.id)

        next_id, next_q, fix, escalation_msg = eng.process_answer(rule_id, question.id, answer)

        if escalation_msg:
            console.print(f"\n[yellow bold]⚠ Escalation Required[/yellow bold]")
            console.print(f"[yellow]{escalation_msg}[/yellow]\n")
            state.status = "escalated"
            break

        if next_q:
            state.current_question_id = next_q.id
            console.print()
            continue

        if fix:
            # Display fix
            console.print(f"\n[bold green]✓ Resolution:[/bold green]")
            console.print(f"[bold green]{fix.title}[/bold green]\n")
            
            for step in fix.steps:
                console.print(f"  [cyan]→[/cyan] {step}")
            
            console.print(f"\n[yellow]Confidence: {int(fix.confidence * 100)}%[/yellow]")
            
            if fix.preventive:
                console.print(f"\n[bold yellow]⚠ Preventive Action:[/bold yellow]")
                console.print(f"[yellow]{fix.preventive}[/yellow]")
            
            state.status = "completed"
            state.final_fix_id = next_id

            # Ask about outcome
            console.print()
            if Confirm.ask("Did this fix resolve the issue?", default=True):
                console.print("[green]✓ Excellent! Glad we could help.[/green]")
            else:
                console.print("[yellow]⚠ Sorry to hear. Consider escalating or reaching out.[/yellow]")
            
            break

    # Summary
    console.print(f"\n[cyan]{'='*50}[/cyan]")
    console.print(f"[cyan]Session Complete[/cyan]")
    console.print(f"Status: [cyan]{state.status}[/cyan] | Rule: [cyan]{rule_id}[/cyan]")
    console.print(f"Questions: {len(state.path_taken)} | Session: [dim]{state.session_id}[/dim]")
    console.print(f"[cyan]{'='*50}[/cyan]\n")
    
    # Save session
    save_session(state)


def save_session(session: ConversationState):
    """Save session for audit trail."""
    session_dir = Path("data/sessions")
    session_dir.mkdir(parents=True, exist_ok=True)
    
    session_file = session_dir / f"{session.session_id.replace(':', '-')}.json"
    with open(session_file, "w") as f:
        json.dump(session.dict(), f, indent=2, default=str)
    
    console.print(f"[dim]Session saved: {session_file}[/dim]")


@app.command()
def version():
    """Show version."""
    console.print("[cyan]Bubba MVP v0.1.0[/cyan]")


if __name__ == "__main__":
    app()
