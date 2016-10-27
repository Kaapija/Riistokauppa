from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User
from gameshop.models import FacebookUser

class FacebookAuthBackend(object):

    def authenticate(self, facebookId=None):
        try:
            fbUser = FacebookUser.objects.get(facebookId=facebookId)
            return fbUser.user
        except:
            return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
