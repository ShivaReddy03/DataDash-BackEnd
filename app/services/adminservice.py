from typing import Optional, List
from ..configuration.database import get_cursor
from ..models.adminmodels import AdminData
import bcrypt
import jwt
import os
from datetime import datetime, timedelta

class AdminService:
    
    # UTILITY METHODS
    @staticmethod
    def _hash_password(password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    @staticmethod
    def _verify_password(password: str, hashed: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    @staticmethod
    def _generate_token(admin_id: str) -> str:
        """Generate JWT token"""
        payload = {
            'admin_id': admin_id,
            'exp': datetime.utcnow() + timedelta(days=7)  # Token expires in 7 days
        }
        return jwt.encode(payload, os.getenv("JWT_SECRET", "ramyaconstructions"), algorithm="HS256")
    
    # WRITE OPERATIONS
    @staticmethod
    async def get_admin_count() -> int:
        """Get total number of admins"""
        async with get_cursor() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT COUNT(*) FROM admin_credentials")
                result = await cur.fetchone()
                return result[0]
    
    @staticmethod
    async def authenticate_admin(email: str, password: str) -> Optional[dict]:
        """Authenticate admin and return token"""
        async with get_cursor() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    SELECT id, name, email, password
                    FROM admin_credentials
                    WHERE email = %s
                """, (email,))
                row = await cur.fetchone()
                
                if not row or not AdminService._verify_password(password, row[3]):
                    return None
                
                token = AdminService._generate_token(str(row[0]))
                
                return {
                    'token': token,
                    'admin': {
                        'id': str(row[0]),
                        'name': row[1],
                        'email': row[2]
                    }
                }
    
    @staticmethod
    async def create_admin(name: str, email: str, password: str) -> AdminData:
        """Create new admin"""
        async with get_cursor() as conn:
            async with conn.cursor() as cur:
                # Check if email already exists
                await cur.execute("""
                    SELECT id FROM admin_credentials WHERE email = %s
                """, (email,))
                existing = await cur.fetchone()
                
                if existing:
                    raise ValueError("Email already exists")
                
                # Hash password and insert
                hashed_password = AdminService._hash_password(password)
                
                await cur.execute("""
                    INSERT INTO admin_credentials (name, email, password)
                    VALUES (%s, %s, %s)
                    RETURNING id, name, email, created_at, updated_at
                """, (name, email, hashed_password))
                row = await cur.fetchone()
                
                await conn.commit()
                
                return AdminData(
                    id=str(row[0]),
                    name=row[1],
                    email=row[2],
                    created_at=row[3],
                    updated_at=row[4]
                )
    
    @staticmethod
    async def update_admin(admin_id: str, name: Optional[str] = None, email: Optional[str] = None, password: Optional[str] = None) -> Optional[AdminData]:
        """Update admin name, email and/or password"""
        async with get_cursor() as conn:
            async with conn.cursor() as cur:
                # Check if admin exists
                await cur.execute("""
                    SELECT id FROM admin_credentials WHERE id = %s
                """, (admin_id,))
                existing = await cur.fetchone()
                
                if not existing:
                    return None
                
                # Build update query dynamically
                update_fields = []
                params = []
                
                if name:
                    update_fields.append("name = %s")
                    params.append(name)
                
                if email:
                    # Check if new email already exists (for other admins)
                    await cur.execute("""
                        SELECT id FROM admin_credentials WHERE email = %s AND id != %s
                    """, (email, admin_id))
                    if await cur.fetchone():
                        raise ValueError("Email already exists")
                    
                    update_fields.append("email = %s")
                    params.append(email)
                
                if password:
                    hashed_password = AdminService._hash_password(password)
                    update_fields.append("password = %s")
                    params.append(hashed_password)
                
                if not update_fields:
                    # No updates needed, just return current admin
                    await cur.execute("""
                        SELECT id, name, email, created_at, updated_at
                        FROM admin_credentials WHERE id = %s
                    """, (admin_id,))
                    row = await cur.fetchone()
                    return AdminData(
                        id=str(row[0]),
                        name=row[1],
                        email=row[2],
                        created_at=row[3],
                        updated_at=row[4]
                    )
                
                update_fields.append("updated_at = CURRENT_TIMESTAMP")
                params.append(admin_id)
                
                query = f"""
                    UPDATE admin_credentials 
                    SET {', '.join(update_fields)}
                    WHERE id = %s
                    RETURNING id, name, email, created_at, updated_at
                """
                
                await cur.execute(query, params)
                row = await cur.fetchone()
                
                await conn.commit()
                
                return AdminData(
                    id=str(row[0]),
                    name=row[1],
                    email=row[2],
                    created_at=row[3],
                    updated_at=row[4]
                )
    
    @staticmethod
    async def delete_admin(admin_id: str) -> bool:
        """Delete admin"""
        async with get_cursor() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    DELETE FROM admin_credentials WHERE id = %s
                """, (admin_id,))
                
                deleted = cur.rowcount > 0
                await conn.commit()
                return deleted
    
    # READ OPERATIONS
    @staticmethod
    async def get_all_admins(page: int = 1, limit: int = 9) -> dict:
        """Retrieve all admin users with pagination"""
        async with get_cursor() as conn:
            async with conn.cursor() as cur:
                # Calculate offset
                offset = (page - 1) * limit
                
                # Get total count
                await cur.execute("SELECT COUNT(*) FROM admin_credentials")
                total_count = (await cur.fetchone())[0]
                
                # Get paginated results
                await cur.execute("""
                    SELECT id, name, email, created_at, updated_at
                    FROM admin_credentials
                    ORDER BY created_at DESC
                    LIMIT %s OFFSET %s
                """, (limit, offset))
                rows = await cur.fetchall()
                
                # Calculate total pages
                total_pages = (total_count + limit - 1) // limit
                
                admins = [
                    AdminData(
                        id=str(row[0]),
                        name=row[1],
                        email=row[2],
                        created_at=row[3],
                        updated_at=row[4]
                    )
                    for row in rows
                ]
                
                return {
                    'admins': admins,
                    'total': total_count,
                    'page': page,
                    'pages': total_pages
                }
    
    @staticmethod
    async def get_admin_by_id(admin_id: str) -> Optional[AdminData]:
        """Retrieve specific admin by ID"""
        async with get_cursor() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    SELECT id, name, email, created_at, updated_at
                    FROM admin_credentials
                    WHERE id = %s
                """, (admin_id,))
                row = await cur.fetchone()
                
                if not row:
                    return None
                    
                return AdminData(
                    id=str(row[0]),
                    name=row[1],
                    email=row[2],
                    created_at=row[3],
                    updated_at=row[4]
                )
    
    @staticmethod
    async def get_admin_by_email(email: str) -> Optional[dict]:
        """Retrieve admin by email (for authentication)"""
        async with get_cursor() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    SELECT id, name, email, password, created_at, updated_at
                    FROM admin_credentials
                    WHERE email = %s
                """, (email,))
                row = await cur.fetchone()
                
                if not row:
                    return None
                    
                return {
                    'id': str(row[0]),
                    'name': row[1],
                    'email': row[2],
                    'password': row[3],
                    'created_at': row[4],
                    'updated_at': row[5]
                }