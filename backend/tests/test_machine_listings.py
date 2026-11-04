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
            name="  Tractor  ", machine_type="  tractor  ", location="  Safi  ", hourly_rate=120
        ))

        self.assertEqual(created["name"], "Tractor")
        self.assertEqual(created["machine_type"], "tractor")
        self.assertEqual(created["location"], "Safi")
        self.assertEqual(created["available"], 1)
        self.assertEqual(machines.machines(), [created])

    def test_update_listing_fields_and_availability(self):
        created = machines.create_machine(machines.MachineCreate(
            name="Tractor", machine_type="tractor"
        ))

        updated = machines.update_machine(
            created["id"], machines.MachineUpdate(available=False, hourly_rate=0)
        )

        self.assertEqual(updated["available"], 0)
        self.assertEqual(updated["hourly_rate"], 0)
        self.assertEqual(updated["name"], "Tractor")

    def test_invalid_listing_and_missing_update(self):
        with self.assertRaises(ValidationError):
            machines.MachineCreate(name=" ", machine_type="tractor", hourly_rate=-1)
        with self.assertRaises(HTTPException) as caught:
            machines.update_machine(999, machines.MachineUpdate(available=False))
        self.assertEqual(caught.exception.status_code, 404)


if __name__ == "__main__":
    unittest.main()