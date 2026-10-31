from pathlib import Path
from praxis.schemas import Dataset

DEFAULT_DATASET = Path(__file__).resolve().parents[3] / 'data' / 'synthetic' / 'updates.json'
DEMO_DATASETS = {'yfs': DEFAULT_DATASET.parent / 'yfs_operations.json',
    'demo': DEFAULT_DATASET.parent / 'founder_demo.json', 'original': DEFAULT_DATASET}
DATASET_NAMES = {'yfs': 'YFS founder demo', 'demo': 'Startup demo', 'original': 'Original regression'}
YFS_PROFILE = {
    'description': 'Fictional programme operations informed by public Young Founders School programmes; not internal school data.',
    'comparison_question': 'Why is the cohort access issue more urgent than the certificate preview redesign?',
    'comparison_label': 'Cohort vs. redesign',
    'exposure_label': 'Programme agreement exposure',
    'exposure_note': 'Signed agreements linked to unresolved partner issues',
    'pipeline_label': 'Potential partnership pipeline',
    'opportunities_label': 'programme proposals awaiting action',
    'escalations_label': 'school or sponsor issue records',
}


def load_dataset(path: str | Path = DEFAULT_DATASET) -> Dataset:
    return Dataset.model_validate_json(Path(path).read_text(encoding='utf-8'))
