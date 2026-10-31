import argparse
import json
from pathlib import Path
from praxis.config import settings
from praxis.data import load_dataset, DEMO_DATASETS
from praxis.decisions import RulesProvider
from praxis.tools import BusinessTools


def main():
    parser = argparse.ArgumentParser(description='Praxis verification and live briefing')
    parser.add_argument('command', choices=['check', 'evaluate', 'brief'])
    parser.add_argument('--question', default='Prepare my founder briefing for today. What are the three most important issues, and why?')
    parser.add_argument('--output', default='artifacts/live-briefing.json')
    parser.add_argument('--dataset', choices=list(DEMO_DATASETS), default='yfs')
    args = parser.parse_args()
    config = settings()
    data = load_dataset(DEMO_DATASETS[args.dataset])
    tools = BusinessTools(data)
    if args.command == 'check':
        from importlib.metadata import version
        import platform
        print(json.dumps(dict(python=platform.python_version(), dependencies={p: version(p) for p in
            ['crewai','streamlit','pydantic','pytest','httpx']}, records=len(data.records), reference_date=str(data.reference_date),
            model=config.model, credentials_present=config.ready, live_verified=False), indent=2))
        print(tools.calculate_business_metrics().model_dump_json(indent=2))
    elif args.command == 'evaluate':
        fixture = json.loads(Path('data/synthetic/yfs_evaluation.json' if args.dataset == 'yfs'
            else 'data/synthetic/evaluation.json').read_text())
        provider = RulesProvider(tools)
        results = [(label, provider.evaluate(tools.by_id[label['record_id']])) for label in fixture]
        print(json.dumps(dict(provider='rules-v1', cases=len(results),
            category_correct=sum(d.classification == l['classification'] for l,d in results),
            urgency_correct=sum(d.urgency == l['urgency'] for l,d in results),
            human_review_count=sum(d.classification == 'Human Review' for _,d in results),
            disagreements=[l['record_id'] for l,d in results if d.classification != l['classification'] or d.urgency != l['urgency']],
            jev='not evaluated by this offline command; optional one-record live adapter available', limitation='Tiny synthetic fixture; rules informed label design. Not an independent benchmark.'), indent=2))
    else:
        from praxis.services.briefing import run_briefing, BriefingFailed
        try:
            result = run_briefing(args.question, data, config)
        except BriefingFailed as exc:
            print(str(exc))
            raise SystemExit(1) from None
        path = Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(result.model_dump_json(indent=2), encoding='utf-8')
        print(f'Accepted live briefing saved to {path}')


if __name__ == '__main__':
    main()
