from django.contrib import admin

from gameshop.models import Player, Developer, FacebookUser, Game, GameState, UserActivation, Payment, Score

admin.site.register(Player)
admin.site.register(Developer)
admin.site.register(FacebookUser)
admin.site.register(Game)
admin.site.register(GameState)
admin.site.register(UserActivation)
admin.site.register(Payment)
admin.site.register(Score)
