"""
API Response Models
===================

Standardized API response models.
"""

class APIResponse:
    """Standard API response format"""
    
    @staticmethod
    def success(data=None, message="Success"):
        return {
            "success": True,
            "message": message,
            "data": data
        }
    
    @staticmethod
    def error(message="Error", error_code=None):
        return {
            "success": False,
            "message": message,
            "error_code": error_code
        }
    
    @staticmethod
    def paginated(data, total, page, per_page, message="Success"):
        return {
            "success": True,
            "message": message,
            "data": data,
            "pagination": {
                "total": total,
                "page": page,
                "per_page": per_page,
                "total_pages": (total + per_page - 1) // per_page
            }
        }
