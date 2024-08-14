# -*- coding: utf-8 -*-
"""The utility functions for AgentScope Studio."""
import os.path
import sqlite3


def _check_and_convert_id_type(db_path: str, table_name: str) -> None:
    """Check and convert the type of the 'id' column in the specified table
    from INTEGER to VARCHAR.

    Args:
        db_path (str): The path of the SQLite database file.
        table_name (str): The name of the table to be checked and converted.
    """

    if not os.path.exists(db_path):
        return

    # Connect to the SQLite database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Obtain the table structure information
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()

        # Look for the type of the 'id' column
        id_column = [col for col in columns if col[1] == "id"]
        if not id_column:
            return

        id_type = id_column[0][2].upper()
        if id_type in ["VARCHAR", "TEXT"]:
            return

        if id_type == "INTEGER":
            # Temporary table name
            temp_table_name = table_name + "_temp"

            # Create a new table and change the type of the 'id' column to
            # VARCHAR
            create_table_sql = f"CREATE TABLE {temp_table_name} ("
            for col in columns:
                col_type = "VARCHAR" if col[1] == "id" else col[2]
                create_table_sql += f"{col[1]} {col_type}, "
            create_table_sql = create_table_sql.rstrip(", ") + ");"

            cursor.execute(create_table_sql)

            # Copy data and convert the value of the 'id' column to a string
            column_names = ", ".join([col[1] for col in columns])
            column_values = ", ".join(
                [
                    f"CAST({col[1]} AS VARCHAR)" if col[1] == "id" else col[1]
                    for col in columns
                ],
            )
            cursor.execute(
                f"INSERT INTO {temp_table_name} ({column_names}) "
                f"SELECT {column_values} FROM {table_name};",
            )

            # Delete the old table
            cursor.execute(f"DROP TABLE {table_name};")

            # Rename the new table
            cursor.execute(
                f"ALTER TABLE {temp_table_name} RENAME TO {table_name};",
            )

            conn.commit()

    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
    finally:
        conn.close()
