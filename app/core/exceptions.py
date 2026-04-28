from uuid import UUID


# ---- Current Version -----
class ResourceNotFoundException(Exception):
    def __init__(self, resouce_id: str | UUID, name: str):
        self.resource_id = resouce_id
        self.name = name


class PaperNotFoundException(ResourceNotFoundException):
    def __init__(self, paper_id: str | UUID):
        super().__init__(paper_id, "Paper")


class SessionNotFoundException(ResourceNotFoundException):
    def __init__(self, session_id: str):
        super().__init__(session_id, "Session")


# -------- V1 -------------
# class PaperNotFoundException(Exception):
#     def __init__(self, paper_id: str | UUID):
#         self.paper_id = paper_id


# -------- V2 -------------
# class ResourceNotFoundError(Exception):
#     pass


# class PaperNotFoundException(Exception):
#     def __init__(self, paper_id: str | UUID):
#         self.paper_id = paper_id


# class SessionNotFoundError(Exception):
#     def __init__(self, session_id: str):
#         self.session_id = session_id


# -------- V3 -------------
# class ResourceNotFoundError(Exception):
#     pass


# class PaperNotFoundException(Exception):
#     def __init__(self, paper_id: str | UUID):
#         self.paper_id = paper_id
#         self.name = "Paper"


# class SessionNotFoundError(Exception):
#     def __init__(self, session_id: str):
#         self.session_id = session_id
#         self.name = "Session"
