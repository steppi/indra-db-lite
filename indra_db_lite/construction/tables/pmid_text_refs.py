import argparse
from contextlib import closing
import logging
import os
import sqlite3

from indra_db_lite.construction import get_sqlite_tables
from indra_db_lite.construction import import_csv_into_sqlite
from indra_db_lite.construction import query_to_csv

logger = logging.getLogger(__name__)


def pmid_text_refs_to_csv(outpath: str) -> None:
    query = """
    SELECT DISTINCT
        pmid_num, id
    FROM
        text_ref
    """
    query_to_csv(query, outpath)


def create_pmid_text_ref_table(
        pmid_text_refs_path: str, sqlite_db_path: str
) -> None:
    query = """--
    CREATE TABLE IF NOT EXISTS pmid_text_refs (
    pmid INTEGER PRIMARY KEY,
    text_ref_id INTEGER,
    UNIQUE(text_ref_id)
    );
    """
    with closing(sqlite3.connect(sqlite_db_path)) as conn:
        with closing(conn.cursor()) as cur:
            cur.execute(query)
        conn.commit()
    import_csv_into_sqlite(
        pmid_text_refs_path,
        'pmid_text_refs',
        sqlite_db_path
    )
    index_query1 = """--
    CREATE INDEX IF NOT EXISTS
        pmid_text_refs_pmid_idx
    ON
        pmid_text_refs(pmid)
    """
    index_query2 = """--
    CREATE INDEX IF NOT EXISTS
        pmid_text_refs_text_ref_id_idx
    ON
        pmid_text_refs(text_ref_id)
    """
    with closing(sqlite3.connect(sqlite_db_path)) as conn:
        with closing(conn.cursor()) as cur:
            for query in index_query1, index_query2:
                cur.execute(query)
        conn.commit()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('outpath')
    args = parser.parse_args()
    outpath = args.outpath

    logging.basicConfig(
        filename=os.path.join(outpath, 'pmid_text_refs.log'),
        filemode='a',
        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
        datefmt='%m-%d %H:%M',
        level=logging.DEBUG,
        force=True,
    )
    logger = logging.getLogger(__name__)

    csv_path = os.path.join(outpath, 'pmid_text_refs.csv')
    db_path = os.path.join(outpath, 'pmid_text_refs.db')

    if 'pmid_text_refs' not in get_sqlite_tables(db_path):
        logger.info("Dumping pmid to text_ref map to csv.")
        pmid_text_refs_to_csv(csv_path)
        logger.info("Constructing pmid text_refs table.")
        create_pmid_text_ref_table(csv_path, db_path)
        logger.info("Removing csv file.")
        os.remove(csv_path)
