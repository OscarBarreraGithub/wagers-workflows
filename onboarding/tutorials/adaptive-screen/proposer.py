"""Observed-data-only selection: no evaluator import or hidden outcome input."""
import random

import numpy as np
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF

from contract import (IDENTITY, MAX_BATCH, MAX_ROUND, csv_bytes, encoded,
                      load_state, records, require, save_state)

LENGTH_SCALE = 0.45
ALPHA = 0.01  # fixed assumed observation variance (std=0.1), not inferred
BETA = 1.5
MODEL = {'class': 'sklearn.gaussian_process.GaussianProcessRegressor',
         'kernel': 'RBF(length_scale=0.45, length_scale_bounds="fixed")',
         'alpha': ALPHA, 'optimizer': None, 'normalize_y': False,
         'beta': BETA, 'score': 'mean + beta * std',
         'batch_rule': 'top scores from one fit, no fantasy updates/diversity penalty'}


def model():
    return GaussianProcessRegressor(kernel=RBF(LENGTH_SCALE, length_scale_bounds='fixed'),
                                    alpha=ALPHA, optimizer=None, normalize_y=False)


def predictions(state):
    """Only candidate features/status and the observed ledger enter the GP."""
    lookup = {r['target_id']: r for r in state['candidates']}
    measured = {r['target_id'] for r in state['observed']}
    pending = {r['target_id'] for r in state['pending']}
    eligible = sorted((r for r in state['candidates'] if r['status'] == 'valid' and
                       r['target_id'] not in measured | pending), key=lambda r: r['target_id'])
    x = [[lookup[r['target_id']]['f1'], lookup[r['target_id']]['f2']] for r in state['observed']]
    y = [r['value'] for r in state['observed']]
    gp = model().fit(np.asarray(x), np.asarray(y))
    mean, std = gp.predict(np.asarray([[r['f1'], r['f2']] for r in eligible]), return_std=True)
    return [dict(target_id=r['target_id'], mean=float(m), std=float(s), score=float(m+BETA*s))
            for r, m, s in zip(eligible, mean, std)]


def propose(state_path, out, batch=4, strategy='adaptive'):
    state = load_state(state_path)
    require(not state['pending'], 'Pending batch exists: import it first')
    require(state['round'] < MAX_ROUND, 'Three-round budget exhausted')
    require(type(batch) is int and 1 <= batch <= MAX_BATCH, 'Batch must be 1..4')
    require(strategy in ('adaptive', 'random'), 'Unknown selection strategy')
    scores = predictions(state)
    require(len(scores) >= batch, 'Insufficient eligible targets')
    ranking = sorted(scores, key=lambda r: (-r['score'], r['target_id']))
    next_round = state['round'] + 1
    if strategy == 'random':
        ranking = sorted(scores, key=lambda r: r['target_id'])
        random.Random(state['seed'] + next_round).shuffle(ranking)
    pending = []
    for row in ranking[:batch]:
        target = row['target_id']
        pending.append(dict(target_id=target, sample_id=f'S-{target}-r{next_round:03}',
                            round_id=f'r{next_round:03}', outcome_id=f'O-{target}-r{next_round:03}'))
    records([{k: r[k] for k in IDENTITY} for r in state['observed']] + pending, state['candidates'], True)
    state['pending'] = pending
    state['round'] = next_round
    state['event'] = 'propose'
    save_state(state, out, state_path, {
        'proposal.csv': csv_bytes(IDENTITY, pending),
        'scores.csv': csv_bytes(['target_id', 'mean', 'std', 'score'], scores),
        'fit.json': encoded({**MODEL, 'strategy': strategy, 'seed': state['seed'],
                             'random_round_seed': state['seed'] + next_round,
                             'n_observed': len(state['observed'])})})
