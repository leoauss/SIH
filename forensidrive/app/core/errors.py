"""User-facing errors with optional technical details."""


class AppError(Exception):
    def __init__(self, user_message, technical_details=""):
        super().__init__(user_message)
        self.user_message = user_message
        self.technical_details = technical_details or ""

    def combined_technical(self):
        if self.technical_details:
            return self.technical_details
        return str(self)


class MissingCommandError(AppError):
    pass


class PermissionDeniedError(AppError):
    pass


class DeviceGoneError(AppError):
    pass


class UserCancelledError(AppError):
    pass


class CommandTimeoutError(AppError):
    pass


class CommandFailedError(AppError):
    pass
