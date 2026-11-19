# Documentation claim auditor

This offline static checker compares exact documentation phrases with Python source patterns. It examines the root README and Markdown under docs, excluding fenced blocks; inline code counts. It scans source without executing it. Install and run:

```sh
python3 -m pip install dist/api_request_claim_audit-0.1.0-py3-none-any.whl
api-request-claim-audit audit . --json
api-request-claim-audit audit . --fail-on medium --ignore vendor/
python3 -m api_request_claim_audit --version
```

Findings are reported as follows:

```text
documented-api-request-claim-false: HIGH, or MEDIUM when evidence exists only in tests
documented-no-api-request-claim-false: HIGH
```

Exit status is 0 for a passing threshold, 2 for findings at or above the threshold, and 1 for usage or I/O errors. The default threshold is high. Ignore prefixes are relative paths and can be repeated. Test files are considered separately; fixtures, docs, examples, and symlinks are excluded from source evidence.

## Differentiation

Web scraping combines fetching and parsing; its fetch can also satisfy this checker. The two families use different claim text, and a project can satisfy both. Database claims and connection-plus-execution evidence belong to another family and do not trigger this check; the checked feature does not trigger that database audit. Redis, memcached, cachetools and functools caching are not evidence here. Text, format, HTML, PDF, spreadsheet, word document, presentation and image generation claims are distinct, as are document extraction, splitting, detection and cropping claims.

The sibling audit of importable interfaces checks documented names and keyword arguments against source; it addresses a different question. Offline, privacy, timeout and server-sent event audits may share a transport pattern, but check different claims.

## Limitations

Exact phrases and static patterns are used, not semantic judgment. Dead code counts, unsupported alias chains can be missed, denial handling depends on the listed phrases, and each route must occur in one module. A call site does not establish the destination: variable URLs, local servers and mocks count. Some phrases can describe configuration wrappers, internal interfaces, sockets or integrations the user must wire up; review findings in context.

Client construction alone, a method call on an unknown object alone, and construction of a request object alone are insufficient. Subprocess calls to curl or wget, websocket connections, feed parsing and parsing with BeautifulSoup or lxml without a fetch are excluded. Fetching followed by parsing can nevertheless satisfy the checker.

Document extraction calls from Mindee, Azure Document Intelligence, Veryfi, Google Document AI, Textract, Eden AI, LlamaParse, Nanonets, Docsumo, ABBYY Vantage, Rossum, Klippa, Parseur and Extend are excluded, including arbitrary products, model identifiers and processors. Opaque identifiers or dashboard configuration do not establish the checked operation.
