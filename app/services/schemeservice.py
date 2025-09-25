from typing import Optional, List
from ..configuration.database import get_cursor
from ..models.schememodels import InvestmentSchemeData, CreateInvestmentSchemeRequest, UpdateInvestmentSchemeRequest

class InvestmentSchemeService:
    
    # WRITE OPERATIONS
    @staticmethod
    async def create_scheme(request: CreateInvestmentSchemeRequest) -> InvestmentSchemeData:
        """Create new investment scheme"""
        
        async with get_cursor() as conn:
            async with conn.cursor() as cur:
                # Validate project exists and get its properties
                await cur.execute("""
                    SELECT property_type, has_rental_income
                    FROM projects
                    WHERE id = %s AND is_active = true
                """, (request.project_id,))
                project = await cur.fetchone()
                
                if not project:
                    raise ValueError("Project not found or inactive")
                
                # Validate rental start month logic
                if request.rental_start_month is not None:
                    if not project[1]:  # has_rental_income
                        raise ValueError("Rental start month can only be set for projects with rental income")
                
                # Validate scheme type specific fields
                if request.scheme_type == 'single_payment':
                    if request.total_installments is not None:
                        raise ValueError("Single payment schemes cannot have installments")
                    if request.monthly_installment_amount is not None:
                        raise ValueError("Single payment schemes cannot have monthly installment amount")
                
                elif request.scheme_type == 'installment':
                    if not request.total_installments or request.total_installments <= 0:
                        raise ValueError("Installment schemes must have valid total_installments")
                    if not request.monthly_installment_amount or request.monthly_installment_amount <= 0:
                        raise ValueError("Installment schemes must have valid monthly_installment_amount")
                    if request.balance_payment_days is not None:
                        raise ValueError("Installment schemes cannot have balance_payment_days")
                
                # Insert the scheme
                await cur.execute("""
                    INSERT INTO investment_schemes (
                        project_id, scheme_type, scheme_name, area_sqft,
                        booking_advance, balance_payment_days, total_installments,
                        monthly_installment_amount, rental_start_month,
                        start_date, end_date, is_active
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    RETURNING id, project_id, scheme_type, scheme_name, area_sqft,
                             booking_advance, balance_payment_days, total_installments,
                             monthly_installment_amount, rental_start_month,
                             start_date, end_date, is_active, created_at, updated_at
                """, (
                    request.project_id, request.scheme_type, request.scheme_name, request.area_sqft,
                    request.booking_advance, request.balance_payment_days, request.total_installments,
                    request.monthly_installment_amount, request.rental_start_month,
                    request.start_date, request.end_date, request.is_active
                ))
                row = await cur.fetchone()
                await conn.commit()
                
                return InvestmentSchemeService._row_to_scheme_data(row)
    
    @staticmethod
    async def update_scheme(scheme_id: str, request: UpdateInvestmentSchemeRequest) -> Optional[InvestmentSchemeData]:
        """Update investment scheme"""
        async with get_cursor() as conn:
            async with conn.cursor() as cur:
                # Check if scheme exists
                await cur.execute("SELECT id, project_id FROM investment_schemes WHERE id = %s", (scheme_id,))
                existing = await cur.fetchone()
                
                if not existing:
                    return None
                
                # Get project info for validation
                await cur.execute("""
                    SELECT property_type, has_rental_income
                    FROM projects
                    WHERE id = %s AND is_active = true
                """, (existing[1],))  # project_id
                project = await cur.fetchone()
                
                if not project:
                    raise ValueError("Associated project not found or inactive")
                
                # Build update query dynamically
                update_fields = []
                params = []
                
                if request.scheme_name is not None:
                    update_fields.append("scheme_name = %s")
                    params.append(request.scheme_name)
                
                if request.area_sqft is not None:
                    update_fields.append("area_sqft = %s")
                    params.append(request.area_sqft)
                
                if request.booking_advance is not None:
                    update_fields.append("booking_advance = %s")
                    params.append(request.booking_advance)
                
                if request.balance_payment_days is not None:
                    update_fields.append("balance_payment_days = %s")
                    params.append(request.balance_payment_days)
                
                if request.total_installments is not None:
                    update_fields.append("total_installments = %s")
                    params.append(request.total_installments)
                
                if request.monthly_installment_amount is not None:
                    update_fields.append("monthly_installment_amount = %s")
                    params.append(request.monthly_installment_amount)
                
                if request.rental_start_month is not None:
                    if not project[1]:  # has_rental_income
                        raise ValueError("Rental start month can only be set for projects with rental income")
                    update_fields.append("rental_start_month = %s")
                    params.append(request.rental_start_month)
                
                if request.start_date is not None:
                    update_fields.append("start_date = %s")
                    params.append(request.start_date)
                
                if request.end_date is not None:
                    update_fields.append("end_date = %s")
                    params.append(request.end_date)
                
                if request.is_active is not None:
                    update_fields.append("is_active = %s")
                    params.append(request.is_active)
                
                if not update_fields:
                    # No updates needed, just return current scheme
                    await cur.execute("""
                        SELECT id, project_id, scheme_type, scheme_name, area_sqft,
                               booking_advance, balance_payment_days, total_installments,
                               monthly_installment_amount, rental_start_month,
                               start_date, end_date, is_active, created_at, updated_at
                        FROM investment_schemes WHERE id = %s
                    """, (scheme_id,))
                    row = await cur.fetchone()
                    return InvestmentSchemeService._row_to_scheme_data(row)
                
                # Add updated_at and scheme_id
                update_fields.append("updated_at = CURRENT_TIMESTAMP")
                params.append(scheme_id)
                
                query = f"""
                    UPDATE investment_schemes 
                    SET {', '.join(update_fields)}
                    WHERE id = %s
                    RETURNING id, project_id, scheme_type, scheme_name, area_sqft,
                             booking_advance, balance_payment_days, total_installments,
                             monthly_installment_amount, rental_start_month,
                             start_date, end_date, is_active, created_at, updated_at
                """
                
                await cur.execute(query, params)
                row = await cur.fetchone()
                await conn.commit()
                
                return InvestmentSchemeService._row_to_scheme_data(row)
    
    # READ OPERATIONS
    @staticmethod
    async def get_all_schemes(
        project_id: Optional[str] = None,
        scheme_type: Optional[str] = None,
        is_active: Optional[bool] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[InvestmentSchemeData]:
        """Get all investment schemes with optional filters"""
        
        async with get_cursor() as conn:
            async with conn.cursor() as cur:
                # Build dynamic WHERE clause - always filter by is_active = true unless explicitly requested
                where_conditions = []
                params = []
                
                if project_id:
                    where_conditions.append("project_id = %s")
                    params.append(project_id)
                
                if scheme_type:
                    where_conditions.append("scheme_type = %s")
                    params.append(scheme_type)
                
                # Default to showing only active schemes
                if is_active is None:
                    where_conditions.append("is_active = true")
                else:
                    where_conditions.append("is_active = %s")
                    params.append(is_active)
                
                # Add limit and offset
                params.extend([limit, offset])
                
                where_clause = " AND ".join(where_conditions) if where_conditions else "is_active = true"
                query = f"""
                    SELECT id, project_id, scheme_type, scheme_name, area_sqft,
                           booking_advance, balance_payment_days, total_installments,
                           monthly_installment_amount, rental_start_month,
                           start_date, end_date, is_active, created_at, updated_at
                    FROM investment_schemes
                    WHERE {where_clause}
                    ORDER BY created_at DESC
                    LIMIT %s OFFSET %s
                """
                
                await cur.execute(query, params)
                rows = await cur.fetchall()
                
                return [InvestmentSchemeService._row_to_scheme_data(row) for row in rows]
    
    @staticmethod
    async def get_scheme_by_id(scheme_id: str) -> Optional[InvestmentSchemeData]:
        """Get specific investment scheme by ID (only active schemes)"""
        async with get_cursor() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    SELECT id, project_id, scheme_type, scheme_name, area_sqft,
                           booking_advance, balance_payment_days, total_installments,
                           monthly_installment_amount, rental_start_month,
                           start_date, end_date, is_active, created_at, updated_at
                    FROM investment_schemes
                    WHERE id = %s AND is_active = true
                """, (scheme_id,))
                row = await cur.fetchone()
                
                if not row:
                    return None
                
                return InvestmentSchemeService._row_to_scheme_data(row)
    
    @staticmethod
    async def get_schemes_by_project(
        project_id: str,
        scheme_type: Optional[str] = None,
        is_active: Optional[bool] = True,
        page: int = 1,
        limit: int = 20
    ) -> tuple[List[InvestmentSchemeData], int]:
        """Get investment schemes for a specific project with pagination"""
        offset = (page - 1) * limit  # calculate offset from page
        
        async with get_cursor() as conn:
            async with conn.cursor() as cur:
                where_conditions = ["project_id = %s"]
                params = [project_id]
                
                if scheme_type:
                    where_conditions.append("scheme_type = %s")
                    params.append(scheme_type)
                if is_active is not None:
                    where_conditions.append("is_active = %s")
                    params.append(is_active)
                
                where_clause = " AND ".join(where_conditions)
                
                # Get total count
                count_query = f"SELECT COUNT(*) FROM investment_schemes WHERE {where_clause}"
                await cur.execute(count_query, params)
                total_schemes = (await cur.fetchone())[0]
                
                # Add limit and offset
                params.extend([limit, offset])
                query = f"""
                    SELECT id, project_id, scheme_type, scheme_name, area_sqft,
                           booking_advance, balance_payment_days, total_installments,
                           monthly_installment_amount, rental_start_month,
                           start_date, end_date, is_active, created_at, updated_at
                    FROM investment_schemes
                    WHERE {where_clause}
                    ORDER BY scheme_type, area_sqft
                    LIMIT %s OFFSET %s
                """
                await cur.execute(query, params)
                rows = await cur.fetchall()
                
                schemes = [InvestmentSchemeService._row_to_scheme_data(row) for row in rows]
                return schemes, total_schemes
    
    # UTILITY METHOD
    @staticmethod
    def _row_to_scheme_data(row) -> InvestmentSchemeData:
        """Convert database row to InvestmentSchemeData model"""
        return InvestmentSchemeData(
            id=str(row[0]),
            project_id=str(row[1]),
            scheme_type=row[2],
            scheme_name=row[3],
            area_sqft=row[4],
            booking_advance=float(row[5]) if row[5] else None,
            balance_payment_days=row[6],
            total_installments=row[7],
            monthly_installment_amount=float(row[8]) if row[8] else None,
            rental_start_month=row[9],
            start_date=row[10],
            end_date=row[11],
            is_active=row[12],
            created_at=row[13],
            updated_at=row[14]
        )