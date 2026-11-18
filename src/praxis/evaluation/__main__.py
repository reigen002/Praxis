import argparse
import json
from pathlib import Path
import sys
from . import load_suite, run_suite, select_cases, compare_reports, markdown
from .suite import ROOT


def main():
    parser = argparse.ArgumentParser(description='Praxis deterministic evaluation; offline by default')
    parser.add_argument('--suite', type=Path, default=ROOT / 'data/evaluation/v1/suite.json')
    parser.add_argument('--mode', choices=['offline', 'live'], default='offline')
    parser.add_argument('--allow-live', action='store_true')
    parser.add_argument('--case', action='append', dest='case_ids')
    parser.add_argument('--max-live-cases', type=int, default=1)
    parser.add_argument('--timeout', type=int, default=150)
    parser.add_argument('--output', type=Path, default=Path('artifacts/evaluation/latest'))
    parser.add_argument('--compare', type=Path)
    parser.add_argument('--worker', nargs=2, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.worker:
        if not args.allow_live:
            parser.error('Live worker requires --allow-live')
        from .live import worker
        worker(*args.worker)
        return 0
    if args.mode == 'live' and not args.allow_live:
        parser.error('Live mode requires --allow-live; may consume provider quota')
    if args.mode == 'live' and (not args.case_ids or not 1 <= args.max_live_cases <= 5 or not 5 <= args.timeout <= 180):
        parser.error('Live mode requires named --case, --max-live-cases in 1..5 and --timeout in 5..180')
    try:
        suite = load_suite(args.suite)
        if args.mode == 'live':
            from .live import run_live
            report = run_live(suite, select_cases(suite, args.case_ids), args.timeout, args.max_live_cases)
        else:
            report = run_suite(suite, args.case_ids)
        if args.compare:
            report['comparison'] = compare_reports(json.loads(args.compare.read_text(encoding='utf-8')), report)
            if report['comparison']['new_failures']:
                report['gate_passed'] = False
        path = args.output.with_suffix('.json')
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False), encoding='utf-8')
        args.output.with_suffix('.md').write_text(markdown(report), encoding='utf-8')
        print(f"{'PASS' if report['gate_passed'] else 'FAIL'}: {report['summary']['case_success']['numerator']}/{len(report['cases'])} cases; {path}")
        return 130 if report.get('interrupted') else (0 if report['gate_passed'] else 1)
    except (ValueError, OSError):
        # Never print arbitrary exception bodies, including provider responses.
        print('Evaluation configuration/report error. Check fixture hashes, labels, case selection and comparison compatibility.', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
