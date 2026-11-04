"""Deterministic, demo-only request prioritization."""
from datetime import date, datetime


def _as_date(value):
    try:
        return date.fromisoformat(str(value)) if value else None
    except ValueError:
        return None


def _request_window(payload):
    preferred_date = _as_date(payload.get('preferred_date'))
    if preferred_date:
        return preferred_date, preferred_date, True

    start = _as_date(payload.get('urgent_window_start'))
    end = _as_date(payload.get('urgent_window_end'))
    if start or end:
        return start or date.min, end or date.max, True
    has_date_text = any(payload.get(key) for key in (
        'preferred_date_text', 'urgent_window_start', 'urgent_window_end'
    ))
    return None, None, has_date_text


def machine_compatibility_for(payload, machines):
    machine_type = (payload.get('machine_type') or '').strip().casefold()
    if not machine_type:
        return 'not_specified', 'نوع الماكينة خاصو يتحدد', []

    type_matches = [
        machine for machine in machines
        if (machine.get('machine_type') or '').strip().casefold() == machine_type
    ]
    available_matches = [
        machine for machine in type_matches
        if machine.get('available') is True or machine.get('available') == 1
    ]
    if not available_matches:
        reason = 'ما كايناش ماكينة من هاد النوع متاحة' if type_matches else 'ما كايناش ماكينة من هاد النوع فالمخزون'
        return 'unavailable', reason, []

    available_matches = [
        machine for machine in available_matches
        if machine.get('reserved_for_own_use') is not True and machine.get('reserved_for_own_use') != 1
    ]
    if not available_matches:
        return 'unavailable', 'الماكينات المطابقة محجوزة للاستعمال الشخصي', []

    request_start, request_end, request_has_date = _request_window(payload)
    date_matches = []
    date_review = []
    date_blocked = 0
    for machine in available_matches:
        machine_start = _as_date(machine.get('available_from'))
        machine_end = _as_date(machine.get('available_to'))
        if request_start and request_end:
            if machine_end and request_start > machine_end:
                date_blocked += 1
                continue
            if machine_start and request_end < machine_start:
                date_blocked += 1
                continue
            date_matches.append(machine)
        elif machine_start or machine_end:
            date_review.append(machine)
        else:
            date_matches.append(machine)

    if not date_matches and not date_review:
        if date_blocked:
            return 'unavailable', 'ما كايناش ماكينة متاحة فالفترة المطلوبة', []
        return 'unavailable', 'ما كايناش ماكينة من هاد النوع متاحة', []

    location = (payload.get('location') or '').strip().casefold()
    local_matches = [
        machine for machine in date_matches
        if location and (machine.get('location') or '').strip().casefold() == location
    ]
    if local_matches:
        return 'match', 'ماكينة من نفس النوع متاحة فنفس المنطقة', local_matches
    local_date_review = [
        machine for machine in date_review
        if location and (machine.get('location') or '').strip().casefold() == location
    ]
    if date_review:
        return 'date_review', 'خاص التاريخ يتأكد من بعد قبل اقتراح الماكينة', local_date_review or date_review
    return 'transport_review', 'النوع متاح ولكن خاص التحقق من النقل والمنطقة', date_matches


def priority_for(payload, created_at, now=None, machine_fit='unknown'):
    score = {'normal': 0, 'urgent': 25, 'critical': 40}.get(payload.get('urgency_level'), 0)
    reasons = []
    urgency = payload.get('urgency_level')
    if urgency in ('urgent', 'critical'):
        reasons.append('Urgence déclarée, validation humaine requise')
    elif urgency == 'normal':
        reasons.append('Demande normale ou flexible')

    if payload.get('verified_by'):
        score += 10
        reasons.append('Urgence validée par la coopérative')
    if payload.get('urgent_window_start') and payload.get('urgent_window_end'):
        score += 5
        reasons.append('Fenêtre de disponibilité précisée')
    if machine_fit == 'match':
        score += 15
        reasons.append('Machine du bon type disponible dans la localité')
    elif machine_fit == 'transport_review':
        score += 5
        reasons.append('Machine du bon type disponible, transport à vérifier')

    try:
        created = datetime.fromisoformat(created_at)
        current = now or datetime.now(created.tzinfo)
        age_bonus = max(0, min((current - created).days, 10))
    except (TypeError, ValueError):
        age_bonus = 0
    score += age_bonus
    if age_bonus:
        reasons.append(f'Demande en attente depuis {age_bonus} jour(s)')

    return score, ' · '.join(reasons) or 'Priorité standard'