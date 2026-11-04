"""Idempotent sample inventory and request data for local demonstrations."""
import json

from .db import connect


LEGACY_DEMO_MACHINE_NAMES = (
    'DEMO - Tracteur Massey Ferguson 240',
    'DEMO - Moissonneuse-batteuse New Holland',
    'DEMO - Motopompe 3 pouces',
    'DEMO - Herse rotative 2,5 m',
    'DEMO - Remorque agricole 5 tonnes',
    'DEMO - Tracteur New Holland TD5',
)

DEMO_MACHINES = (
    ('DEMO - Combine harvester priority simulation', 'combine_harvester', 'Meknes', 1250, 1,
     'company', 0, '2026-11-12', '2026-11-30',
     'Illustrative availability; travel outside Meknes needs review'),
)

DEMO_REQUESTS = (
    ('DEMO-PRIORITY-URGENT', 'pending_review', {
        'intent': 'request_machine', 'machine_type': 'combine_harvester', 'operation': 'harvest',
        'area_hectares': 12, 'location': 'Meknes', 'preferred_date': '2026-11-15',
        'preferred_date_text': None, 'urgency_level': 'critical',
        'urgency_reason': 'Harvest window is approaching',
        'urgent_window_start': '2026-11-12', 'urgent_window_end': '2026-11-17',
        'language': 'fr', 'notes': None,
    }),
    ('DEMO-PRIORITY-FLEXIBLE', 'pending_review', {
        'intent': 'request_machine', 'machine_type': 'combine_harvester', 'operation': 'harvest',
        'area_hectares': 6, 'location': 'Fes', 'preferred_date': '2026-11-25',
        'preferred_date_text': None, 'urgency_level': 'normal', 'urgency_reason': None,
        'urgent_window_start': None, 'urgent_window_end': None,
        'language': 'fr', 'notes': None,
    }),
)


def seed_demo_data():
    with connect() as con:
        legacy_requests = con.execute(
            "SELECT id FROM requests WHERE farmer_phone LIKE 'DEMO-FARMER-%'"
        ).fetchall()
        if legacy_requests:
            ids = [row['id'] for row in legacy_requests]
            placeholders = ','.join('?' for _ in ids)
            con.execute(f'DELETE FROM bookings WHERE request_id IN ({placeholders})', ids)
            con.execute(f'DELETE FROM requests WHERE id IN ({placeholders})', ids)

        placeholders = ','.join('?' for _ in LEGACY_DEMO_MACHINE_NAMES)
        legacy_machines = con.execute(
            f'SELECT id FROM machines WHERE name IN ({placeholders})', LEGACY_DEMO_MACHINE_NAMES
        ).fetchall()
        if legacy_machines:
            ids = [row['id'] for row in legacy_machines]
            placeholders = ','.join('?' for _ in ids)
            con.execute(f'DELETE FROM bookings WHERE machine_id IN ({placeholders})', ids)
            con.execute(f'DELETE FROM machines WHERE id IN ({placeholders})', ids)

        for machine in DEMO_MACHINES:
            con.execute(
                """INSERT INTO machines(
                    name, machine_type, location, hourly_rate, available, owner_type,
                    reserved_for_own_use, available_from, available_to, compatibility_notes
                ) SELECT ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                WHERE NOT EXISTS (SELECT 1 FROM machines WHERE name=?)""",
                (*machine, machine[0]),
            )

        for phone, status, payload in DEMO_REQUESTS:
            data = {
                'urgency_level': 'normal', 'urgency_reason': None,
                'urgent_window_start': None, 'urgent_window_end': None,
                **payload,
            }
            con.execute(
                """INSERT INTO requests(farmer_phone, payload, status)
                SELECT ?, ?, ? WHERE NOT EXISTS (
                    SELECT 1 FROM requests WHERE farmer_phone=?
                )""",
                (phone, json.dumps(data, ensure_ascii=False), status, phone),
            )