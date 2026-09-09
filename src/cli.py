"""
Typer CLI for Bubba's troubleshooting flow.
Guides operators through RDR questions and captures their input.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.syntax import Syntax
from rich.table import Table

from src.engine import RDREngine
from src.models import ConversationState, QuestionType, LearnedRule

app = typer.Typer(help="Bubba RDR troubleshooting CLI")
console = Console()

# Global engine instance
engine: Optional[RDREngine] = None
state: Optional[ConversationState] = None


def init_engine(rules_file: Path = Path("data/rdr_rules.json")):
    """Initialize the RDR engine."""
    global engine
    if engine is None:
        console.print("[cyan]Loading RDR rules...[/cyan]")
        engine = RDREngine(rules_file)
        console.print(f"[green]✓ Loaded {len(engine.rules)} rules[/green]\n")


@app.command()
def list_rules(category: Optional[str] = None):
    """List available troubleshooting rules."""
    init_engine()
    
    if category:
        rules = engine.list_rules_by_category(category)
        console.print(f"\nRules in category '{category}':\n")
    else:
        rules = list(engine.rules.values())
        console.print(f"\nAll {len(rules)} rules:\n")

    table = Table(title="Available Rules")
    table.add_column("Rule ID", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Category", style="magenta")
    table.add_column("Last Seen", style="yellow")

    for rule in sorted(rules, key=lambda r: r.rule_id):
        if not category or rule.category == category:
            table.add_row(
                rule.rule_id,
                rule.name,
                rule.category,
                rule.last_seen or "Unknown"
            )

    console.print(table)


@app.command()
def search(keywords: str):
    """Search for rules by keyword."""
    init_engine()
    
    kw_list = keywords.split()
    results = engine.find_rules(kw_list)
    
    if not results:
        console.print(f"[yellow]No rules found matching: {keywords}[/yellow]")
        return
    
    console.print(f"\n[green]Found {len(results)} rule(s):[/green]\n")
    for rule in results:
        console.print(f"  [cyan]{rule.rule_id}[/cyan] — {rule.name}")
        if rule.description:
            console.print(f"    {rule.description}\n")


@app.command()
def troubleshoot(rule_id: str):
    """Start a guided troubleshooting session with a specific rule."""
    init_engine()
    global state
    
    rule = engine.get_rule(rule_id)
    if not rule:
        console.print(f"[red]✗ Rule '{rule_id}' not found[/red]")
        return

    console.print(f"\n[bold cyan]╔════════════════════════════════════════╗[/bold cyan]")
    console.print(f"[bold cyan]║  Troubleshooting: {rule.name:<26}  ║[/bold cyan]")
    console.print(f"[bold cyan]╚════════════════════════════════════════╝[/bold cyan]\n")

    if rule.description:
        console.print(f"[dim]{rule.description}[/dim]\n")

    # Initialize session state
    state = ConversationState(
        session_id=f"session-{datetime.now().isoformat()}",
        rule_id=rule_id,
        current_question_id=rule.entry_point
    )

    # Main question loop
    while True:
        question = engine.get_question(rule_id, state.current_question_id)
        if not question:
            console.print("[red]✗ Question not found[/red]")
            break

        # Display question
        console.print(f"\n[bold]Q{question.seq}: {question.text}[/bold]")
        
        if question.help_text:
            console.print(f"[dim]💡 {question.help_text}[/dim]")

        # Get operator input
        if question.type == QuestionType.YES_NO:
            answer = Prompt.ask("[yellow]Answer[/yellow]", choices=["yes", "no"])
        elif question.type == QuestionType.CHOICE:
            answer = Prompt.ask(
                "[yellow]Answer[/yellow]",
                choices=question.choices,
                default=question.choices[0] if question.choices else None
            )
        else:  # OPEN
            answer = typer.prompt("Answer")

        # Record answer
        state.operator_answers[question.id] = answer
        state.path_taken.append(question.id)

        # Process answer and get next step
        next_id, next_q, fix, escalation_msg = engine.process_answer(rule_id, question.id, answer)

        if escalation_msg:
            console.print(f"\n[yellow]⚠ {escalation_msg}[/yellow]")
            state.status = "escalated"
            break

        # Handle next step
        if next_q:  # Next question
            state.current_question_id = next_q.id
            continue
        elif fix:  # Resolution reached
            display_fix(rule_id, next_id, fix)
            state.status = "completed"
            state.final_fix_id = next_id

            # Ask about new findings
            if ask_for_new_learning(rule_id, fix):
                break
            
            break
        else:
            console.print("[red]✗ Unexpected state[/red]")
            break

    # End session
    console.print("\n[bold cyan]─── Session Complete ───[/bold cyan]\n")
    console.print(f"Status: [cyan]{state.status}[/cyan]")
    console.print(f"Rule: [cyan]{rule_id}[/cyan]")
    console.print(f"Questions asked: {len(state.path_taken)}")
    
    # Optionally save session
    if state.status in ("completed", "escalated"):
        save_session(state)


def display_fix(rule_id: str, fix_id: str, fix):
    """Display a resolution/fix to the operator."""
    console.print("\n")
    console.print(Panel(
        f"[bold green]{fix.title}[/bold green]\n\n" + 
        "\n".join(f"[cyan]→[/cyan] {step}" for step in fix.steps),
        border_style="green",
        title="[bold]Resolution[/bold]"
    ))
    console.print(f"\nConfidence: [yellow]{int(fix.confidence * 100)}%[/yellow]")
    if fix.preventive:
        console.print(f"[bold yellow]⚠ Preventive action needed:[/bold yellow] {fix.preventive}")


def ask_for_new_learning(rule_id: str, fix) -> bool:
    """Ask if operator has new findings to teach Bubba."""
    console.print("\n[bold cyan]Did this fix work?[/bold cyan]")
    
    if not Confirm.ask("Did the issue resolve?", default=True):
        console.print("\n[yellow]Capture what you found instead:[/yellow]")
        finding = typer.prompt("What did you actually discover?")
        new_fix_title = typer.prompt("What did you do to fix it?")
        new_steps = []
        console.print("Enter fix steps (empty line to finish):")
        while True:
            step = typer.prompt("  Step", default="")
            if not step:
                break
            new_steps.append(step)
        
        confidence = typer.prompt(
            "How confident are you in this fix?",
            type=float,
            default=0.70
        )

        # Create learned rule
        learned = engine.suggest_learned_rule(
            rule_id,
            finding,
            new_fix_title,
            new_steps,
            confidence
        )

        console.print("\n[green]✓ New rule captured:[/green]")
        console.print(f"  ID: [cyan]{learned.rule_id}[/cyan]")
        console.print(f"  Name: [cyan]{learned.name}[/cyan]")

        # Save to file
        save_learned_rule(learned)
        
        return True
    else:
        console.print("[green]✓ Great! Glad it's fixed.[/green]")
        return False


def save_session(state: ConversationState):
    """Save session state for audit/replay."""
    log_dir = Path("data/sessions")
    log_dir.mkdir(exist_ok=True)
    
    session_file = log_dir / f"{state.session_id.replace(':', '-')}.json"
    with open(session_file, "w") as f:
        json.dump(state.dict(), f, indent=2)
    
    console.print(f"[dim]Session saved: {session_file}[/dim]")


def save_learned_rule(learned: LearnedRule):
    """Save a user-learned rule to the rules file."""
    rules_file = Path("data/rdr_rules.json")
    
    # Load existing rules
    with open(rules_file) as f:
        rules = json.load(f)
    
    # Append new rule
    rules.append(learned.dict())
    
    # Save back
    with open(rules_file, "w") as f:
        json.dump(rules, f, indent=2)
    
    console.print(f"[dim]Rule saved: {learned.rule_id}[/dim]")


@app.command()
def interactive():
    """Interactive mode: let operator choose a rule or search."""
    init_engine()
    
    console.print("\n[bold cyan]Welcome to Bubba[/bold cyan]")
    console.print("[dim]Your AI troubleshooting assistant[/dim]\n")

    while True:
        console.print("[bold]What would you like to do?[/bold]")
        action = typer.prompt(
            "",
            type=click.Choice(["search", "list", "troubleshoot", "quit"]),
            default="list"
        )

        if action == "quit":
            console.print("[yellow]Goodbye![/yellow]")
            break
        elif action == "list":
            list_rules()
        elif action == "search":
            keywords = typer.prompt("Enter keywords")
            search(keywords)
        elif action == "troubleshoot":
            rule_id = typer.prompt("Enter rule ID")
            troubleshoot(rule_id)


if __name__ == "__main__":
    app()
