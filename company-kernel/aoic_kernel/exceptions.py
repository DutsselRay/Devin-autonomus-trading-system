class AOICError(Exception):
    pass


class AuthorityDenied(AOICError):
    pass


class BudgetExceeded(AOICError):
    pass


class ApprovalExpired(AOICError):
    pass


class PolicyViolation(AOICError):
    pass


class PITViolation(AOICError):
    pass


class PublicationGateBlocked(AOICError):
    pass


class CharterInvalid(AOICError):
    pass


class IdempotencyViolation(AOICError):
    pass
