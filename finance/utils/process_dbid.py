from django.db import connections
from django.apps import apps
import logging
logger = logging.getLogger(__name__)

def reset_pk_sequence_safely(model, alias="default"):
    """
    일부 레코드 삭제 후 PK(id) 재시작 정책:
      - 테이블이 비어있으면 → 다음 id = 1 로 시작되도록 리셋
      - 레코드가 남아있으면 → 다음 id = (현재 MAX(id) + 1) 로 맞춤
    DB별로 안전하게 처리. 테이블명은 model._meta.db_table 사용.
    """
    engine = connections[alias].settings_dict.get("ENGINE", "")
    table = model._meta.db_table

    # 남은 행/최대 id 는 ORM으로 확인 (raw SQL 불필요)
    qs = model.objects.using(alias).all()
    count = qs.count()
    max_id = qs.order_by("-id").values_list("id", flat=True).first() or 0

    logger.info("[PK-RESET] table=%s engine=%s count=%s max_id=%s", table, engine, count, max_id)

    with connections[alias].cursor() as cursor:
        if "postgresql" in engine:
            # PostgreSQL: 시퀀스를 테이블의 현재 MAX(id)로 맞춤 (비어있으면 1, 존재하면 max+1)
            # setval(seq, last_value, is_called)
            # is_called=True이면 nextval() 호출 시 last_value+1 반환됨
            cursor.execute(
                f"SELECT setval(pg_get_serial_sequence(%s, 'id'), COALESCE(MAX(id), 1), COALESCE(MAX(id) > 0, FALSE)) FROM {table}",
                [table],
            )
            logger.info("[PK-RESET] PostgreSQL sequence synced for %s", table)

        elif "sqlite3" in engine:
            # SQLite:
            # - AUTOINCREMENT 일 때만 sqlite_sequence 존재
            # - 비어있으면 sqlite_sequence에서 해당 테이블 row 삭제 → 다음 id=1
            # - 비어있지 않으면 SQLite는 기본적으로 max(id)+1 사용 → 추가 조치 불필요
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sqlite_sequence';")
            has_seq = cursor.fetchone() is not None

            if count == 0 and has_seq:
                cursor.execute("DELETE FROM sqlite_sequence WHERE name=%s", [table])
                logger.info("[PK-RESET] SQLite sqlite_sequence cleared for %s", table)
            else:
                logger.info("[PK-RESET] SQLite: no action needed (next id will be max+1)")

        elif "mysql" in engine:
            # MySQL/MariaDB:
            # - 비어있으면 AUTO_INCREMENT=1 로
            # - 남아있으면 AUTO_INCREMENT = max_id + 1 로
            next_val = 1 if count == 0 else (max_id + 1)
            cursor.execute(f"ALTER TABLE {table} AUTO_INCREMENT = %s", [next_val])
            logger.info("[PK-RESET] MySQL AUTO_INCREMENT set to %s for %s", next_val, table)

        else:
            logger.warning("[PK-RESET] Unsupported engine: %s (no-op)", engine)

