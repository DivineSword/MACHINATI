import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi import HTTPException
from pydantic import ValidationError

from app import db
from app.routes import machines


class MachineListingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_patch = patch.object(db, "DB_PATH", str(Path(self.tmp.name) / "test.db"))
        self.db_patch.start()
        db.init_db()

    def tearDown(self):
        self.db_patch.stop()
        self.tmp.cleanup()

    def test_create_and_list_machine_listing(self):
        created = machines.create_machine(machines.MachineCreate(
            name="  Tractor  ", machine_type="  tractor  ", location="  Safi  ", hourly_rate=120,
            owner_type='partner', reserved_for_own_use=True,
            available_from='2026-11-05', available_to='2026-11-20',
            compatibility_notes='  Needs an operator  ',
        ))

        self.assertEqual(created["name"], "Tractor")
        self.assertEqual(created["machine_type"], "tractor")
        self.assertEqual(created["location"], "Safi")
        self.assertEqual(created["available"], 1)
        self.assertEqual(created['owner_type'], 'partner')
        self.assertEqual(created['reserved_for_own_use'], 1)
        self.assertEqual(created['available_from'], '2026-11-05')
        self.assertEqual(created['available_to'], '2026-11-20')
        self.assertEqual(created['compatibility_notes'], 'Needs an operator')
        self.assertEqual(machines.machines(), [created])

    def test_update_listing_fields_and_availability(self):
        created = machines.create_machine(machines.MachineCreate(
            name="Tractor", machine_type="tractor"
        ))

        updated = machines.update_machine(
            created["id"], machines.MachineUpdate(
                available=False, hourly_rate=0, owner_type='partner',
                reserved_for_own_use=True, available_from='2026-11-10',
                available_to='2026-11-22', compatibility_notes='Low clearance',
            )
        )

        self.assertEqual(updated["available"], 0)
        self.assertEqual(updated["hourly_rate"], 0)
        self.assertEqual(updated["name"], "Tractor")
        self.assertEqual(updated['owner_type'], 'partner')
        self.assertEqual(updated['reserved_for_own_use'], 1)
        self.assertEqual(updated['available_from'], '2026-11-10')
        self.assertEqual(updated['compatibility_notes'], 'Low clearance')

    def test_invalid_listing_and_missing_update(self):
        with self.assertRaises(ValidationError):
            machines.MachineCreate(name=" ", machine_type="tractor", hourly_rate=-1)
        with self.assertRaises(ValidationError):
            machines.MachineCreate(
                name='Tractor', machine_type='tractor', owner_type='unknown'
            )
        with self.assertRaises(ValidationError):
            machines.MachineCreate(
                name='Tractor', machine_type='tractor',
                available_from='2026-11-20', available_to='2026-11-05',
            )
        with self.assertRaises(HTTPException) as caught:
            machines.update_machine(999, machines.MachineUpdate(available=False))
        self.assertEqual(caught.exception.status_code, 404)

    def test_patch_cannot_invert_existing_availability_window(self):
        created = machines.create_machine(machines.MachineCreate(
            name='Tractor', machine_type='tractor',
            available_from='2026-11-05', available_to='2026-11-20',
        ))

        with self.assertRaises(HTTPException) as caught:
            machines.update_machine(created['id'], machines.MachineUpdate(available_from='2026-11-25'))
        self.assertEqual(caught.exception.status_code, 422)

    def test_init_migrates_existing_machine_rows_with_safe_defaults(self):
        with db.connect() as con:
            con.execute('DROP TABLE machines')
            con.execute('''CREATE TABLE machines (
                id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
                machine_type TEXT NOT NULL, location TEXT, hourly_rate REAL,
                available INTEGER NOT NULL DEFAULT 1
            )''')
            con.execute(
                "INSERT INTO machines(name,machine_type,location) VALUES ('Old tractor','tractor','Safi')"
            )

        db.init_db()
        db.init_db()
        row = machines.machines()[0]

        self.assertEqual(row['name'], 'Old tractor')
        self.assertEqual(row['owner_type'], 'company')
        self.assertEqual(row['reserved_for_own_use'], 0)
        self.assertIsNone(row['available_from'])
        self.assertIsNone(row['compatibility_notes'])


if __name__ == "__main__":
    unittest.main()