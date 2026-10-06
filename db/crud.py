def create_set(connection,name):
    cursor=connection.cursor()
    cursor.execute("""
            INSERT INTO sets(name,created_at)
            VALUES (?,datetime('now'))""",
                   (name,))
    set_id=cursor.lastrowid
    connection.commit()
    return set_id

def list_sets(connection):
    cursor=connection.cursor()
    cursor.execute("""
            SELECT id, name, created_at
            FROM sets
            ORDER BY id
""")
    rows=cursor.fetchall()
    return rows
def add_message(connection,set_id,role,content):
    cursor=connection.cursor()
    cursor.execute("""
            INSERT INTO messages(set_id,role,content,timestamp)
            VALUES (?,?,?,datetime('now'))""",
            (set_id,role,content))

    connection.commit()

def get_latest_messages(connection,set_id,n):
    cursor=connection.cursor()
    cursor.execute("""
            SELECT role,content FROM messages 
            WHERE set_id=? 
            ORDER BY id DESC LIMIT ?""",
            (set_id,n))
    
    rows=cursor.fetchall()
    return list(reversed(rows))

def get_message_count(connection,set_id):
    cursor=connection.cursor()
    cursor.execute("""
            SELECT COUNT(*) 
            FROM messages 
            WHERE set_id=?""",
            (set_id,))
    
    return cursor.fetchone()[0]

def delete_oldest_messages(connection, set_id, count):
    cursor = connection.cursor()

    cursor.execute("""
        DELETE FROM messages
        WHERE id IN (
            SELECT id
            FROM messages
            WHERE set_id = ?
            ORDER BY id ASC
            LIMIT ?)""", 
        (set_id, count))

    connection.commit()

def get_oldest_messages(connection, set_id, count) -> list:
    cursor=connection.cursor()

    cursor.execute("""
        SELECT role,content 
        FROM messages
        WHERE set_id=?
        ORDER BY id ASC
        LIMIT ?"""
        ,(set_id,count))

    return cursor.fetchall()

def add_knowledges(connection,set_id,url_name,source_url,chunk_count):
    cursor=connection.cursor()
    cursor.execute("""
            INSERT INTO knowledge_bases(set_id,url_name,source_url,chunk_count,uploaded_at)
            VALUES (?,?,?,?,datetime('now'))""",
                   (set_id,url_name,source_url,chunk_count)
    )

    connection.commit()

def list_knowledges(connection,set_id):
    cursor=connection.cursor()
    cursor.execute("""
            SELECT url_name,source_url,chunk_count,uploaded_at FROM knowledge_bases
            WHERE set_id=?
            ORDER BY id""",
            (set_id,)
    )
    rows=cursor.fetchall()
    return rows

def delete_messages_by_set(connection, set_id):
    cursor=connection.cursor()
    cursor.execute("""
            DELETE FROM messages
            WHERE set_id=?""",
            (set_id,))
    connection.commit()

def delete_knowledge_by_set(connection, set_id):
    cursor=connection.cursor()
    cursor.execute("""
            DELETE FROM knowledge_bases
            WHERE set_id=?""",
            (set_id,))

    connection.commit()

def delete_set(connection,set_id):
    cursor=connection.cursor()
    cursor.execute("""
            DELETE FROM sets
            WHERE id=?""",
            (set_id,))
    
    connection.commit()
