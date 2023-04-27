from typing import List


class CloudStorage:
    """
    Abstract CloudStorage class
    """

    def __init__(self, credentials):
        self.credentials = credentials

    def get_files_keys(self) -> List[str]:
        pass

    def get_file(self, _key: str) -> bytes:
        pass

    def put_file(self, _key: str, body_file: bytes) -> None:
        pass

    def delete_file(self, _key: str) -> None:
        pass
