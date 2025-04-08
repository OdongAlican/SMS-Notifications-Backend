import jwt
from .threadlocals import set_current_user
from users.models import PrideUser

class CurrentUserMiddleware:
    """
    Middleware to set the current user in thread-local storage from JWT token.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        
        # Extract token from Authorization header
        token = request.headers.get('Authorization')
        if token and token.startswith('Bearer '):
            token = token[7:]  # Remove "Bearer " prefix
            print(token, "Token information")
            
            try:
                # payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
                payload = jwt.decode(token, 'your_secret_key', algorithms=["HS256"])
                
                user_id = payload.get('user_id')

                if user_id:
                    user = PrideUser.objects.get(id=user_id)
                    print(f"Authenticated user: {user}")
                    set_current_user(user)
                else:
                    print("User ID not found in token.")
            except jwt.ExpiredSignatureError:
                print("Token has expired.")
            except jwt.InvalidTokenError:
                print("Invalid token.")
        
        response = self.get_response(request)
        return response
