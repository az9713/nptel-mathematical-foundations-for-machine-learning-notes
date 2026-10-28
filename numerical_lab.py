"""Reproduce five small mathematical constructions; NumPy is required."""
from math import comb, erfc, isclose, sqrt

import numpy as np


def identifiability():
    x = np.array([[1., 2.], [2., 4.], [3., 6.]])
    y = np.array([1., 2., 3.])
    first = np.array([1., 0.])
    second = np.array([-1., 1.])
    minimum_norm, _, rank, _ = np.linalg.lstsq(x, y, rcond=None)
    assert np.allclose(x @ first, y)
    assert np.allclose(x @ second, y)
    assert np.allclose(minimum_norm, [.2, .4])
    assert rank == 1
    assert np.linalg.norm(minimum_norm) < np.linalg.norm(first)
    new_input = np.array([1., 3.])
    predictions = [float(new_input @ w) for w in (first, second)]
    assert predictions == [1., 2.]
    return {'rank': int(rank), 'minimum_norm': minimum_norm.tolist(),
            'new_input_predictions': predictions}


def variance_and_prediction():
    x = np.array([[-10., -1.], [-10., 1.],
                  [10., -1.], [10., 1.]])
    centered = x - x.mean(axis=0)
    _, singular, vt = np.linalg.svd(centered, full_matrices=False)
    top = vt[0]
    scores = centered @ top
    reconstructed = np.outer(scores, top)
    error = float(np.sum((centered - reconstructed) ** 2))
    assert isclose(error, 4.)
    assert np.allclose(np.abs(top), [1., 0.])
    # Each retained score corresponds to both possible labels.
    for score in np.unique(scores):
        assert sorted(centered[scores == score, 1]) == [-1., 1.]
    explained = float(singular[0] ** 2 / np.sum(singular ** 2))
    assert isclose(explained, 100 / 101)
    return {'variance_fraction': explained,
            'squared_reconstruction_error': error,
            'best_training_accuracy_from_top_score': .5,
            'training_accuracy_from_discarded_coordinate': 1.}


def concentration():
    n = 20
    exact = sum(comb(n, k) for k in range(n + 1)
                if abs(k - 10) >= 6) / 2 ** n
    chebyshev = .25 / n / .3 ** 2
    # The binomial count has mean 10 and standard deviation sqrt(5).
    # Continuity correction starts at 15.5 or ends at 4.5.
    normal = erfc(5.5 / sqrt(5) / sqrt(2))
    assert exact <= chebyshev
    assert isclose(exact, 6196 / 524288)
    return {'exact_binomial_tail': exact,
            'chebyshev_upper_bound': chebyshev,
            'normal_approximation_with_continuity_correction': normal}


def matrix_gradient():
    x = np.array([[1., 2.], [-1., 1.], [0., 1.]])
    w = np.array([[.2, -.1], [.4, .3]])
    y = np.array([[1., 0.], [0., 1.], [1., 1.]])
    direction = np.array([[.3, -.5], [.7, .2]])

    def objective(value):
        return .5 * np.sum((x @ value - y) ** 2)

    gradient = x.T @ (x @ w - y)
    analytic = float(np.sum(gradient * direction))
    epsilon = 1e-5
    finite_difference = float((objective(w + epsilon * direction)
                               - objective(w - epsilon * direction))
                              / (2 * epsilon))
    assert isclose(analytic, finite_difference, rel_tol=1e-8, abs_tol=1e-8)
    return {'directional_derivative': analytic,
            'central_difference': finite_difference,
            'absolute_discrepancy': abs(analytic - finite_difference)}


def stable_steps():
    hessian = np.diag([1., 10.])
    outcomes = {}
    for rate in (.1, .25):
        value = np.ones(2)
        for _ in range(20):
            value -= rate * (hessian @ value)
        exact = (1 - rate * np.diag(hessian)) ** 20
        assert np.allclose(value, exact)
        outcomes[str(rate)] = float(np.linalg.norm(value))
    assert outcomes['0.1'] < 1
    assert outcomes['0.25'] > 1000
    return outcomes


def run():
    return {'identifiability': identifiability(),
            'variance_and_prediction': variance_and_prediction(),
            'concentration': concentration(),
            'matrix_gradient': matrix_gradient(),
            'gradient_step_norms_after_20_updates': stable_steps()}


if __name__ == '__main__':
    import json
    print(json.dumps(run(), indent=2))
