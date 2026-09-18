class SkyCardsError(Exception):
    """Base class for expected, user-facing errors in this app.

    Callers catch this (not bare Exception) so truly unexpected bugs still
    surface with a full traceback instead of being swallowed.
    """


class ConfigError(SkyCardsError):
    pass


class CityError(SkyCardsError):
    pass


class OpenSkyError(SkyCardsError):
    pass


class AircraftDbError(SkyCardsError):
    pass
