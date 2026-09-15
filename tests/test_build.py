import hashlib, importlib.util, json, pathlib, tempfile, unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("fetch", ROOT / "build/fetch.py")
fetch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fetch)


class Build(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        scratch = ROOT / ".work/test-temp"
        scratch.mkdir(parents=True, exist_ok=True)
        tempfile.tempdir = str(scratch)

    def test_recipes_and_sources_resolve(self):
        items = {
            p["name"]: p
            for group in ["lfs", "blfs", "ai"]
            for p in json.loads((ROOT / "sources" / f"{group}.json").read_text())
        }
        for name in ["lfs", "blfs"]:
            plan = json.loads((ROOT / "build" / f"{name}-plan.json").read_text())
            self.assertTrue(plan)
            for p in plan:
                self.assertTrue((ROOT / p["recipe"]).is_file(), p)
                if p["source"]:
                    self.assertIn(p["source"], items)
                self.assertNotIn("grub", p["recipe"])
                self.assertNotIn("chapter10", p["recipe"])
        self.assertTrue(
            any(
                "linux-headers" in p["recipe"]
                for p in json.loads((ROOT / "build/lfs-plan.json").read_text())
            )
        )

    def test_checksum_mismatch_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            p = pathlib.Path(d) / "source"
            p.write_bytes(b"original")
            checksum = "sha256:" + hashlib.sha256(p.read_bytes()).hexdigest()
            fetch.verify(p, checksum)
            p.write_bytes(b"corrupt")
            with self.assertRaises(ValueError):
                fetch.verify(p, checksum)
            with self.assertRaises(ValueError):
                fetch.fetch(
                    {
                        "name": "source",
                        "checksum": checksum,
                        "url": "https://invalid.invalid",
                    },
                    pathlib.Path(d),
                )

    def test_git_blob_integrity(self):
        with tempfile.TemporaryDirectory() as d:
            p = pathlib.Path(d) / "certdata"
            p.write_bytes(b"abc")
            fetch.verify(p, "git-blob:" + hashlib.sha1(b"blob 3\0abc").hexdigest())

    def test_no_unresolved_book_placeholders(self):
        for p in (ROOT / "build/recipes").glob("*.sh"):
            for marker in ["<xxx>", "<paper_size>", "<your", "tzselect", "passwd root"]:
                self.assertNotIn(marker, p.read_text(), p)

    def test_cuda_pin(self):
        items = json.loads((ROOT / "sources/ai.json").read_text())
        self.assertFalse(any("13." in p["url"] for p in items if "component" in p))
        self.assertIn(
            "CMAKE_CUDA_ARCHITECTURES=52",
            (ROOT / "build/stages/09-llama-cpp.sh").read_text(),
        )


if __name__ == "__main__":
    unittest.main()
