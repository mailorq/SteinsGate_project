from django.db import models


class Profile(models.Model):
    user = models.OneToOneField('auth.User', on_delete=models.CASCADE)
    nickname = models.CharField(max_length=255, null=True, blank=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True, default='avatars/default.jpg')

    def __str__(self):
        return self.user.username