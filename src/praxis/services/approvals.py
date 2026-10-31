from typing import Literal
from praxis.schemas import Briefing


def review_draft(state: dict, run_id: str, briefing: Briefing, index: int,
                 decision: Literal['approved', 'rejected']):
    if decision not in ('approved', 'rejected') or not 0 <= index < len(briefing.follow_ups):
        raise ValueError('Invalid review decision or draft')
    state[f'{run_id}:{index}'] = decision
