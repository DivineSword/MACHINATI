import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app import db
from app.demo import DEMO_MACHINES, DEMO_REQUESTS, LEGACY_DEMO_MACHINE_NAMES, seed_demo_data
from app.routes.requests import list_requests


class DemoDataTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_patch = patch.object(db, "DB_PATH", str(Path(self.tmp.name) / "test.db"))
        self.db_patch.start()
        db.init_db()

    def tearDown(self):
        self.db_patch.stop()
        self.tmp.cleanup()

    def test_seed_examples_for_catalogue_and_request_statuses(self):
        seed_demo_data()
        seed_demo_data()

        with db.connect() as con:
            machine_count = con.execute("SELECT count(*) FROM machines").fetchone()[0]
            statuses = {row[0] for row in con.execute(
                "SELECT DISTINCT status FROM requests WHERE farmer_phone LIKE 'DEMO-PRIORITY-%'"
            )}
            request_count = con.execute(
                "SELECT count(*) FROM requests WHERE farmer_phone LIKE 'DEMO-PRIORITY-%'"
            ).fetchone()[0]

        self.assertEqual(machine_count, len(DEMO_MACHINES))
        self.assertEqual(request_count, len(DEMO_REQUESTS))
        self.assertEqual(statuses, {'pending_review'})

        requests = {row['farmer_phone']: row for row in list_requests()}
        urgent = requests['DEMO-PRIORITY-URGENT']
        flexible = requests['DEMO-PRIORITY-FLEXIBLE']
        self.assertGreater(urgent['priority_score'], flexible['priority_score'])
        self.assertEqual(urgent['machine_fit'], 'match')
        self.assertEqual(flexible['machine_fit'], 'transport_review')
        self.assertIsNone(urgent['payload'].get('verified_by'))

    def test_seed_removes_old_demo_rows_but_preserves_user_rows(self):
        with db.connect() as con:
            con.execute(
                'INSERT INTO machines(name,machine_type,location) VALUES (?,?,?)',
                (LEGACY_DEMO_MACHINE_NAMES[0], 'tractor', 'Sefrou'),
            )
            con.execute("INSERT INTO requests(farmer_phone,payload) VALUES ('DEMO-FARMER-01','{}')")
            con.execute("INSERT INTO machines(name,machine_type,location) VALUES ('My tractor','tractor','Fes')")
            con.execute("INSERT INTO requests(farmer_phone,payload) VALUES ('REAL-FARMER','{}')")

        seed_demo_data()

        with db.connect() as con:
            machine_names = {row[0] for row in con.execute('SELECT name FROM machines')}
            farmer_phones = {row[0] for row in con.execute('SELECT farmer_phone FROM requests')}

        self.assertNotIn(LEGACY_DEMO_MACHINE_NAMES[0], machine_names)
        self.assertNotIn('DEMO-FARMER-01', farmer_phones)
        self.assertIn('My tractor', machine_names)
        self.assertIn('REAL-FARMER', farmer_phones)


if __name__ == "__main__":
    unittest.main()