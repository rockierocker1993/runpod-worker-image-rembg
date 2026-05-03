from db.database import SessionLocal
from db.models import RembgImage


def save_rembg_image(
    job_id: str | None,
    processing_time: float,
    original_url: str,
    output_url: str,
    model_name: str,
    original_size: tuple[int, int],
    output_size: tuple[int, int],
) -> RembgImage:
    """Insert a new rembg image record and return it."""
    record = RembgImage(
        job_id=job_id,
        processing_time=processing_time,
        original_url=original_url,
        output_url=output_url,
        model_name=model_name,
        original_width=original_size[0],
        original_height=original_size[1],
        output_width=output_size[0],
        output_height=output_size[1],
    )

    with SessionLocal() as session:
        session.add(record)
        session.commit()
        session.refresh(record)

    return record
