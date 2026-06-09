"""Exchange rate module: automatic rate update via free API."""

from typing import Dict, Optional

try:
    import urllib.request
    import urllib.error
    import json
    HAS_NETWORK = True
except ImportError:
    HAS_NETWORK = False

FALLBACK_RATES = {
    "USD": 7.24,
    "EUR": 7.86,
    "JPY": 0.048,
    "GBP": 9.12,
    "CNY": 1.0,
}


def fetch_exchange_rates() -> Optional[Dict[str, float]]:
    """
    Fetch exchange rates from free API (against CNY as base).

    Returns:
        Dict of currency code -> rate (1 currency = X CNY)
        None if network error or API failure.
    """
    if not HAS_NETWORK:
        return None

    api_urls = [
        "https://cdn.jsdelivr.net/gh/fawazahmed0/currency-api@1/latest/currencies/cny.json",
        "https://latest.currency-api.pages.dev/v1/currencies/cny.json",
    ]

    for url in api_urls:
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0"}
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode("utf-8"))

            if "cny" in data:
                cny_rates = data["cny"]
                result = {}

                for code, rate in cny_rates.items():
                    code_upper = code.upper()
                    if rate > 0:
                        result[code_upper] = 1.0 / rate

                for code in FALLBACK_RATES:
                    if code not in result:
                        result[code] = FALLBACK_RATES[code]

                return result

        except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError):
            continue
        except Exception:
            continue

    return FALLBACK_RATES.copy()


def get_rate_for_currency(currency_code: str) -> float:
    """
    Get exchange rate for a specific currency.

    Args:
        currency_code: Currency code (e.g., "USD", "EUR")

    Returns:
        Exchange rate (1 currency = X CNY). Falls back to default if API fails.
    """
    code = currency_code.upper()
    rates = fetch_exchange_rates()

    if rates and code in rates:
        return rates[code]

    return FALLBACK_RATES.get(code, 1.0)


def get_all_supported_rates() -> Dict[str, float]:
    """
    Get all supported exchange rates.

    Returns:
        Dict of currency code -> rate (1 currency = X CNY)
    """
    rates = fetch_exchange_rates()
    if rates:
        result = {}
        for code in ["CNY", "USD", "EUR", "JPY", "GBP"]:
            if code in rates:
                result[code] = rates[code]
            else:
                result[code] = FALLBACK_RATES[code]
        return result

    return FALLBACK_RATES.copy()


if __name__ == "__main__":
    print("Testing exchange rate module...")
    print()
    print("Fetching rates from API...")
    rates = fetch_exchange_rates()
    if rates:
        print("SUCCESS!")
        print()
        for code in ["CNY", "USD", "EUR", "JPY", "GBP"]:
            if code in rates:
                print(f"  1 {code} = ¥{rates[code]:.4f}")
    else:
        print("API unavailable, using fallback rates:")
        for code, rate in FALLBACK_RATES.items():
            print(f"  1 {code} = ¥{rate:.4f}")
