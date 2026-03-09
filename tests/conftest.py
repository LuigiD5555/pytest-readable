def pytest_configure(config):
    config.addinivalue_line("markers", "auto_lang_only: test visible only when readable-lang=auto")
    config.addinivalue_line("markers", "es_lang_only: test visible only when readable-lang=es")
    config.addinivalue_line("markers", "en_lang_only: test visible only when readable-lang=en")


def pytest_collection_modifyitems(config, items):
    try:
        readable_lang = config.getoption("readable_lang")
    except Exception:
        readable_lang = "auto"

    kept = []
    deselected = []
    for item in items:
        is_auto_only = item.get_closest_marker("auto_lang_only") is not None
        is_es_only = item.get_closest_marker("es_lang_only") is not None
        is_en_only = item.get_closest_marker("en_lang_only") is not None

        if readable_lang == "auto":
            if is_es_only or is_en_only:
                deselected.append(item)
                continue
        if is_auto_only and readable_lang != "auto":
            deselected.append(item)
            continue
        if is_es_only and readable_lang != "es":
            deselected.append(item)
            continue
        if is_en_only and readable_lang != "en":
            deselected.append(item)
            continue
        kept.append(item)

    if deselected:
        config.hook.pytest_deselected(items=deselected)
        items[:] = kept
