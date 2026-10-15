import hashlib
import tempfile
import unittest
from pathlib import Path

import storage


class StorageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test.sqlite3"
        storage.initialize_storage(self.db_path)
        self.user_a = storage.register_user(
            "user_a", "a-very-long-test-password-1", self.db_path
        )
        self.user_b = storage.register_user(
            "user_b", "a-very-long-test-password-2", self.db_path
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def make_pair(self) -> tuple[str, str]:
        room_id, invite_code = storage.create_room(
            self.user_a["user_id"], self.db_path
        )
        joined_room_id = storage.join_room(
            self.user_b["user_id"], invite_code, self.db_path
        )
        self.assertEqual(room_id, joined_room_id)
        return room_id, invite_code

    def consent_both(self, room_id: str) -> None:
        storage.save_summary(
            self.user_a["user_id"], room_id, "A shared summary", True, self.db_path
        )
        storage.save_summary(
            self.user_b["user_id"], room_id, "B shared summary", True, self.db_path
        )

    def test_passwords_are_hashed_and_authenticate(self) -> None:
        self.assertEqual(
            storage.authenticate_user(
                "USER_A", "a-very-long-test-password-1", self.db_path
            ),
            self.user_a,
        )
        self.assertIsNone(
            storage.authenticate_user("user_a", "wrong-password", self.db_path)
        )
        with storage._connect(self.db_path) as connection:
            stored_hash = connection.execute(
                "SELECT password_hash FROM users WHERE username = 'user_a'"
            ).fetchone()[0]
        self.assertNotEqual(stored_hash, "a-very-long-test-password-1")

    def test_duplicate_usernames_are_rejected_case_insensitively(self) -> None:
        with self.assertRaises(storage.StorageError):
            storage.register_user(
                "USER_A", "a-different-long-test-password", self.db_path
            )

    def test_invite_is_single_use_and_membership_roles_are_assigned(self) -> None:
        room_id, invite_code = self.make_pair()
        rooms_a = storage.list_user_rooms(self.user_a["user_id"], self.db_path)
        rooms_b = storage.list_user_rooms(self.user_b["user_id"], self.db_path)
        self.assertEqual(rooms_a[0]["role"], "A")
        self.assertEqual(rooms_b[0]["role"], "B")
        self.assertEqual(rooms_a[0]["partner_username"], "user_b")
        with self.assertRaises(storage.StorageError):
            storage.join_room(
                self.user_a["user_id"], invite_code, self.db_path
            )
        self.assertEqual(rooms_a[0]["room_id"], room_id)

    def test_expired_invite_is_rejected(self) -> None:
        _, invite_code = storage.create_room(self.user_a["user_id"], self.db_path)
        invite_hash = hashlib.sha256(invite_code.encode("ascii")).hexdigest()
        with storage._connect(self.db_path) as connection:
            connection.execute(
                "UPDATE rooms SET invite_expires_at = 0 WHERE invite_hash = ?",
                (invite_hash,),
            )
        with self.assertRaises(storage.StorageError):
            storage.join_room(
                self.user_b["user_id"], invite_code, self.db_path
            )

    def test_private_summaries_are_isolated_until_both_consent(self) -> None:
        room_id, _ = self.make_pair()
        storage.save_summary(
            self.user_a["user_id"], room_id, "A private draft", False, self.db_path
        )
        self.assertEqual(
            storage.get_own_summary(self.user_a["user_id"], room_id, self.db_path)[
                "content"
            ],
            "A private draft",
        )
        self.assertIsNone(
            storage.get_own_summary(self.user_b["user_id"], room_id, self.db_path)
        )
        self.assertIsNone(
            storage.get_shared_summaries(self.user_a["user_id"], room_id, self.db_path)
        )
        with self.assertRaises(storage.StorageError):
            storage.save_report(
                self.user_a["user_id"], room_id, "Should not persist", self.db_path
            )

        storage.save_summary(
            self.user_a["user_id"], room_id, "A consented summary", True, self.db_path
        )
        storage.save_summary(
            self.user_b["user_id"], room_id, "B consented summary", True, self.db_path
        )
        self.assertEqual(
            storage.get_shared_summaries(
                self.user_a["user_id"], room_id, self.db_path
            ),
            {"A": "A consented summary", "B": "B consented summary"},
        )

    def test_only_one_member_can_claim_generation_and_both_read_same_report(self) -> None:
        room_id, _ = self.make_pair()
        self.consent_both(room_id)

        self.assertEqual(
            storage.claim_report_generation(self.user_a["user_id"], room_id, self.db_path),
            "claimed",
        )
        self.assertEqual(
            storage.claim_report_generation(self.user_b["user_id"], room_id, self.db_path),
            "generating",
        )
        self.assertEqual(
            storage.get_report_generation_state(
                self.user_b["user_id"], room_id, self.db_path
            ),
            "generating",
        )

        storage.save_report(
            self.user_a["user_id"], room_id, "The single shared report", self.db_path
        )
        self.assertEqual(
            storage.get_report(self.user_a["user_id"], room_id, self.db_path),
            "The single shared report",
        )
        self.assertEqual(
            storage.get_report(self.user_b["user_id"], room_id, self.db_path),
            "The single shared report",
        )
        self.assertEqual(
            storage.get_report_generation_state(
                self.user_b["user_id"], room_id, self.db_path
            ),
            "completed",
        )
        self.assertEqual(
            storage.claim_report_generation(self.user_b["user_id"], room_id, self.db_path),
            "completed",
        )

    def test_failed_generation_can_be_reclaimed_and_report_cannot_be_overwritten(self) -> None:
        room_id, _ = self.make_pair()
        self.consent_both(room_id)
        self.assertEqual(
            storage.claim_report_generation(self.user_a["user_id"], room_id, self.db_path),
            "claimed",
        )
        storage.release_report_generation(self.user_a["user_id"], room_id, self.db_path)
        self.assertEqual(
            storage.claim_report_generation(self.user_b["user_id"], room_id, self.db_path),
            "claimed",
        )
        storage.save_report(
            self.user_b["user_id"], room_id, "Original shared report", self.db_path
        )
        self.assertEqual(
            storage.claim_report_generation(self.user_a["user_id"], room_id, self.db_path),
            "completed",
        )
        with self.assertRaises(storage.StorageError):
            storage.save_report(
                self.user_a["user_id"],
                room_id,
                "Replacement report",
                self.db_path,
            )
        self.assertEqual(
            storage.get_report(self.user_a["user_id"], room_id, self.db_path),
            "Original shared report",
        )

    def test_nonmember_cannot_read_or_write_room_data(self) -> None:
        room_id, _ = self.make_pair()
        outsider = storage.register_user(
            "outsider", "another-long-test-password", self.db_path
        )
        self.assertIsNone(
            storage.get_own_summary(outsider["user_id"], room_id, self.db_path)
        )
        with self.assertRaises(storage.StorageError):
            storage.save_summary(
                outsider["user_id"], room_id, "intrusion", True, self.db_path
            )
        with self.assertRaises(storage.StorageError):
            storage.get_room_consents(outsider["user_id"], room_id, self.db_path)

    def test_withdrawing_consent_removes_saved_report(self) -> None:
        room_id, _ = self.make_pair()
        self.consent_both(room_id)
        self.assertEqual(
            storage.claim_report_generation(self.user_a["user_id"], room_id, self.db_path),
            "claimed",
        )
        storage.save_summary(
            self.user_a["user_id"], room_id, "A temporarily private", False, self.db_path
        )
        with self.assertRaises(storage.StorageError):
            storage.claim_report_generation(self.user_b["user_id"], room_id, self.db_path)
        storage.save_summary(
            self.user_a["user_id"], room_id, "A shared again", True, self.db_path
        )
        self.assertEqual(
            storage.claim_report_generation(self.user_b["user_id"], room_id, self.db_path),
            "claimed",
        )
        storage.save_report(self.user_b["user_id"], room_id, "Shared report", self.db_path)
        self.assertEqual(
            storage.get_report(self.user_b["user_id"], room_id, self.db_path),
            "Shared report",
        )
        storage.save_summary(
            self.user_a["user_id"], room_id, "A revised", False, self.db_path
        )
        self.assertIsNone(
            storage.get_report(self.user_a["user_id"], room_id, self.db_path)
        )
        storage.save_summary(
            self.user_a["user_id"], room_id, "A revised and shared", True, self.db_path
        )
        self.assertEqual(
            storage.claim_report_generation(self.user_b["user_id"], room_id, self.db_path),
            "claimed",
        )

    def test_resaving_unchanged_summary_keeps_report(self) -> None:
        room_id, _ = self.make_pair()
        self.consent_both(room_id)
        storage.claim_report_generation(self.user_a["user_id"], room_id, self.db_path)
        storage.save_report(self.user_a["user_id"], room_id, "Report", self.db_path)
        self.assertFalse(
            storage.summary_change_clears_report(
                self.user_a["user_id"], room_id, "A shared summary", True, self.db_path
            )
        )
        storage.save_summary(
            self.user_a["user_id"], room_id, "A shared summary", True, self.db_path
        )
        self.assertEqual(
            storage.get_report(self.user_b["user_id"], room_id, self.db_path), "Report"
        )
        self.assertTrue(
            storage.summary_change_clears_report(
                self.user_a["user_id"], room_id, "A edited summary", True, self.db_path
            )
        )

    def test_deleting_room_removes_all_shared_data(self) -> None:
        room_id, _ = self.make_pair()
        self.consent_both(room_id)
        storage.claim_report_generation(self.user_a["user_id"], room_id, self.db_path)
        storage.save_report(self.user_a["user_id"], room_id, "Report", self.db_path)
        storage.delete_room(self.user_a["user_id"], room_id, self.db_path)
        self.assertEqual(storage.list_user_rooms(self.user_b["user_id"], self.db_path), [])


if __name__ == "__main__":
    unittest.main()
