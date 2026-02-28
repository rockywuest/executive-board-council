#!/usr/bin/env python3
"""
Kommandozeilenschnittstelle für das Vorstandsgremium.

Starten Sie eine interaktive Sitzung, in der Sie Geschäftssituationen
einem virtuellen deutschen Unternehmensvorstand präsentieren können.
"""

import asyncio
import sys
from typing import Optional

# Add the project root to the path
sys.path.insert(0, '.')

from backend.council import run_executive_board_meeting, EXECUTIVE_ROLES
from backend.config import COUNCIL_SPEAKER_MODEL


def print_header():
    """Print the application header."""
    print("\n" + "=" * 80)
    print("  VORSTANDSGREMIUM - Deutsches Produktionsunternehmen")
    print("=" * 80)
    print("\nVorstandsmitglieder:")
    for role_key, role_config in EXECUTIVE_ROLES.items():
        print(f"  • {role_config['title']}")
    print(f"\nVorstandssprecher-Modell: {COUNCIL_SPEAKER_MODEL}")
    print("\n" + "-" * 80)


def print_stage1(results):
    """Print Stage 1 results - Individual Perspectives."""
    print("\n" + "=" * 80)
    print("  PHASE 1: Individuelle Vorstandsperspektiven")
    print("=" * 80)

    for result in results:
        print(f"\n{'─' * 60}")
        print(f"📊 {result['title']} ({result['role']})")
        print(f"   Modell: {result['model']}")
        print(f"{'─' * 60}")
        print(result['response'])


def print_stage2(results, aggregate_rankings):
    """Print Stage 2 results - Cross-Evaluations."""
    print("\n" + "=" * 80)
    print("  PHASE 2: Gegenseitige Bewertungen")
    print("=" * 80)

    for result in results:
        print(f"\n{'─' * 60}")
        print(f"🔍 Bewertung durch {result['title']} ({result['role']})")
        print(f"{'─' * 60}")
        print(result['evaluation'])

    if aggregate_rankings:
        print(f"\n{'─' * 60}")
        print("📈 Gesamtranking (basierend auf gegenseitigen Bewertungen):")
        print(f"{'─' * 60}")
        for i, ranking in enumerate(aggregate_rankings, 1):
            print(f"  {i}. {ranking['title']} - Durchschnittsrang: {ranking['average_rank']:.2f}")


def print_stage3(result):
    """Print Stage 3 results - Council Speaker Synthesis."""
    print("\n" + "=" * 80)
    print("  PHASE 3: Schlussempfehlung des Vorstandssprechers")
    print("=" * 80)
    print(f"\nModell: {result['model']}")
    print(f"\n{'─' * 60}")
    print(result['response'])
    print(f"{'─' * 60}")


async def run_meeting(situation: str, show_all_stages: bool = True):
    """
    Run an executive board meeting for the given situation.

    Args:
        situation: The business situation to discuss
        show_all_stages: Whether to show all stages or just the final synthesis
    """
    print("\n⏳ Der Vorstand wird einberufen...")
    print("   Dies kann eine Minute dauern, während wir die Perspektiven aller Vorstände sammeln.\n")

    try:
        stage1_results, stage2_results, stage3_result, metadata = await run_executive_board_meeting(situation)

        if show_all_stages:
            print_stage1(stage1_results)
            print_stage2(stage2_results, metadata.get('aggregate_rankings', []))

        print_stage3(stage3_result)

        return stage1_results, stage2_results, stage3_result, metadata

    except Exception as e:
        print(f"\n❌ Fehler bei der Vorstandssitzung: {e}")
        raise


async def interactive_session():
    """Run an interactive CLI session."""
    print_header()

    print("\nPräsentieren Sie eine Geschäftssituation dem Vorstand.")
    print("Geben Sie 'quit' oder 'exit' ein, um die Sitzung zu beenden.")
    print("Geben Sie 'kurz' vor Ihrer Situation ein für eine verkürzte Ausgabe (nur Schlussempfehlung).")
    print("-" * 80)

    while True:
        print("\n📋 Geben Sie Ihre Geschäftssituation oder Frage ein:")
        print("   (Mehrzeilige Eingabe möglich. Drücken Sie zweimal Enter zum Absenden)\n")

        lines = []
        while True:
            try:
                line = input()
                if line == "":
                    if lines:
                        break
                else:
                    lines.append(line)
            except EOFError:
                return

        situation = "\n".join(lines).strip()

        if situation.lower() in ['quit', 'exit']:
            print("\n👋 Vielen Dank für die Nutzung des Vorstandsgremiums. Auf Wiedersehen!")
            break

        # Check for brief mode
        show_all_stages = True
        if situation.lower().startswith('kurz ') or situation.lower().startswith('brief '):
            show_all_stages = False
            if situation.lower().startswith('kurz '):
                situation = situation[5:].strip()
            else:
                situation = situation[6:].strip()

        if not situation:
            print("⚠️  Bitte geben Sie eine Geschäftssituation ein.")
            continue

        await run_meeting(situation, show_all_stages)


async def single_query(situation: str, brief: bool = False):
    """
    Run a single query and exit.

    Args:
        situation: The business situation to discuss
        brief: If True, only show the final synthesis
    """
    print_header()
    print(f"\n📋 Geschäftssituation:\n{situation}")
    await run_meeting(situation, show_all_stages=not brief)


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Vorstandsgremium - Entscheidungsunterstützung für deutsche Unternehmen"
    )
    parser.add_argument(
        '-q', '--query',
        type=str,
        help='Einzelne Geschäftssituation zur Diskussion (nicht-interaktiver Modus)'
    )
    parser.add_argument(
        '-b', '--brief',
        action='store_true',
        help='Nur die Schlussempfehlung anzeigen (einzelne Perspektiven und Bewertungen überspringen)'
    )
    parser.add_argument(
        '-f', '--file',
        type=str,
        help='Geschäftssituation aus einer Datei lesen'
    )

    args = parser.parse_args()

    if args.file:
        with open(args.file, 'r') as f:
            situation = f.read().strip()
        asyncio.run(single_query(situation, args.brief))
    elif args.query:
        asyncio.run(single_query(args.query, args.brief))
    else:
        asyncio.run(interactive_session())


if __name__ == "__main__":
    main()
