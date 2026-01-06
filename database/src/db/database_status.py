from record_types import RecordTypes


class RepositoryError(Exception):
    def __init__(self, message):
        super().__init__(message)
        
class RepositoryTimeoutError(RepositoryError):
    def __init__(self, point_of_error=None):
        message = "Database connection timed out" + f":{point_of_error}" if point_of_error else "!"
        super().__init__(message)

class RepositoryInternalError(RepositoryError):
    def __init__(self, error_desc: str):
        super().__init__(f"An internal error occurred: {error_desc}")
        
        
class RepositoryParsingError(RepositoryError):
    def __init__(self, error_desc: str):
        super().__init__(f"An error occurred while parsing results: {error_desc}")
        
        
class RepositoryNotFoundError(RepositoryError):
    def __init__(self, value):
        super().__init__(f"{value} was not found!")
        
        
class RepositoryRecordInvalid(RepositoryError):
    def __init__(self, value):
        valid_types = list(RecordTypes._value2member_map_)
        super().__init__(f"Invalid record type provided: {value}! Must be between {valid_types[0]} and {valid_types[-1]}")