from app.models.background_job import JobStatus, JobType


def test_background_job_types_cover_the_mvp_pipeline() -> None:
    assert {job_type.value for job_type in JobType} == {
        "process_intake",
        "qualify_lead",
        "generate_reply",
        "sync_crm",
    }


def test_background_job_statuses_include_safe_retry() -> None:
    assert JobStatus.RETRY_SCHEDULED.value == "retry_scheduled"
