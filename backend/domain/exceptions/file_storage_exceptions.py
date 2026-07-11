"""Business-rule violations for the file storage service.

Plain Python exceptions, no framework dependency — translated into HTTP
responses at the api/ boundary (see core/exceptions.py).
"""


class FileStorageError(Exception):
    """Raised when the storage layer cannot fulfil a store/delete request
    (e.g. a collision-free filename couldn't be found after several
    attempts). Not tied to any particular backend."""
