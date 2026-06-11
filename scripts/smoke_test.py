import os
import sys
import httpx


CHECKS = [
    ("Companies House", lambda: httpx.get(
        "https://api.company-information.service.gov.uk/search/companies?q=test",
        auth=(os.environ["CH_API_KEY"], ""),
        timeout=5,
    ).raise_for_status()),
    ("GitHub", lambda: httpx.get(
        "https://api.github.com/user",
        headers={"Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}"},
        timeout=5,
    ).raise_for_status()),
    ("Anthropic", lambda: __import__(
        "enrich.llm_client", fromlist=["LLMClient"]
    ).LLMClient().complete("ping", max_tokens=3)),
]

failed = []
for name, check in CHECKS:
    try:
        check()
        print(f"  ✓ {name} OK")
    except Exception as e:
        print(f"  ✗ {name} FAIL: {e}")
        failed.append(name)

if failed:
    print(f"\nFailed: {', '.join(failed)}")
    sys.exit(1)
else:
    print("\nAll checks passed.")
