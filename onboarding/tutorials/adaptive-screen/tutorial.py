#!/usr/bin/env python3
"""One command interface. Propose/import never import the simulator module."""
import argparse
import json
import sys

from contract import Refusal, import_outcomes, initialize


def main():
    parser = argparse.ArgumentParser(description='Fictional adaptive-screen software tutorial only')
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('generate')
    p.add_argument('--out', required=True)
    p.add_argument('--seed', type=int, default=17)
    p.add_argument('--count', type=int, default=200)
    p = sub.add_parser('init')
    p.add_argument('--candidates', required=True)
    p.add_argument('--outcomes', required=True)
    p.add_argument('--seed', type=int, default=17)
    p.add_argument('--out', required=True)
    p = sub.add_parser('propose')
    p.add_argument('--state', required=True)
    p.add_argument('--out', required=True)
    p.add_argument('--batch', type=int, default=4)
    p.add_argument('--strategy', choices=['adaptive', 'random'], default='adaptive')
    p = sub.add_parser('import')
    p.add_argument('--state', required=True)
    p.add_argument('--outcomes', required=True)
    p.add_argument('--out', required=True)
    p = sub.add_parser('simulate')
    p.add_argument('--state', required=True)
    p.add_argument('--truth', required=True)
    p.add_argument('--out', required=True)
    p = sub.add_parser('evaluate')
    p.add_argument('--adaptive', required=True)
    p.add_argument('--random', required=True)
    p.add_argument('--truth', required=True)
    p.add_argument('--out', required=True)
    p = sub.add_parser('suite')
    p.add_argument('--out', required=True)
    args = parser.parse_args()
    try:
        match args.command:
            case 'generate':
                from simulator import generate
                generate(args.out, args.seed, args.count)
            case 'init':
                initialize(args.candidates, args.outcomes, args.out, args.seed)
            case 'propose':
                from proposer import propose
                propose(args.state, args.out, args.batch, args.strategy)
            case 'import':
                import_outcomes(args.state, args.outcomes, args.out)
            case 'simulate':
                from simulator import measure
                measure(args.state, args.truth, args.out)
            case 'evaluate':
                from simulator import evaluate
                evaluate(args.adaptive, args.random, args.truth, args.out)
            case 'suite':
                from suite import run
                return run(args.out)
    except (Refusal, OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({'status': 'FAIL', 'command': args.command, 'error': str(exc)}))
        return 2
    print(json.dumps({'status': 'PASS', 'command': args.command}))
    return 0


if __name__ == '__main__':
    sys.exit(main())
