#!/usr/bin/env python3
"""
Command-line interface for the Executive Board Council.

Run an interactive session where you can present business situations
to a virtual German production company executive board.
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
    print("  EXECUTIVE BOARD COUNCIL - German Production Company (Produktionsunternehmen)")
    print("=" * 80)
    print("\nBoard Members:")
    for role_key, role_config in EXECUTIVE_ROLES.items():
        print(f"  • {role_config['title']}")
    print(f"\nCouncil Speaker Model: {COUNCIL_SPEAKER_MODEL}")
    print("\n" + "-" * 80)


def print_stage1(results):
    """Print Stage 1 results - Individual Perspectives."""
    print("\n" + "=" * 80)
    print("  STAGE 1: Individual Executive Perspectives")
    print("=" * 80)

    for result in results:
        print(f"\n{'─' * 60}")
        print(f"📊 {result['title']} ({result['role']})")
        print(f"   Model: {result['model']}")
        print(f"{'─' * 60}")
        print(result['response'])


def print_stage2(results, aggregate_rankings):
    """Print Stage 2 results - Cross-Evaluations."""
    print("\n" + "=" * 80)
    print("  STAGE 2: Cross-Evaluations")
    print("=" * 80)

    for result in results:
        print(f"\n{'─' * 60}")
        print(f"🔍 Evaluation by {result['title']} ({result['role']})")
        print(f"{'─' * 60}")
        print(result['evaluation'])

    if aggregate_rankings:
        print(f"\n{'─' * 60}")
        print("📈 Aggregate Rankings (based on peer evaluations):")
        print(f"{'─' * 60}")
        for i, ranking in enumerate(aggregate_rankings, 1):
            print(f"  {i}. {ranking['title']} - Average Rank: {ranking['average_rank']:.2f}")


def print_stage3(result):
    """Print Stage 3 results - Council Speaker Synthesis."""
    print("\n" + "=" * 80)
    print("  STAGE 3: Council Speaker's Final Recommendation")
    print("=" * 80)
    print(f"\nModel: {result['model']}")
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
    print("\n⏳ Convening the Executive Board...")
    print("   This may take a minute as we gather perspectives from all executives.\n")

    try:
        stage1_results, stage2_results, stage3_result, metadata = await run_executive_board_meeting(situation)

        if show_all_stages:
            print_stage1(stage1_results)
            print_stage2(stage2_results, metadata.get('aggregate_rankings', []))

        print_stage3(stage3_result)

        return stage1_results, stage2_results, stage3_result, metadata

    except Exception as e:
        print(f"\n❌ Error running executive board meeting: {e}")
        raise


async def interactive_session():
    """Run an interactive CLI session."""
    print_header()

    print("\nPresent a business situation to the Executive Board.")
    print("Type 'quit' or 'exit' to end the session.")
    print("Type 'brief' before your situation for a condensed output (final synthesis only).")
    print("-" * 80)

    while True:
        print("\n📋 Enter your business situation or question:")
        print("   (You can enter multiple lines. Press Enter twice to submit)\n")

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
            print("\n👋 Thank you for using the Executive Board Council. Auf Wiedersehen!")
            break

        # Check for brief mode
        show_all_stages = True
        if situation.lower().startswith('brief '):
            show_all_stages = False
            situation = situation[6:].strip()

        if not situation:
            print("⚠️  Please enter a business situation to discuss.")
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
    print(f"\n📋 Business Situation:\n{situation}")
    await run_meeting(situation, show_all_stages=not brief)


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Executive Board Council - German Production Company Decision Support"
    )
    parser.add_argument(
        '-q', '--query',
        type=str,
        help='Single business situation to discuss (non-interactive mode)'
    )
    parser.add_argument(
        '-b', '--brief',
        action='store_true',
        help='Only show the final synthesis (skip individual perspectives and evaluations)'
    )
    parser.add_argument(
        '-f', '--file',
        type=str,
        help='Read business situation from a file'
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
