class PendingActionNotFoundError(Exception):
    def __init__(self, action_id: str):
        self.action_id = action_id
        super().__init__(f"Pending action {action_id} not found")


class UnsupportedPendingActionError(Exception):
    def __init__(self, action_name: str):
        self.action_name = action_name
        super().__init__(f"Unsupported pending action: {action_name}")
