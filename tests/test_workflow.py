import csv
import importlib.util
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location("outreach_" + name, ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


mail, resume, dependencies = (load(name) for name in ("mail", "resume", "dependencies"))


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        for path in (ROOT / "assets/examples").iterdir():
            shutil.copy2(path, self.base / path.name)
        profile = mail.read_json(self.base / "profile.json")
        profile.update(email="student@example.org", attachments=["resume-attachment.pdf"])
        mail.write_json(self.base / "profile.json", profile)
        (self.base / "resume-attachment.pdf").write_bytes(b"test attachment")
        self.write_teachers(["a@example.org"])

    def write_teachers(self, addresses):
        with (self.base / "teachers.csv").open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=["name", "email", "research", "source_url", "motivation", "subject", "body"])
            writer.writeheader()
            for address in addresses:
                writer.writerow(dict(name="Teacher", email=address, research="Research", source_url="https://example.org/faculty", motivation="Interest", subject="Individual subject", body="Personalized body, with comma\nand newline."))

    def draft(self):
        mail.draft_all(self.base)
        return next((self.base / "outbox").glob("*.json")).stem

    def approve(self, identifier):
        mail.approve(self.base, identifier, "TEST ONLY: mock send authorized")

    def test_personalized_csv_and_approval_invalidation(self):
        identifier = self.draft()
        path = self.base / "outbox" / f"{identifier}.json"
        draft = mail.read_json(path)
        self.assertEqual(draft["body"], "Personalized body, with comma\nand newline.")
        with self.assertRaises(ValueError):
            mail.send(self.base, identifier)
        self.approve(identifier)
        draft["body"] += " modified"
        mail.write_json(path, draft)
        with self.assertRaises(ValueError):
            mail.send(self.base, identifier)

    def test_attachments_and_duplicate_targets(self):
        identifier = self.draft()
        self.approve(identifier)
        (self.base / "resume-attachment.pdf").write_bytes(b"modified")
        with self.assertRaises(ValueError):
            mail.send(self.base, identifier)
        self.write_teachers(["a@example.org", "A@example.org"])
        with self.assertRaises(ValueError):
            mail.draft_all(self.base)

    @patch.dict("os.environ", {"SMTP_HOST": "mock", "SMTP_USER": "mock", "SMTP_PASSWORD": "mock"})
    def test_send_rerun_and_unknown_result(self):
        identifier = self.draft()
        self.approve(identifier)
        connection = MagicMock()
        with patch.object(mail.smtplib, "SMTP_SSL", return_value=connection):
            mail.send(self.base, identifier)
            with self.assertRaises(ValueError):
                mail.send(self.base, identifier)
        self.assertEqual(connection.send_message.call_count, 1)
        self.assertEqual(mail.state_for(self.base)[identifier]["status"], "sent")
        mail.write_json(self.base / "state.json", {})
        self.approve(identifier)
        connection.send_message.side_effect = OSError("mock connection lost")
        with patch.object(mail.smtplib, "SMTP_SSL", return_value=connection), self.assertRaises(OSError):
            mail.send(self.base, identifier)
        self.assertEqual(mail.state_for(self.base)[identifier]["status"], "uncertain")
        with self.assertRaises(ValueError):
            self.approve(identifier)

    @patch.dict("os.environ", {"SMTP_HOST": "mock", "SMTP_USER": "mock", "SMTP_PASSWORD": "mock"})
    def test_batch_checks_entire_queue_before_sending(self):
        self.write_teachers(["a@example.org", "b@example.org"])
        self.draft()
        paths = list((self.base / "outbox").glob("*.json"))
        for path in paths:
            self.approve(path.stem)
        draft = mail.read_json(paths[-1]); draft["body"] += " changed"
        mail.write_json(paths[-1], draft)
        connection = MagicMock()
        argv = ["mail.py", "--workspace", str(self.base), "send-approved", "--interval", "0"]
        with patch.object(mail.smtplib, "SMTP_SSL", return_value=connection), patch("sys.argv", argv), self.assertRaises(SystemExit):
            mail.main()
        connection.send_message.assert_not_called()
        self.approve(paths[-1].stem)
        with patch.object(mail.smtplib, "SMTP_SSL", return_value=connection), patch("sys.argv", argv):
            mail.main()
            mail.main()
        self.assertEqual(connection.send_message.call_count, 2)

    def test_missing_research_dependency_is_explicit(self):
        result = dependencies.check("research", [self.base])
        self.assertFalse(result["ready"])
        self.assertIn("academic-research-suite", result["missing"])
        self.assertTrue(dependencies.check("resume", [self.base])["ready"])

    def test_resume_escapes_content_and_removes_old_pdf(self):
        cv = mail.read_json(self.base / "cv.json")
        cv["name"] = r"Name & 100% \input{private}"
        cv["subtitle"] = "@@NAME@@"
        mail.write_json(self.base / "cv.json", cv)
        output = resume.render(self.base)
        tex = (output / "resume.tex").read_text()
        self.assertIn(r"\textbackslash{}input\{private\}", tex)
        self.assertIn("@@NAME@@", tex)
        (output / "resume.pdf").write_bytes(b"stale")
        resume.render(self.base)
        self.assertFalse((output / "resume.pdf").exists())

    @unittest.skipUnless(shutil.which("xelatex") and shutil.which("pdftotext"), "XeLaTeX/PDF text tools unavailable")
    def test_chinese_and_english_pdf_content(self):
        for language, name, section in [("zh", "测试同学", "教育背景"), ("en", "Example Student", "Education")]:
            with self.subTest(language=language):
                mail.write_json(self.base / "cv.json", dict(name=name, email="student@example.org", language=language, subtitle="Example University", sections=[dict(title=section, items=["Research project: reproducible analysis."])]))
                output = resume.render(self.base, True)
                text = subprocess.check_output(["pdftotext", str(output / "resume.pdf"), "-"], text=True)
                self.assertIn(name.casefold(), text.casefold())
                self.assertIn("student@example.org", text)
                self.assertIn("reproducible analysis", text)


if __name__ == "__main__":
    unittest.main()
