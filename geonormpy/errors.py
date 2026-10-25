"""Stable, JSON-serializable errors for library and command-line callers."""


class GeoNormPyError(ValueError):
    def __init__(self, code, message, *, field=None, details=None):
        super().__init__(message)
        self.code = code
        self.field = field
        self.details = details or {}

    def to_dict(self):
        return {'code': self.code, 'message': str(self), 'field': self.field, 'details': self.details}

    def __reduce__(self):
        return (type(self), (self.code, str(self)), {'field': self.field, 'details': self.details})


def error_details(error):
    if isinstance(error, GeoNormPyError):
        return error.to_dict()
    code = 'file_not_found' if isinstance(error, FileNotFoundError) else (
        'file_access_error' if isinstance(error, OSError) else 'calculation_error')
    return {'code': code, 'message': str(error), 'field': None, 'details': {}}
