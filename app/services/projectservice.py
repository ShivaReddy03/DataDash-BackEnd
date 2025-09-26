from typing import Optional, List
from ..configuration.database import get_cursor
from ..models.projectmodels import ProjectData, CreateProjectRequest, UpdateProjectRequest, ProjectOption
import json

class ProjectService:
    
    # WRITE OPERATIONS
    @staticmethod
    async def create_project(request: CreateProjectRequest) -> ProjectData:
        """Create new project"""
        
        # Validate unit numbers
        if request.total_units != (request.available_units + request.sold_units + request.reserved_units):
            raise ValueError("Total units must equal sum of available, sold, and reserved units")
        
        # Validate rental income logic
        if request.property_type in ['plot', 'land'] and request.has_rental_income:
            raise ValueError("Plot and land properties cannot have rental income")
        
        async with get_cursor() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    INSERT INTO projects (
                        title, location, description, long_description, website_url,
                        status, base_price, property_type, has_rental_income,
                        pricing_details, total_units, available_units, sold_units,
                        reserved_units, rera_number, building_permission,
                        quick_info, gallery_images, key_highlights, features,
                        investment_highlights, amenities
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    RETURNING id, title, location, description, long_description, website_url,
                             status, base_price, property_type, has_rental_income,
                             pricing_details, total_units, available_units, sold_units,
                             reserved_units, rera_number, building_permission,
                             quick_info, gallery_images, key_highlights, features,
                             investment_highlights, amenities, created_at, updated_at, is_active
                """, (
                    request.title, request.location, request.description, request.long_description,
                    str(request.website_url) if request.website_url else None,
                    request.status, request.base_price, request.property_type, request.has_rental_income,
                    json.dumps(request.pricing_details) if request.pricing_details else None,
                    request.total_units, request.available_units, request.sold_units, request.reserved_units,
                    request.rera_number, request.building_permission,
                    json.dumps(request.quick_info) if request.quick_info else None,
                    json.dumps(request.gallery_images) if request.gallery_images else None,
                    json.dumps(request.key_highlights) if request.key_highlights else None,
                    json.dumps(request.features) if request.features else None,
                    json.dumps(request.investment_highlights) if request.investment_highlights else None,
                    json.dumps(request.amenities) if request.amenities else None
                ))
                row = await cur.fetchone()
                await conn.commit()
                
                return ProjectService._row_to_project_data(row)
    
    @staticmethod
    async def update_project(project_id: str, request: UpdateProjectRequest) -> Optional[ProjectData]:
        """Update project - handles all types of updates"""
        async with get_cursor() as conn:
            async with conn.cursor() as cur:
                # Check if project exists
                await cur.execute("SELECT id FROM projects WHERE id = %s", (project_id,))
                if not await cur.fetchone():
                    return None
                
                # Build update query dynamically
                update_fields = []
                params = []
                
                # Basic fields
                if request.title is not None:
                    update_fields.append("title = %s")
                    params.append(request.title)
                
                if request.location is not None:
                    update_fields.append("location = %s")
                    params.append(request.location)
                
                if request.description is not None:
                    update_fields.append("description = %s")
                    params.append(request.description)
                
                if request.long_description is not None:
                    update_fields.append("long_description = %s")
                    params.append(request.long_description)
                
                if request.website_url is not None:
                    update_fields.append("website_url = %s")
                    params.append(str(request.website_url) if request.website_url else None)
                
                if request.status is not None:
                    update_fields.append("status = %s")
                    params.append(request.status)
                
                if request.base_price is not None:
                    update_fields.append("base_price = %s")
                    params.append(request.base_price)
                
                if request.property_type is not None:
                    update_fields.append("property_type = %s")
                    params.append(request.property_type)
                
                if request.has_rental_income is not None:
                    # Validate rental income logic
                    if request.property_type in ['plot', 'land'] and request.has_rental_income:
                        raise ValueError("Plot and land properties cannot have rental income")
                    update_fields.append("has_rental_income = %s")
                    params.append(request.has_rental_income)
                
                # JSON fields
                if request.pricing_details is not None:
                    update_fields.append("pricing_details = %s")
                    params.append(json.dumps(request.pricing_details) if request.pricing_details else None)
                
                if request.quick_info is not None:
                    update_fields.append("quick_info = %s")
                    params.append(json.dumps(request.quick_info) if request.quick_info else None)
                
                if request.gallery_images is not None:
                    update_fields.append("gallery_images = %s")
                    params.append(json.dumps(request.gallery_images) if request.gallery_images else None)
                
                if request.key_highlights is not None:
                    update_fields.append("key_highlights = %s")
                    params.append(json.dumps(request.key_highlights) if request.key_highlights else None)
                
                if request.features is not None:
                    update_fields.append("features = %s")
                    params.append(json.dumps(request.features) if request.features else None)
                
                if request.investment_highlights is not None:
                    update_fields.append("investment_highlights = %s")
                    params.append(json.dumps(request.investment_highlights) if request.investment_highlights else None)
                
                if request.amenities is not None:
                    update_fields.append("amenities = %s")
                    params.append(json.dumps(request.amenities) if request.amenities else None)
                
                # Legal fields
                if request.rera_number is not None:
                    update_fields.append("rera_number = %s")
                    params.append(request.rera_number)
                
                if request.building_permission is not None:
                    update_fields.append("building_permission = %s")
                    params.append(request.building_permission)
                
                # Unit inventory - validate if provided
                if (request.total_units is not None or 
                    request.available_units is not None or 
                    request.sold_units is not None or 
                    request.reserved_units is not None):
                    
                    # Get current values if not all provided
                    if not all(x is not None for x in [request.total_units, request.available_units, 
                                                      request.sold_units, request.reserved_units]):
                        await cur.execute("""
                            SELECT total_units, available_units, sold_units, reserved_units 
                            FROM projects WHERE id = %s
                        """, (project_id,))
                        current = await cur.fetchone()
                        
                        total = request.total_units if request.total_units is not None else current[0]
                        available = request.available_units if request.available_units is not None else current[1]
                        sold = request.sold_units if request.sold_units is not None else current[2]
                        reserved = request.reserved_units if request.reserved_units is not None else current[3]
                    else:
                        total = request.total_units
                        available = request.available_units
                        sold = request.sold_units
                        reserved = request.reserved_units
                    
                    # Validate unit numbers
                    if total != (available + sold + reserved):
                        raise ValueError("Total units must equal sum of available, sold, and reserved units")
                    
                    if request.total_units is not None:
                        update_fields.append("total_units = %s")
                        params.append(request.total_units)
                    
                    if request.available_units is not None:
                        update_fields.append("available_units = %s")
                        params.append(request.available_units)
                    
                    if request.sold_units is not None:
                        update_fields.append("sold_units = %s")
                        params.append(request.sold_units)
                    
                    if request.reserved_units is not None:
                        update_fields.append("reserved_units = %s")
                        params.append(request.reserved_units)
                
                # Active status
                if request.is_active is not None:
                    update_fields.append("is_active = %s")
                    params.append(request.is_active)
                
                if not update_fields:
                    # No updates needed, just return current project
                    await cur.execute("""
                        SELECT id, title, location, description, long_description, website_url,
                               status, base_price, property_type, has_rental_income,
                               pricing_details, total_units, available_units, sold_units,
                               reserved_units, rera_number, building_permission,
                               quick_info, gallery_images, key_highlights, features,
                               investment_highlights, amenities, created_at, updated_at, is_active
                        FROM projects WHERE id = %s
                    """, (project_id,))
                    row = await cur.fetchone()
                    return ProjectService._row_to_project_data(row)
                
                # Add updated_at and project_id
                update_fields.append("updated_at = CURRENT_TIMESTAMP")
                params.append(project_id)
                
                query = f"""
                    UPDATE projects 
                    SET {', '.join(update_fields)}
                    WHERE id = %s
                    RETURNING id, title, location, description, long_description, website_url,
                             status, base_price, property_type, has_rental_income,
                             pricing_details, total_units, available_units, sold_units,
                             reserved_units, rera_number, building_permission,
                             quick_info, gallery_images, key_highlights, features,
                             investment_highlights, amenities, created_at, updated_at, is_active
                """
                
                await cur.execute(query, params)
                row = await cur.fetchone()
                await conn.commit()
                
                return ProjectService._row_to_project_data(row)
    
    # # READ OPERATIONS - Only show projects where is_active = true
    # @staticmethod
    # async def list_projects(
    #     limit: int = 20,
    #     offset: int = 0,
    #     property_type: Optional[str] = None,
    #     status_filter: Optional[str] = None,
    #     min_price: Optional[float] = None,
    #     max_price: Optional[float] = None
    # ) -> tuple[List[ProjectData], int]:
    #     """Return projects and total count for pagination"""
    #     async with get_cursor() as conn:
    #         async with conn.cursor() as cur:
    #             # Build WHERE clause
    #             where_conditions = ["is_active = true"]
    #             params = []
                
    #             if property_type:
    #                 where_conditions.append("property_type = %s")
    #                 params.append(property_type)
    #             if status_filter:
    #                 where_conditions.append("status = %s")
    #                 params.append(status_filter)
    #             if min_price is not None:
    #                 where_conditions.append("base_price >= %s")
    #                 params.append(min_price)
    #             if max_price is not None:
    #                 where_conditions.append("base_price <= %s")
    #                 params.append(max_price)
                
    #             where_clause = " AND ".join(where_conditions)
                
    #             # Total count
    #             count_query = f"SELECT COUNT(*) FROM projects WHERE {where_clause}"
    #             await cur.execute(count_query, params)
    #             total_projects = (await cur.fetchone())[0]
                
    #             # Add pagination
    #             params.extend([limit, offset])
    #             query = f"""
    #                 SELECT id, title, location, description, long_description, website_url,
    #                        status, base_price, property_type, has_rental_income,
    #                        pricing_details, total_units, available_units, sold_units,
    #                        reserved_units, rera_number, building_permission,
    #                        quick_info, gallery_images, key_highlights, features,
    #                        investment_highlights, amenities, created_at, updated_at, is_active
    #                 FROM projects
    #                 WHERE {where_clause}
    #                 ORDER BY created_at DESC
    #                 LIMIT %s OFFSET %s
    #             """
    #             await cur.execute(query, params)
    #             rows = await cur.fetchall()
                
    #             projects = [ProjectService._row_to_project_data(row) for row in rows]
    #             return projects, total_projects

    @staticmethod
    async def list_projects(
        page: int = 1,
        limit: int = 20,
        property_type: Optional[str] = None,
        status_filter: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None
    ) -> tuple[List[ProjectData], int]:
        """Return projects and total count for pagination"""
        offset = (page - 1) * limit  # calculate offset from page

        async with get_cursor() as conn:
            async with conn.cursor() as cur:
                where_conditions = ["is_active = true"]
                params = []

                if property_type:
                    where_conditions.append("property_type = %s")
                    params.append(property_type)
                if status_filter:
                    where_conditions.append("status = %s")
                    params.append(status_filter)
                if min_price is not None:
                    where_conditions.append("base_price >= %s")
                    params.append(min_price)
                if max_price is not None:
                    where_conditions.append("base_price <= %s")
                    params.append(max_price)

                where_clause = " AND ".join(where_conditions)

                # Total count
                count_query = f"SELECT COUNT(*) FROM projects WHERE {where_clause}"
                await cur.execute(count_query, params)
                total_projects = (await cur.fetchone())[0]

                # Pagination
                params.extend([limit, offset])
                query = f"""
                    SELECT id, title, location, description, long_description, website_url,
                           status, base_price, property_type, has_rental_income,
                           pricing_details, total_units, available_units, sold_units,
                           reserved_units, rera_number, building_permission,
                           quick_info, gallery_images, key_highlights, features,
                           investment_highlights, amenities, created_at, updated_at, is_active
                    FROM projects
                    WHERE {where_clause}
                    ORDER BY created_at DESC
                    LIMIT %s OFFSET %s
                """
                await cur.execute(query, params)
                rows = await cur.fetchall()

                projects = [ProjectService._row_to_project_data(row) for row in rows]
                return projects, total_projects


    @staticmethod
    async def get_project_by_id(project_id: str) -> Optional[ProjectData]:
        """Get single project by ID - Only if active"""
        async with get_cursor() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    SELECT id, title, location, description, long_description, website_url,
                           status, base_price, property_type, has_rental_income,
                           pricing_details, total_units, available_units, sold_units,
                           reserved_units, rera_number, building_permission,
                           quick_info, gallery_images, key_highlights, features,
                           investment_highlights, amenities, created_at, updated_at, is_active
                    FROM projects
                    WHERE id = %s AND is_active = true
                """, (project_id,))
                row = await cur.fetchone()
                
                if not row:
                    return None
                
                return ProjectService._row_to_project_data(row)
    
    @staticmethod
    async def get_projects_by_property_type(
        property_type: str,
        limit: int = 20,
        offset: int = 0
    ) -> List[ProjectData]:
        """Filter projects by property type - Only active projects"""
        async with get_cursor() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    SELECT id, title, location, description, long_description, website_url,
                           status, base_price, property_type, has_rental_income,
                           pricing_details, total_units, available_units, sold_units,
                           reserved_units, rera_number, building_permission,
                           quick_info, gallery_images, key_highlights, features,
                           investment_highlights, amenities, created_at, updated_at, is_active
                    FROM projects
                    WHERE property_type = %s AND is_active = true
                    ORDER BY created_at DESC
                    LIMIT %s OFFSET %s
                """, (property_type, limit, offset))
                rows = await cur.fetchall()
                
                return [ProjectService._row_to_project_data(row) for row in rows]
    
    @staticmethod
    async def get_available_projects(
        limit: int = 20,
        offset: int = 0
    ) -> List[ProjectData]:
        """Get only available projects - Only active projects"""
        async with get_cursor() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    SELECT id, title, location, description, long_description, website_url,
                           status, base_price, property_type, has_rental_income,
                           pricing_details, total_units, available_units, sold_units,
                           reserved_units, rera_number, building_permission,
                           quick_info, gallery_images, key_highlights, features,
                           investment_highlights, amenities, created_at, updated_at, is_active
                    FROM projects
                    WHERE status = 'available' AND is_active = true
                    ORDER BY created_at DESC
                    LIMIT %s OFFSET %s
                """, (limit, offset))
                rows = await cur.fetchall()
                
                return [ProjectService._row_to_project_data(row) for row in rows]
    
    @staticmethod
    async def search_projects(
        search_term: str,
        limit: int = 20,
        offset: int = 0
    ) -> List[ProjectData]:
        """Search projects - Only active projects"""
        async with get_cursor() as conn:
            async with conn.cursor() as cur:
                search_pattern = f"%{search_term}%"
                await cur.execute("""
                    SELECT id, title, location, description, long_description, website_url,
                           status, base_price, property_type, has_rental_income,
                           pricing_details, total_units, available_units, sold_units,
                           reserved_units, rera_number, building_permission,
                           quick_info, gallery_images, key_highlights, features,
                           investment_highlights, amenities, created_at, updated_at, is_active
                    FROM projects
                    WHERE (
                        title ILIKE %s OR 
                        location ILIKE %s OR 
                        description ILIKE %s OR
                        long_description ILIKE %s
                    ) AND is_active = true
                    ORDER BY created_at DESC
                    LIMIT %s OFFSET %s
                """, (search_pattern, search_pattern, search_pattern, search_pattern, limit, offset))
                rows = await cur.fetchall()
                
                return [ProjectService._row_to_project_data(row) for row in rows]
    
    # UTILITY METHOD
    @staticmethod
    def _row_to_project_data(row) -> ProjectData:
        """Convert database row to ProjectData model"""
        return ProjectData(
            id=str(row[0]),
            title=row[1],
            location=row[2],
            description=row[3],
            long_description=row[4],
            website_url=row[5],
            status=row[6],
            base_price=float(row[7]),
            property_type=row[8],
            has_rental_income=row[9],
            pricing_details=row[10],
            total_units=row[11],
            available_units=row[12],
            sold_units=row[13],
            reserved_units=row[14],
            rera_number=row[15],
            building_permission=row[16],
            quick_info=row[17],
            gallery_images=row[18],
            key_highlights=row[19],
            features=row[20],
            investment_highlights=row[21],
            amenities=row[22],
            created_at=row[23],
            updated_at=row[24],
            is_active=row[25]
        )
    
    @staticmethod
    async def get_project_options() -> List[ProjectOption]:
        """Fetch only project id and title for dropdowns"""
        async with get_cursor() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    SELECT id, title
                    FROM projects
                    WHERE is_active = true
                    ORDER BY title ASC
                """)
                rows = await cur.fetchall()

                return [ProjectOption(id=row[0], title=row[1]) for row in rows]