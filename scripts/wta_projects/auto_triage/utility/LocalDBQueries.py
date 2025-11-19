import sqlite3
import os
import glob

def delete_all_execution_status_dbs():
    """
    Deletes all SQLite database files matching the pattern 'ececution_status_*.db' in the current directory.
    """
    pattern = "execution_status_*.db"
    files = glob.glob(pattern) 

    if not files:
        return

    for file in files:
        try:
            os.remove(file)
        except Exception as e:
            print(f"Error deleting {file}: {e}")

            

def check_and_create_db(db_name, bundle):
    """
    Ensures the SQLite database and table exist. Inserts a new bundle with status=0
    only if it does not already exist.
    
    :param db_name: Name of the SQLite database file
    :param bundle: Name of the bundle to insert
    """
    
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bundles_ready_for_triaging (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bundle_name TEXT NOT NULL UNIQUE,  
            status INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Check if the bundle already exists
    cursor.execute("SELECT id FROM bundles_ready_for_triaging WHERE bundle_name = ?", (bundle,))
    existing_bundle = cursor.fetchone()

    if not existing_bundle:
        cursor.execute("INSERT INTO bundles_ready_for_triaging (bundle_name, status) VALUES (?, ?)", (bundle, 0))
        conn.commit()
        print(f"Inserted bundle '{bundle}' with status 0.")

    conn.close()



def check_bundle_exists(db_name, bundle_name):
    """
    Ensures the table exists before checking if a specific bundle_name exists.

    :param db_name: Name of the SQLite database file.
    :param bundle_name: The name of the bundle to check.
    :return: True if the bundle exists, False otherwise.
    """
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    # Ensure the table exists before querying
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bundles_ready_for_triaging (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bundle_name TEXT NOT NULL UNIQUE,
            status INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Use parameterized query to prevent SQL injection
    cursor.execute("""
        SELECT EXISTS(
            SELECT 1 FROM bundles_ready_for_triaging WHERE bundle_name = ?
        )
    """, (bundle_name,))
    
    result = cursor.fetchone()[0]

    conn.close()
    return bool(result)



def increment_status(db_name, bundle_name):
    """
    Increments the status of a specific bundle in the 'bundles_ready_for_triaging' table.

    :param db_name: Name of the SQLite database file.
    :param bundle_name: The bundle whose status should be incremented.
    :return: The new status after incrementing, or None if the bundle does not exist.
    """
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    # Ensure table exists
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bundles_ready_for_triaging (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bundle_name TEXT NOT NULL UNIQUE,
            status INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Fetch current status of the bundle
    cursor.execute("""
        SELECT id, status FROM bundles_ready_for_triaging 
        WHERE bundle_name = ?
    """, (bundle_name,))
    
    row = cursor.fetchone()

    if row:
        row_id, current_status = row
        new_status = current_status + 1

        # Update the status in the database
        cursor.execute("""
            UPDATE bundles_ready_for_triaging
            SET status = ?
            WHERE id = ?
        """, (new_status, row_id))

        conn.commit()
        conn.close()

        print(f"Updated status to {new_status} for bundle '{bundle_name}' (ID: {row_id})")
        return new_status
    else:
        print(f"Bundle '{bundle_name}' not found in the database.")
        check_and_create_db(db_name, bundle_name)
        increment_status(db_name, bundle_name)
        conn.close()
        return None




def is_bundle_status_greater_than_threshold(db_name, bundle_name, check_threshold=1):
    """
    Checks if the status of a specific bundle is greater than 4.

    :param db_name: Name of the SQLite database file.
    :param bundle_name: The bundle whose status needs to be checked.
    :return: True if status > 4, False otherwise.
    """
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    # Ensure the table exists before querying
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bundles_ready_for_triaging (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bundle_name TEXT NOT NULL UNIQUE,
            status INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Fetch the current status of the bundle
    cursor.execute("""
        SELECT status FROM bundles_ready_for_triaging 
        WHERE bundle_name = ?
    """, (bundle_name,))
    
    row = cursor.fetchone()
    conn.close()

    if row and row[0] > check_threshold:
        return True
    return False


