import unittest
from api_request_claim_audit.phrases import APIREQUEST, NOAPIREQUEST
EXPECTED_APIREQUEST = ('makes api requests', 'make api requests', 'sends api requests', 'send api requests', 'calls rest apis', 'call rest apis', 'calls rest api', 'call rest api', 'calls an api', 'call an api', 'calls the api', 'call the api', 'sends http requests', 'send http requests', 'makes http requests', 'make http requests', 'sends requests to the api', 'send requests to the api', 'queries the api', 'query the api', 'fetches data from the api', 'fetch data from the api', 'retrieves data from the api', 'retrieve data from the api', 'posts data to the api', 'post data to the api', 'api request support', 'rest api support', 'http request support', 'api integration', 'rest api integration', 'makes api calls', 'make api calls', 'sends api calls', 'send api calls', 'talks to the api', 'talk to the api', 'communicates with the api', 'communicate with the api', 'connects to the api', 'connect to the api', 'calls external apis', 'call external apis', 'calls third party apis', 'call third party apis', 'api client', 'rest client', 'http client', 'sends get requests', 'send get requests')
EXPECTED_NOAPIREQUEST = ('does not make api requests', 'never makes api requests', 'does not send api requests', 'never sends api requests', 'does not call rest apis', 'never calls rest apis', 'does not call an api', 'never calls an api', 'does not send http requests', 'never sends http requests', 'does not make http requests', 'never makes http requests', 'does not query the api', 'never queries the api', 'does not fetch data from the api', 'never fetches data from the api', 'does not post data to the api', 'never posts data to the api', 'no api request support', 'no rest api support', 'does not make api calls', 'never makes api calls', 'no api integration', 'no http client')

class PhraseOracle(unittest.TestCase):
    def test_phrases(self):
        self.assertEqual(APIREQUEST, EXPECTED_APIREQUEST)
        self.assertEqual(NOAPIREQUEST, EXPECTED_NOAPIREQUEST)

import json
from pathlib import Path
import subprocess
import sys
import tempfile
from api_request_claim_audit.audit import audit, claims, evidence, GENERIC, HTTP_METHODS

class EvidenceTests(unittest.TestCase):
    def test_routes(self):
        samples = ([f'import {lib}\n{lib}.{method}()' for lib in ('requests', 'httpx') for method in HTTP_METHODS] + [f'import {lib}\n{lib}.{client}()\nx.{method}()' for lib, client in [('requests','Session'), ('httpx','Client'), ('httpx','AsyncClient'), ('aiohttp','ClientSession')] for method in HTTP_METHODS] + ['from requests import get as g\ng()', 'import requests as r\nr.get()', 'from httpx import get\nget()', 'import urllib.request\nurllib.request.urlopen(x)', 'from urllib.request import urlopen as u\nu(x)', 'import http.client\nhttp.client.HTTPConnection(x)\nx.request()', 'import http.client\nhttp.client.HTTPSConnection(x)\nx.request()', 'from http.client import HTTPConnection as C\nC(x)\nx.request()', 'from aiohttp import ClientSession as C\nC()\nx.get()', 'from x import make_api_request as m\nm()'] + ['x.' + name + '()' for name in GENERIC])
        for source in samples:
            with self.subTest(source=source): self.assertTrue(evidence(source))
    def test_non_evidence(self):
        samples = ['import requests', 'import httpx, aiohttp, urllib, http.client', 'import requests\nrequests.Session()', 'import httpx\nhttpx.Client()', 'import httpx\nhttpx.AsyncClient()', 'import aiohttp\naiohttp.ClientSession()', 'import http.client\nhttp.client.HTTPConnection(x)', 'import http.client\nhttp.client.HTTPSConnection(x)', 'x.get()', 'x.request()', 'import urllib.request\nurllib.request.Request(x)', 'subprocess.run(["curl"])', 'subprocess.run(["wget"])', 'websockets.connect(x)', 'feedparser.parse(x)', 'BeautifulSoup(x)', 'lxml.parse(x)', '"api"', '"requests.get()"', 'requests.get', 'mindee.parse(InvoiceV4)', 'azure.begin_analyze_document("prebuilt-layout")', 'veryfi.Client()', 'documentai.process_document(x)', 'textract.analyze_document(x)', 'eden.universal_ai(x)', 'llamaparse.parse(x)', 'nanonets.ocr("opaque")', 'docsumo.upload(x)', 'make_api_request()', 'import requests\ndef get(): pass\nrequests.get()', 'from requests import get\nget = 3\nget()', 'from requests import get\nwith x as get: pass\nget()', 'import requests\nrequests.get(']
        for source in samples:
            with self.subTest(source=source): self.assertFalse(evidence(source))

class AuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup); self.root = Path(self.temp.name)
    def write(self, name, content):
        p = self.root / name; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(content, encoding='utf-8')
    def test_findings(self):
        self.write('README.md', 'makes api requests')
        self.assertEqual(audit(self.root)['findings'][0]['id'], 'documented-api-request-claim-false')
        self.assertEqual(audit(self.root)['findings'][0]['severity'], 'HIGH')
        self.write('tests/test_x.py', 'import requests\nrequests.get(x)')
        self.assertEqual(audit(self.root)['findings'][0]['severity'], 'MEDIUM')
        self.write('app.py', 'import requests\nrequests.get(x)')
        self.assertEqual(audit(self.root)['verdict'], 'PASS')
        self.write('README.md', 'does not make api requests')
        self.assertEqual(audit(self.root)['findings'][0]['id'], 'documented-no-api-request-claim-false')
        (self.root / 'app.py').unlink()
        self.assertEqual(audit(self.root)['verdict'], 'PASS')
        self.write('README.md', 'unrelated')
        self.assertEqual(audit(self.root)['verdict'], 'PASS')
    def test_exclusions(self):
        self.write('README.md', 'makes api requests')
        self.write('a.py', 'import requests\nrequests.Session()'); self.write('b.py', 'x.get()')
        for d in ('examples', 'fixtures', 'docs'): self.write(d + '/x.py', 'import requests\nrequests.get(x)')
        (self.root / 'link.py').symlink_to(self.root / 'examples/x.py')
        self.assertEqual(audit(self.root)['findings'][0]['severity'], 'HIGH')
        self.write('src/test_x.py', 'import requests\nrequests.get(x)')
        self.assertEqual(audit(self.root)['findings'][0]['severity'], 'MEDIUM')
        self.assertEqual(audit(self.root, ['src/'])['findings'][0]['severity'], 'HIGH')
    def test_claims(self):
        self.assertEqual(claims('```\nmakes api requests\n```'), (False, False))
        self.assertEqual(claims('`makes api requests`'), (True, False))
        self.assertEqual(claims('does not make api requests'), (False, True))
        self.assertEqual(claims('MAKES-API-REQUESTS'), (True, False))
        self.assertEqual(claims('nothing here'), (False, False))
    def test_cli(self):
        self.write('README.md', 'makes api requests')
        cmd = [sys.executable, '-m', 'api_request_claim_audit', 'audit', str(self.root)]
        p = subprocess.run(cmd + ['--json'], capture_output=True, text=True)
        self.assertEqual(p.returncode, 2); result = json.loads(p.stdout)
        self.assertEqual(result['verdict'], 'FAIL'); self.assertTrue(result['findings'][0]['message'])
        self.write('tests/test_x.py', 'import requests\nrequests.get(x)')
        self.assertEqual(subprocess.run(cmd, capture_output=True).returncode, 0)
        self.assertEqual(subprocess.run(cmd + ['--fail-on', 'medium'], capture_output=True).returncode, 2)
        self.write('app.py', 'import requests\nrequests.get(x)'); self.write('README.md', 'does not make api requests')
        self.assertEqual(subprocess.run(cmd, capture_output=True).returncode, 2)
        self.assertEqual(subprocess.run([sys.executable, '-m', 'api_request_claim_audit', '--version'], capture_output=True, text=True).stdout.strip(), '0.1.0')
