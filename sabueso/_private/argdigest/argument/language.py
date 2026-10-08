from sabueso._private.argdigest._shared import refuse


def digest_language(language, caller=None):
    if language in ("en", "es"):
        return language
    raise refuse("language", language, caller, "expected 'en' or 'es'")
