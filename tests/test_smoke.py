import shutil
import unittest
import uuid
from pathlib import Path

from cli import commands


class SmokeTest(unittest.TestCase):
    def test_ingest_sample_data(self):
        case_id = f"smoke-{uuid.uuid4().hex[:8]}"
        case_dir = commands.case_paths(case_id)["case_dir"]
        try:
            commands.init_case(case_id, title="Smoke Test")
            run_id_1 = commands.add_run(
                case_id=case_id,
                source="splunk",
                query_name="Splunk Sample",
                query_text=None,
                time_start="2024-07-01T12:00:00Z",
                time_end="2024-07-01T12:15:00Z",
                file_path=Path("sample_data/splunk.ndjson"),
            )
            run_id_2 = commands.add_run(
                case_id=case_id,
                source="kusto",
                query_name="Kusto Sample",
                query_text=None,
                time_start="2024-07-01T12:00:00Z",
                time_end="2024-07-01T12:15:00Z",
                file_path=Path("sample_data/kusto.ndjson"),
            )
            count_1 = commands.ingest_run(case_id, run_id_1)
            count_2 = commands.ingest_run(case_id, run_id_2)
            self.assertGreater(count_1, 0)
            self.assertGreater(count_2, 0)
        finally:
            if case_dir.exists():
                shutil.rmtree(case_dir)


if __name__ == "__main__":
    unittest.main()
