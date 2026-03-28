from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from db.session import get_db

router = APIRouter()


@router.get("/status")
def database_status(db: Session = Depends(get_db)):
    try:
        rows = db.execute(
            text(
                "SELECT relname AS table_name, n_live_tup AS row_count "
                "FROM pg_stat_user_tables ORDER BY relname"
            )
        ).fetchall()
        tables = [{"name": r.table_name, "row_count": r.row_count} for r in rows]
        return {"connected": True, "database": "datalyze", "tables": tables}
    except Exception as exc:
        return {"connected": False, "error": str(exc), "tables": []}
