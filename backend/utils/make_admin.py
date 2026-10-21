import argparse
from models.database import SessionLocal, User

def make_admin(email):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            print(f"Error: User with email {email} not found.")
            return
        
        user.role = "admin"
        db.commit()
        print(f"Success: User {email} is now an admin.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Grant admin role to a user by email.")
    parser.add_argument("--email", required=True, help="Email address of the user.")
    args = parser.parse_args()
    make_admin(args.email)
