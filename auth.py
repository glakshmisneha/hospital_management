from database import get_connection

def register_user(name, email, password, role):
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (name,email,password,role) VALUES (?,?,?,?)",
                  (name,email,password,role))
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()

def login_user(email, password):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE email=? AND password=?", (email,password))
    user = c.fetchone()
    conn.close()
    return user
