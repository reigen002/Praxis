"""Revalidate existing genuine rehearsal exports. Makes no model/API calls."""
import json
from pathlib import Path

from praxis.data import load_dataset, DEMO_DATASETS
from praxis.schemas import RunResult
from praxis.services.saved_runs import save_run

ROOT = Path(__file__).resolve().parents[1]


def main():
    for name in ('morning', 'explanation'):
        path = ROOT / 'artifacts' / f'react-api-yfs-{name}.json'
        if not path.is_file():
            raise SystemExit(f'Missing actual rehearsal export: {path.name}. Complete a live run in the app first.')
        job = json.loads(path.read_text(encoding='utf-8'))
        if job.get('status') != 'completed' or job.get('dataset') != 'yfs':
            raise SystemExit(f'{path.name} is not a completed school-dataset run.')
        result = RunResult.model_validate(job['result'])
        dataset = load_dataset(DEMO_DATASETS['yfs'])
        save_run(dataset, result, ROOT / 'artifacts' / 'saved-briefings')
        print(f'Prepared {name}: original run {result.run_id}; sources, policy, metrics and agent events revalidated.')
    print('No new provider requests. Open Saved briefings in the school workspace.')


if __name__ == '__main__':
    main()
