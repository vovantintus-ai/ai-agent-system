from dealhunter.sources.rss import parse_price


def test_parse_price_euro_symbol_prefix():
    assert parse_price("Makita drill €95 like new") == 95


def test_parse_price_suffix_currency():
    assert parse_price("Laptop 650 EUR") == 650


def test_parse_price_thousands_dot():
    assert parse_price("Car €12.500 negotiable") == 12500


def test_parse_price_none_when_absent():
    assert parse_price("Free to a good home") is None
    assert parse_price("") is None


def test_parse_price_dollar():
    assert parse_price("$1200 gaming rig") == 1200
