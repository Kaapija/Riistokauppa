from django.conf.urls import include, url
from django.contrib import admin
from gameshop import views
from gameshop_api import views as apiViews

urlpatterns = [
    # Examples:
    # url(r'^$', 'seitti_projekti.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^admin/', include(admin.site.urls)),
    url(r'^$', views.index, name='index'),
    url(r'^login$', views.log_in, name='login'),
    url(r'^logout$', views.log_out, name="logout"),
    url(r'^register$', views.register, name="register"),
    url(r'^activate/(?P<activationCode>\w+)', views.activation, name="activation"),
    url(r'^facebook_login$', views.facebookLogin, name="fbLogin"),
    url(r'^facebook_user_finalize$', views.facebookUserFinalize, name="fbUserfinalize"),
	url(r'^examine$', views.examine, name='examine'),
	url(r'^add$', views.add, name='add'),
	url(r'^dev_profile$', views.dev_profile, name='dev_profile'),
	url(r'^devModify$', views.devModify, name="devModify"),
	url(r'^devModifyPass$', views.changePasswordDev, name="changePasswordDev"),
    url(r'^search$', views.search, name='search'),
    #url(r'^buy_game/(?P<game>\w+)', views.buyGame, name="buyGame"),
    url(r'^game/(?P<game>\w+)', views.game, name="game"),
    url(r'^editGame/(?P<game>\w+)', views.editGame, name="editGame"),
    url(r'^dev_game/(?P<game>\w+)', views.dev_game, name="dev_game"),
    url(r'^submit_score/(?P<game>\w+)', views.submitScore, name="submitScore"),
    url(r'^gamestate/(?P<game>\w+)', views.gameState, name="gameState"),
    url(r'^player_profile$', views.playerProfile, name="playerProfile"),
    url(r'^player_modify$', views.playerModifyInfo, name="playerModifyInfo"),
    url(r'^change_password$', views.changePassword, name="changePassword"),
    url(r'^confirm_payment/(?P<game>\w+)$', views.confirmPayment, name="confirmPayment"),
    url(r'^succesful_payment$', views.succesfulPayment, name="succesfulPayment"),
    url(r'^failed_payment$', views.failedPayment, name="failedPayment"),
    url(r'^highscore$', apiViews.highscore, name="highscore"),
    url(r'^highscore/(?P<id>\w+)$', apiViews.gameHighscore, name="gameHighscore"),

]
