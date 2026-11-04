import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from fastapi import HTTPException
import httpx

from app import config, db, main
from app.priority import machine_compatibility_for, priority_for
from app.routes.requests import UrgencyVerification, list_requests, verify_urgency


class PriorityTests(unittest.TestCase):
    def test_explicit_and_verified_urgency_outweigh_normal_request(self):
        now = datetime(2026, 11, 4)
        created = '2026-11-04 00:00:00'
        normal_score, _ = priority_for({'urgency_level': 'normal'}, created, now)
        urgent_score, _ = priority_for({'urgency_level': 'urgent'}, created, now)
        critical_score, _ = priority_for(
            {'urgency_level': 'critical', 'verified_by': 'reviewer'}, created, now
        )

        self.assertGreater(urgent_score, normal_score)
        self.assertGreater(critical_score, urgent_score)

    def test_unverified_urgency_has_no_verification_bonus(self):
        created = '2026-11-04 00:00:00'
        unverified, _ = priority_for({'urgency_level': 'urgent'}, created, datetime(2026, 11, 4))
        verified, reason = priority_for(
            {'urgency_level': 'urgent', 'verified_by': 'reviewer'}, created, datetime(2026, 11, 4)
        )

        self.assertEqual(verified - unverified, 10)
        self.assertIn('validée', reason)

    def test_machine_fit_requires_availability_type_and_locality(self):
        machines = [
            {'id': 1, 'name': 'Local tractor', 'machine_type': ' Tractor ', 'location': 'Safi', 'available': 1},
            {'id': 2, 'name': 'Remote tractor', 'machine_type': 'tractor', 'location': 'Meknes', 'available': 1},
            {'id': 3, 'name': 'Unavailable local tractor', 'machine_type': 'tractor', 'location': 'Safi', 'available': 0},
            {'id': 4, 'name': 'Local trailer', 'machine_type': 'transport', 'location': 'Safi', 'available': 1},
            {'id': 5, 'name': 'Unavailable irrigation pump', 'machine_type': 'irrigation', 'location': 'Safi', 'available': 0},
        ]

        fit, _, matches = machine_compatibility_for({'machine_type': 'tractor', 'location': 'safi'}, machines)
        remote_fit, _, remote_matches = machine_compatibility_for(
            {'machine_type': 'tractor', 'location': 'Fes'}, machines
        )
        missing_fit, _, no_matches = machine_compatibility_for(
            {'machine_type': 'irrigation', 'location': 'Safi'}, machines
        )

        self.assertEqual(fit, 'match')
        self.assertEqual([machine['id'] for machine in matches], [1])
        self.assertEqual(remote_fit, 'transport_review')
        self.assertEqual({machine['id'] for machine in remote_matches}, {1, 2})
        self.assertEqual(missing_fit, 'unavailable')
        self.assertEqual(no_matches, [])

    def test_reserved_machines_and_non_overlapping_dates_are_excluded(self):
        machines = [
            {'id': 1, 'machine_type': 'tractor', 'location': 'Safi', 'available': 1,
             'reserved_for_own_use': 0, 'available_from': '2026-11-01', 'available_to': '2026-11-20'},
            {'id': 2, 'machine_type': 'tractor', 'location': 'Safi', 'available': 1,
             'reserved_for_own_use': 1},
        ]

        fit, _, matches = machine_compatibility_for(
            {'machine_type': 'tractor', 'location': 'Safi', 'preferred_date': '2026-11-15'}, machines
        )
        outside_window, _, no_matches = machine_compatibility_for(
            {'machine_type': 'tractor', 'location': 'Safi', 'preferred_date': '2026-11-25'}, machines
        )
        date_review, _, review_matches = machine_compatibility_for(
            {'machine_type': 'tractor', 'location': 'Safi'}, machines[:1]
        )

        self.assertEqual(fit, 'match')
        self.assertEqual([machine['id'] for machine in matches], [1])
        self.assertEqual(outside_window, 'unavailable')
        self.assertEqual(no_matches, [])
        self.assertEqual(date_review, 'date_review')
        self.assertEqual([machine['id'] for machine in review_matches], [1])

    def test_local_machine_fit_improves_priority_above_unchecked_transport(self):
        created = '2026-11-04 00:00:00'
        now = datetime(2026, 11, 4)
        local, _ = priority_for({'urgency_level': 'normal'}, created, now, machine_fit='match')
        transport_review, _ = priority_for(
            {'urgency_level': 'normal'}, created, now, machine_fit='transport_review'
        )

        self.assertEqual(local - transport_review, 10)


class RequestPriorityApiTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_patch = patch.object(db, 'DB_PATH', str(Path(self.tmp.name) / 'test.db'))
        self.db_patch.start()
        db.init_db()

    def tearDown(self):
        self.db_patch.stop()
        self.tmp.cleanup()

    def insert_request(self, phone, urgency, status='pending_review'):
        payload = {'machine_type': 'tractor', 'urgency_level': urgency}
        with db.connect() as con:
            cursor = con.execute(
                'INSERT INTO requests(farmer_phone,payload,status) VALUES (?,?,?)',
                (phone, json.dumps(payload), status),
            )
        return cursor.lastrowid

    def test_api_sorts_by_score_and_human_verification_changes_score(self):
        with db.connect() as con:
            con.execute(
                'INSERT INTO machines(name,machine_type,location,available) VALUES (?,?,?,?)',
                ('Local tractor', 'tractor', 'Safi', 1),
            )
        normal_id = self.insert_request('normal-farmer', 'normal')
        urgent_id = self.insert_request('urgent-farmer', 'urgent')

        self.assertEqual([row['id'] for row in list_requests()], [urgent_id, normal_id])
        result = verify_urgency(urgent_id, UrgencyVerification(reviewer=' Cooperative reviewer '))
        ranked = list_requests()

        self.assertEqual(result['verified_by'], 'Cooperative reviewer')
        self.assertEqual(ranked[0]['payload']['verified_by'], 'Cooperative reviewer')
        self.assertIn('priority_score', ranked[0])
        self.assertEqual(ranked[0]['machine_fit'], 'transport_review')
        self.assertEqual(ranked[1]['machine_fit'], 'transport_review')

    def test_verification_rejects_normal_and_non_pending_requests(self):
        normal_id = self.insert_request('normal-farmer', 'normal')
        approved_id = self.insert_request('approved-farmer', 'urgent', 'approved')

        with self.assertRaises(HTTPException) as normal:
            verify_urgency(normal_id, UrgencyVerification(reviewer='reviewer'))
        with self.assertRaises(HTTPException) as approved:
            verify_urgency(approved_id, UrgencyVerification(reviewer='reviewer'))
        self.assertEqual(normal.exception.status_code, 409)
        self.assertEqual(approved.exception.status_code, 409)


class PriorityWorkflowTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_patch = patch.object(db, 'DB_PATH', str(Path(self.tmp.name) / 'workflow.db'))
        self.seed_patch = patch.object(config, 'SEED_DEMO_DATA', True)
        self.db_patch.start()
        self.seed_patch.start()

    def tearDown(self):
        self.seed_patch.stop()
        self.db_patch.stop()
        self.tmp.cleanup()

    async def test_seeded_priority_scenario_through_http_review_workflow(self):
        async with main.app.router.lifespan_context(main.app):
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=main.app), base_url='http://testserver'
            ) as client:
                response = await client.get('/api/requests')
                self.assertEqual(response.status_code, 200)
                requests = response.json()
                urgent, flexible = requests
                self.assertEqual(urgent['farmer_phone'], 'DEMO-PRIORITY-URGENT')
                self.assertEqual(urgent['machine_fit'], 'match')
                self.assertEqual(flexible['farmer_phone'], 'DEMO-PRIORITY-FLEXIBLE')
                self.assertEqual(flexible['machine_fit'], 'transport_review')
                initial_score = urgent['priority_score']

                verification = await client.patch(
                    f"/api/requests/{urgent['id']}/urgency-verification",
                    json={'reviewer': 'Demo reviewer'},
                )
                self.assertEqual(verification.status_code, 200)
                refreshed = (await client.get('/api/requests')).json()[0]
                self.assertEqual(refreshed['payload']['verified_by'], 'Demo reviewer')
                self.assertEqual(refreshed['priority_score'], initial_score + 10)

                approval = await client.patch(
                    f"/api/requests/{urgent['id']}/status", json={'status': 'approved'}
                )
                self.assertEqual(approval.status_code, 200)
                self.assertEqual(approval.json()['status'], 'approved')


if __name__ == '__main__':
    unittest.main()