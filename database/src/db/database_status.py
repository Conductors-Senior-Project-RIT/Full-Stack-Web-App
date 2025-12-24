class RepositoryError(Exception):
    def __init__(self, error_desc: str):
        super().__init__(f"An error occurred: {error_desc}")
        
class NotFoundError(Exception):
    def __init__(self, value):
        super().__init__(f"{value} was not found!")