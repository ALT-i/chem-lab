"""
Dynamic grading and evaluation engine for student measurements and lab telemetry.
Evaluates precision adherence and target adherence across experiment steps.
"""

from typing import Any, Dict, List, Optional, Tuple, Union


def evaluate_measurement_step(
    measured_volume: float,
    target_volume: Optional[float] = None,
    precision: Optional[float] = None,
    tolerance: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Evaluates a single measurement against target volume, tolerance, and instrument precision.

    Returns:
        dict with:
            - target_adherence: score 0-100
            - precision_adherence: score 0-100
            - step_grade: combined weighted score 0-100
            - difference: measured - target
            - is_within_tolerance: bool
            - feedback: human-readable evaluation summary
    """
    if target_volume is None or target_volume <= 0:
        # Step has no specific volume target (e.g. qualitative step)
        return {
            'target_adherence': 100.0,
            'precision_adherence': 100.0,
            'step_grade': 100.0,
            'difference': 0.0,
            'is_within_tolerance': True,
            'feedback': f'Measured {measured_volume:.2f} cm³ (qualitative step).',
        }

    effective_precision = precision if (precision is not None and precision > 0) else 0.5
    effective_tolerance = tolerance if (tolerance is not None and tolerance > 0) else effective_precision

    diff = measured_volume - target_volume
    abs_diff = abs(diff)
    is_within_tolerance = abs_diff <= (effective_tolerance + 1e-6)

    # 1. Target Adherence Score (0 - 100)
    if effective_tolerance > 0:
        ratio = abs_diff / effective_tolerance
        if ratio <= 1.0:
            # Within tolerance: 80% to 100%
            target_score = 100.0 - (ratio * 20.0)
        else:
            # Beyond tolerance: penalty drops score from 80% down to 0%
            target_score = max(0.0, 80.0 - ((ratio - 1.0) * 40.0))
    else:
        rel_error = abs_diff / target_volume if target_volume > 0 else 0
        target_score = max(0.0, 100.0 * (1.0 - rel_error))

    # 2. Precision Adherence Score (0 - 100)
    # Rewards measuring within the instrument's reading error bounds
    if effective_precision > 0:
        prec_ratio = abs_diff / effective_precision
        if prec_ratio <= 1.0:
            precision_score = 100.0 - (prec_ratio * 15.0)
        elif is_within_tolerance:
            # Within tolerance but slightly beyond single reading error: gentle drop
            precision_score = max(60.0, 85.0 - ((prec_ratio - 1.0) * 15.0))
        else:
            precision_score = max(0.0, 60.0 - ((prec_ratio - 1.0) * 25.0))
    else:
        precision_score = target_score

    # Combined Step Grade: 70% Target Adherence, 30% Precision Adherence
    step_grade = round(0.7 * target_score + 0.3 * precision_score, 1)

    feedback = (
        f"Measured {measured_volume:.2f} cm³ vs target {target_volume:.2f} cm³ "
        f"(diff: {diff:+.2f} cm³, tol: ±{effective_tolerance:.2f}, score: {step_grade}%)."
    )

    return {
        'target_adherence': round(target_score, 1),
        'precision_adherence': round(precision_score, 1),
        'step_grade': step_grade,
        'difference': round(diff, 4),
        'is_within_tolerance': is_within_tolerance,
        'feedback': feedback,
    }


def calculate_session_grade(
    measurements: Union[List[Dict[str, Any]], Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Evaluates dynamic grade across all session measurements / telemetry.

    Supports:
        - List of measurement dicts
        - Dict with 'measurements', 'steps', or 'readings' key
    """
    if isinstance(measurements, dict):
        # Extract list from wrapper dictionary if present
        records = (
            measurements.get('measurements')
            or measurements.get('steps')
            or measurements.get('readings')
            or []
        )
    elif isinstance(measurements, list):
        records = measurements
    else:
        records = []

    if not records:
        # Default baseline grade for completed session with no measurements recorded
        return {
            'overall_grade': 100.0,
            'average_target_adherence': 100.0,
            'average_precision_adherence': 100.0,
            'step_evaluations': [],
            'feedback': 'Completed experiment without volume measurement requirements.',
        }

    step_evals = []
    for idx, record in enumerate(records):
        if not isinstance(record, dict):
            continue

        measured = record.get('measured_volume')
        if measured is None:
            measured = record.get('measuredVolume')
        if measured is None:
            measured = record.get('recordedVolume')
        if measured is None:
            measured = record.get('volume')
        if measured is None:
            measured = record.get('inputVolume')
        if measured is None:
            continue

        try:
            measured = float(measured)
        except (ValueError, TypeError):
            continue

        target = record.get('target_volume')
        if target is None:
            target = record.get('targetVolume')
        if target is None:
            target = record.get('recommendedVolume')
        if target is not None:
            try:
                target = float(target)
            except (ValueError, TypeError):
                target = None

        precision = record.get('precision')
        if precision is not None:
            try:
                precision = float(precision)
            except (ValueError, TypeError):
                precision = None

        tolerance = record.get('tolerance')
        if tolerance is not None:
            try:
                tolerance = float(tolerance)
            except (ValueError, TypeError):
                tolerance = None

        eval_res = evaluate_measurement_step(
            measured_volume=measured,
            target_volume=target,
            precision=precision,
            tolerance=tolerance,
        )
        eval_res['step_index'] = record.get('stepIndex', record.get('step_index', idx))
        step_evals.append(eval_res)

    if not step_evals:
        return {
            'overall_grade': 100.0,
            'average_target_adherence': 100.0,
            'average_precision_adherence': 100.0,
            'step_evaluations': [],
            'feedback': 'Completed experiment.',
        }

    avg_target = sum(e['target_adherence'] for e in step_evals) / len(step_evals)
    avg_precision = sum(e['precision_adherence'] for e in step_evals) / len(step_evals)
    overall_grade = sum(e['step_grade'] for e in step_evals) / len(step_evals)
    overall_grade = round(overall_grade, 1)

    step_feedback_parts = [e['feedback'] for e in step_evals]
    summary_feedback = (
        f"Dynamic Grade: {overall_grade}% (Accuracy: {avg_target:.1f}%, Precision: {avg_precision:.1f}%). "
        + " | ".join(step_feedback_parts)
    )

    return {
        'overall_grade': overall_grade,
        'average_target_adherence': round(avg_target, 1),
        'average_precision_adherence': round(avg_precision, 1),
        'step_evaluations': step_evals,
        'feedback': summary_feedback,
    }
