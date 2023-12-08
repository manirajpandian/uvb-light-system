from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from .models import Profile

User = get_user_model()

class ProfileBackend(ModelBackend):
    def authenticate(self, request, email=None, password=None, **kwargs):
        try:
            user = User.objects.get(email=email)
            profile_obj = Profile.objects.get(user=user)

            # Check the password against the user's password
            if user.check_password(password):
                return user
        except User.DoesNotExist:
            return None
        except Profile.DoesNotExist:
            return None

        return None
