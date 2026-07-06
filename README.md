# SunStone Secure Artemis FedRAMP Advisor Information (MKT-CAS-WEB)

SunStone Secure provides Artemis Agent AI-native compliance and advisory services.

## General description of the consulting or advisory service

SunStone Secure has been providing FedRAMP and other regulated security and compliance advisory services, including CISO-as-a-Serice and ConMon-as-a-Service offerrings since 2019.

## Contact information

Sales: Mats Nahlinder, info at sunstonesecure dot com

Security Reporting: Security Team, security at sunstonesecure dot com

General Questions: (650) 508-1796

## Types of consulting or advisory services offered

20x: 
  - AI-native and Agentic SaaS capabilities for continuous threat assessment, audit readiness and compliance operations.
    
Rev5: 
  - AI-native and Agentic SaaS capabilities for continuous threat assessment, audit readiness, and compliance operations.
  - Rev 5 SSP and appendices automation.
  - Rev 5 SAP and SRTM automation.
  - Rev 5 interview preparation automation.
  - Rev 5 ConMon automation.
  - Rev 5 red teaming automation.

## Optional: Positive attestations from customers or customer references

SunStone Secure advises and maintains ConMon preparedness for multiple Rev 4, Rev 5 and 20x FedRAMP Marketplace-listed CSPs.  Please contact:

Mats Nahlinder, info at sunstonesecure dot com
(650) 508-1796

For detailed customer references.

## Public JSON artifact

The machine-readable FedRAMP Advisor Information JSON is published as a GitHub Release asset:

https://github.com/SunStone-Secure-LLC/artemisadvisory/releases/download/fedramp-advisor-information/fedramp-advisor-information.json

The release workflow builds this JSON from the `20x-MKT-CAS-WEB-*` HTML comment metadata in this README.

### Manual download

Open the release page and download `fedramp-advisor-information.json`:

https://github.com/SunStone-Secure-LLC/artemisadvisory/releases/tag/fedramp-advisor-information

### CLI download

Use `curl`:

```bash
curl -L \
  -o fedramp-advisor-information.json \
  https://github.com/SunStone-Secure-LLC/artemisadvisory/releases/download/fedramp-advisor-information/fedramp-advisor-information.json
```

Or use the GitHub CLI:

```bash
gh release download fedramp-advisor-information \
  --repo SunStone-Secure-LLC/artemisadvisory \
  --pattern fedramp-advisor-information.json \
  --clobber
```

### REST API download

Fetch the release by tag, find the asset named `fedramp-advisor-information.json`, then download its `browser_download_url`.

```bash
curl -L \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2026-03-10" \
  https://api.github.com/repos/SunStone-Secure-LLC/artemisadvisory/releases/tags/fedramp-advisor-information
```

Python example:

```python
import json
import urllib.request

owner = "SunStone-Secure-LLC"
repo = "artemisadvisory"
tag = "fedramp-advisor-information"
asset_name = "fedramp-advisor-information.json"

request = urllib.request.Request(
    f"https://api.github.com/repos/{owner}/{repo}/releases/tags/{tag}",
    headers={
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2026-03-10",
        "User-Agent": "fedramp-advisor-downloader",
    },
)

with urllib.request.urlopen(request) as response:
    release = json.load(response)

asset = next(item for item in release["assets"] if item["name"] == asset_name)

urllib.request.urlretrieve(asset["browser_download_url"], asset_name)
print(f"Downloaded {asset_name}")
```

### Attestation verification

After downloading the JSON, verify its GitHub Artifact Attestation:

```bash
gh attestation verify fedramp-advisor-information.json \
  --repo SunStone-Secure-LLC/artemisadvisory \
  --signer-workflow SunStone-Secure-LLC/artemisadvisory/.github/workflows/publish-fedramp-advisor-information.yml
```

<!-- 20x-MKT-CAS-WEB-serviceDescription: "SunStone Secure has been providing FedRAMP and other regulated security and compliance advisory services, including CISO-as-a-Serice and ConMon-as-a-Service offerrings since 2019." -->
<!-- 20x-MKT-CAS-WEB-contactInformation: ["Mats Nahlinder|info@sunstonesecure.com","Security Team|security@sunstonesecure.com","General|(650)508-1796"] -->
<!-- 20x-MKT-CAS-WEB-servicesOffered: [{serviceName:"20x",description:"AI-native and Agentic SaaS capabilities for continuous threat assessment, audit readiness and compliance operations."},{serviceName:"Rev5",description:"AI-native and Agentic SaaS capabilities for continuous threat assessment, audit readiness, and compliance operations.|Rev 5 SSP and appendices automation.|Rev 5 SAP and SRTM automation.|Rev 5 interview preparation automation.|Rev 5 ConMon automation.|Rev 5 red teaming automation."}] -->
<!-- 20x-MKT-CAS-WEB-customerReferences: ["SunStone Secure advises and maintains ConMon preparedness for multiple Rev 4, Rev 5 and 20x FedRAMP Marketplace-listed CSPs.  Please contact: Mats Nahlinder info@sunstonesecure.com (650) 508-1796 For detailed customer references."] -->
