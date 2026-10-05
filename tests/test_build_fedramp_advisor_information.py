import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import build_fedramp_advisor_information as build  # noqa: E402

CONTACT = (
    '{pointOfContactName:"A B",jobTitle:"Sales",email:"a@b.com",'
    'phone:"(650) 508-1796",companyWebsite:"https://example.com"}'
)


def readme(contact: str = CONTACT) -> str:
    return "\n".join(
        [
            '<!-- 20x-MKT-CAS-WEB-advisorName: "X" -->',
            '<!-- 20x-MKT-CAS-WEB-logo: "https://example.com/l.svg" -->',
            '<!-- 20x-MKT-CAS-WEB-serviceDescription: "Desc" -->',
            f"<!-- 20x-MKT-CAS-WEB-contactInformation: {contact} -->",
            '<!-- 20x-MKT-CAS-WEB-servicesOffered: [{serviceName:"S",description:"D"}] -->',
        ]
    )


def build_from(text: str) -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "README.md"
        path.write_text(text, encoding="utf-8")
        return build.build_advisor_information(path)


class ContactInformationTests(unittest.TestCase):
    def test_emits_contact_object(self):
        doc = build_from(readme())
        self.assertEqual(
            doc["contactInformation"],
            {
                "pointOfContactName": "A B",
                "jobTitle": "Sales",
                "email": "a@b.com",
                "phone": "(650) 508-1796",
                "companyWebsite": "https://example.com",
            },
        )
        json.dumps(doc)

    def test_rejects_legacy_string_array(self):
        with self.assertRaises(ValueError):
            build_from(readme('["A|a@b.com"]'))

    def test_rejects_missing_field(self):
        with self.assertRaises(ValueError):
            build_from(readme(CONTACT.replace('jobTitle:"Sales",', "")))

    def test_rejects_unexpected_field(self):
        with self.assertRaises(ValueError):
            build_from(readme(CONTACT.replace("}", ',extra:"x"}')))

    def test_rejects_bad_email(self):
        with self.assertRaises(ValueError):
            build_from(readme(CONTACT.replace("a@b.com", "nope")))

    def test_rejects_bad_website(self):
        with self.assertRaises(ValueError):
            build_from(readme(CONTACT.replace("https://example.com", "example.com")))

    def test_repository_readme_builds(self):
        doc = build.build_advisor_information(ROOT / "README.md")
        self.assertIsInstance(doc["contactInformation"], dict)


if __name__ == "__main__":
    unittest.main()
