import enum


class EmailCategory(str, enum.Enum):
    APPLICATION_CONFIRMATION = "application_confirmation"
    REJECTION = "rejection"
    INTERVIEW_INVITATION = "interview_invitation"
    ASSESSMENT = "assessment"
    RECRUITER_OUTREACH = "recruiter_outreach"
    OFFER = "offer"
    FOLLOW_UP_NEEDED = "follow_up_needed"
    IRRELEVANT = "irrelevant"


class ApplicationStatus(str, enum.Enum):
    APPLIED = "applied"
    ASSESSMENT = "assessment"
    INTERVIEW_SCHEDULED = "interview_scheduled"
    REJECTED = "rejected"
    OFFER_RECEIVED = "offer_received"
    FOLLOW_UP = "follow_up"
    UNKNOWN = "unknown"


class EventType(str, enum.Enum):
    APPLICATION_CONFIRMATION = "application_confirmation"
    REJECTION = "rejection"
    INTERVIEW_INVITATION = "interview_invitation"
    ASSESSMENT = "assessment"
    RECRUITER_OUTREACH = "recruiter_outreach"
    OFFER = "offer"
    FOLLOW_UP_NEEDED = "follow_up_needed"
    IRRELEVANT = "irrelevant"
    STATUS_UPDATE = "status_update"
