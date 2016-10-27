from django.shortcuts import render, get_object_or_404
from gameshop.forms import LoginForm, RegistrationForm, GameSearchForm, PaymentForm, ModifyDevForm, ModifyPlayerForm, ChangePasswordForm, GameAddForm, GameEditForm
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import HttpResponseRedirect, Http404, HttpResponse
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.utils import timezone
from django.conf import settings
from gameshop.models import UserActivation, Player, Developer, FacebookUser, Game, GameState, Score, Payment, updateUser, createUser, createActivationCode, createGame
from gameshop.authbackends import FacebookAuthBackend
from django.template.loader import render_to_string
from hashlib import md5
import json, datetime

def isDeveloper(user):
    return hasattr(user, "developer")

def isPlayer(user):
    return hasattr(user, "player")

def log_in(request):
    if request.user.is_authenticated():
        return HttpResponseRedirect("/")
    elif request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            user = form.login()
            login(request, user)
            return HttpResponseRedirect("/")
        else:
            return render(request, "login.html", {"form": form}, status=403)
    else:
        form = LoginForm()
        return render(request, "login.html", {"form": form})

@login_required(login_url="/login")
def index(request):
    if isPlayer(request.user):
        ownGames = request.user.player.game_set.all()
        popularGames = Game.getPopularUnboughtGames(request.user.player)
        return render(request, "player_index.html", {"ownGames": ownGames, "popularGames": popularGames})
    elif isDeveloper(request.user):
        return render(request, "dev_index.html")

@login_required(login_url="/login")
def log_out(request):
    logout(request)
    return HttpResponseRedirect("/login")

def register(request):
    if request.user.is_authenticated():
        return HttpResponseRedirect("/")
    elif request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            newUser = createUser(form.cleaned_data, False)
            activationCode = createActivationCode(newUser)

            # Create either a Developer or Player object for the account being registered
            if form.cleaned_data["userType"] == "developer":
                newDev = Developer.objects.create(user=newUser)
            else:
                newPlayer = Player.objects.create(user=newUser)

            # Send email with account activation info
            emailSubject = "Account activation"
            emailBody = "Aktivoi tilisi osoitteessa " + request.get_host() + "/activate/" + activationCode
            send_mail(emailSubject, emailBody,
                      "admin@riistokauppa.com", [form.cleaned_data["email"]])

            return render(request, "registration_success.html")
        else:
            return render(request, "registration.html", {"form": form}, status=400)
    else:
        form = RegistrationForm()
        return render(request, "registration.html", {"form": form})

def activation(request, activationCode):
    if request.user.is_authenticated():
        return HttpResponseRedirect("/")
    try:
        activationInfo = UserActivation.objects.get(activationCode=activationCode)
        if activationInfo.expires > timezone.now():
            user = activationInfo.user
            user.is_active = True
            user.save()
            return render(request, "activation_success.html")
        else:
            raise Http404("Aktivointikoodi on vanhentunut.")
    except UserActivation.DoesNotExist:
        raise Http404("Antamaasi aktivointikoodia ei löytynyt.")

def facebookLogin(request):
    if request.is_ajax():
        facebookId = request.POST['id']
        firstName = request.POST['firstName']
        lastName = request.POST['lastName']

        if "email" in request.POST:
            userWithEmail = User.objects.all().filter(email=request.POST["email"])
            if userWithEmail.exists():
                existingUser = userWithEmail.first()
                fbUser = FacebookUser.objects.create(facebookId=facebookId, user=existingUser)

        fbUserWithId = FacebookUser.objects.all().filter(facebookId=facebookId)
        if fbUserWithId.exists():
            response = {"url": "/"}
            user = authenticate(facebookId=facebookId)
            login(request, user)
        else:
            username = firstName + str(User.objects.count())
            html = render_to_string("user_type_form.html",
                                    {"username": username, "facebookid": facebookId, "firstName": firstName, "lastName": lastName},
                                    request=request)
            response = {"html": html, "status": 1}
        return HttpResponse(json.dumps(response), content_type='application/json')
    else:
        return HttpResponseRedirect("/")

def facebookUserFinalize(request):
    if request.method == "POST" and not isPlayer(request.user) and not isDeveloper(request.user):
        newUser = createUser(request.POST)

        facebookId = request.POST["facebookid"]
        newFacebookUser = FacebookUser.objects.create(facebookId=facebookId, user=newUser)
        user = authenticate(facebookId=facebookId)

        if request.POST["userType"] == "developer":
            dev = Developer.objects.create(user=user)
        else:
            player = Player.objects.create(user=user)
        login(request, user)
    return HttpResponseRedirect("/")

@login_required(login_url="/login")
def examine(request):
    if isDeveloper(request.user):
        games = Game.listGames(request.user.username)
        context = {'games': games}
        return render(request, 'dev_listofgames.html', context)
    else:
        return HttpResponseRedirect("/")

@login_required(login_url="/login")
def add(request):
    if isDeveloper(request.user):
        if request.method == "GET":
            form = GameAddForm()
            return render(request, "dev_addgame.html", {"form": form})
        elif request.method == "POST":
            form = GameAddForm(request.POST)
            if form.is_valid():
                game = createGame(form.cleaned_data, request.user.developer)
                return render(request, "dev_game_examine.html", {"game": game})
            else:
                return render(request, "dev_addgame.html", {"form": form}, status=400)
        else:
            return HttpResponseRedirect("/")
    else:
        return HttpResponseRedirect("/")

@login_required(login_url="/login")
def dev_game(request, game):
    if isDeveloper(request.user):
        game = get_object_or_404(Game, pk=game)
        if (game.developer == request.user.developer):
            game.buyerAmount = game.buyers.count()
            return render(request, "dev_game_examine.html", {"game": game})
        return HttpResponseRedirect("/")
    else:
        return HttpResponseRedirect("/")

@login_required(login_url="/login")
def editGame(request, game):
    if isDeveloper(request.user):
        game = get_object_or_404(Game, pk=game)
        if (game.developer == request.user.developer):
            if request.method == "POST":
                form = GameEditForm(request.POST)
                if form.is_valid():
                    if game.editGame(form.cleaned_data):
                        messages.success(request, "Tiedot muutettu")
                    else:
                        messages.error(request, "Peli on järjestelmässä")
                return render(request, "dev_game_edit.html", {"form": form})
            else:
                initialData = {"name": game.name, "url": game.url,
                               "price": game.price, "description": game.description,
                               "categories": game.category}
                form = GameEditForm(initial=initialData)
                return render(request, "dev_game_edit.html", {"form": form})
        else:
            return HttpResponseRedirect("/")
    else:
        return HttpResponseRedirect("/")

@login_required(login_url="/login")
def dev_profile(request):
	return render(request, "dev_profile.html")

@login_required(login_url="/login")
def search(request):
    if isPlayer(request.user):
        if request.method == "GET":
            form = GameSearchForm()
            return render(request, "search.html", { "form": form })
        elif request.is_ajax():
            form = GameSearchForm(request.POST)
            if form.is_valid():
                games = Game.searchGames(form.cleaned_data, request.user.player)
                html = render_to_string("search_results.html", {"results": games}, request=request)
                response = {"html": html, "status": 1} # status is mainly for testing purposes
            else:
                response = {"html": "Error", "status": -1}
            return HttpResponse(json.dumps(response), content_type="json/application")
        else:
            return HttpResponseRedirect("/")
    else:
        return HttpResponseRedirect("/")

@login_required(login_url="/login")
def game(request, game):
    if (isPlayer(request.user)):
        game = get_object_or_404(Game, pk=game)
        if (request.user.player.hasBought(game.name)):
            highScores = game.getSortedScoreList()[:10]
            playerScores = request.user.player.getScoresForGame(game)[:10]
            return render(request, "game_play.html", {"game": game,
                                                      "highScores": highScores,
                                                      "playerScores": playerScores})
        else:
            return render(request, "game_examine.html", {"game": game})
    else:
        return HttpResponseRedirect("/")

@login_required(login_url="/login")
def submitScore(request, game):
    try:
        if request.is_ajax():
            game = Game.objects.get(pk=game)
            gs = Score.objects.create(score=request.POST["score"],
                                      player=request.user.player,
                                      game=game)
            return HttpResponse()
        else:
            return HttpResponseRedirect("/")
    except:
        return HttpResponse("Pisteiden tallennus epäonnistui")

@login_required(login_url="/login")
def gameState(request, game):
    if request.is_ajax():
        game = Game.objects.get(pk=game)
        if request.method == "POST":
            stateData = request.POST["gameState"]
            GameState.saveGame(stateData=stateData,
                               game=game,
                               player=request.user.player)
            return HttpResponse("ok")
        else:
            savedGame = GameState.objects.filter(game=game, player=request.user.player)[0]
            return HttpResponse(savedGame.stateData)
    else:
        return HttpResponseRedirect("/")

@login_required(login_url="/login")
def devModify(request):
	if request.method == "POST":
		form = ModifyDevForm(request.POST, user=request.user)
		if form.is_valid():
			user = updateUser(request.user, form.cleaned_data)
			messages.success(request, "Tiedot muutettu")
		return render(request, "dev_modify.html", {"form": form})
	else:
		initialData = {"username": request.user.username,
						"email": request.user.email,
						"firstName": request.user.first_name,
						"lastName": request.user.last_name }
		form = ModifyDevForm(initial=initialData)
		return render(request, "dev_modify.html", {"form": form})

@login_required(login_url="/login")
def playerProfile(request):
    return render(request, "player_profile.html")

@login_required(login_url="/login")
def playerModifyInfo(request):
    if request.method == "POST":
        form = ModifyPlayerForm(request.POST, user=request.user)
        if form.is_valid():
            user = updateUser(request.user, form.cleaned_data)
            messages.success(request, "Tiedot muutettu")
        return render(request, "player_modify.html", {"form": form})
    else:
        initialData = {"username": request.user.username,
                       "email": request.user.email,
                       "firstName": request.user.first_name,
                       "lastName": request.user.last_name }
        form = ModifyPlayerForm(initial=initialData)
        return render(request, "player_modify.html", {"form": form})

@login_required(login_url="/login")
def changePassword(request):
    if request.method == "POST":
        form = ChangePasswordForm(request.POST, user=request.user)
        if form.is_valid():
            request.user.set_password(form.cleaned_data["newPassword"])
            request.user.save()
            update_session_auth_hash(request, request.user)
            messages.success(request, "Salasana vaihdettu")
        return render(request, "change_password.html", {"form": form})
    else:
        form = ChangePasswordForm()
        return render(request, "change_password.html", {"form": form})

@login_required(login_url="/login")
def changePasswordDev(request):
    if request.method == "POST":
        form = ChangePasswordForm(request.POST, user=request.user)
        if form.is_valid():
            request.user.set_password(form.cleaned_data["newPassword"])
            request.user.save()
            update_session_auth_hash(request, request.user)
            messages.success(request, "Salasana vaihdettu")
        return render(request, "change_devpassword.html", {"form": form})
    else:
        form = ChangePasswordForm()
        return render(request, "change_devpassword.html", {"form": form})

@login_required(login_url="/login")
def confirmPayment(request, game):
    if isPlayer(request.user):
        sellerID = settings.PAYMENT_SETTINGS["SELLER_ID"]
        secretKey = settings.PAYMENT_SETTINGS["SECRET_KEY"]
        game = Game.objects.get(pk=game)
        player = request.user.player
        payment = Payment.objects.create(amount=game.price, timestamp=datetime.datetime.today(),
                                         player=player, game=game)

        form = PaymentForm()
        form.setUpPayment(payment.pk, sellerID, secretKey, game.price,
                          request.build_absolute_uri("/succesful_payment"),
                          request.build_absolute_uri("/failed_payment"),
                          request.build_absolute_uri("/failed_payment"))
        return render(request, "confirm_payment.html", {"form": form, "game": game})
    else:
        return HttpResponseRedirect("/")

@login_required(login_url="/login")
def succesfulPayment(request):
    try:
        checksumSeed = "pid={}&ref={}&result={}&token={}".format(request.GET["pid"],
                                                                 request.GET["ref"],
                                                                 request.GET["result"],
                                                                 settings.PAYMENT_SETTINGS["SECRET_KEY"])
        m = md5(checksumSeed.encode("ascii"))
        checksum = m.hexdigest()
        if checksum == request.GET["checksum"]:
            payment = Payment.objects.get(pk=request.GET["pid"])
            payment.complete()
            return HttpResponseRedirect("/game/" + str(payment.game.pk))
        else:
            return HttpResponseRedirect("/")
    except:
        return HttpResponseRedirect("/")

def failedPayment(request):
    try:
        pid = request.GET["pid"]
        Payment.objects.get(pk=pid).delete()
        if request.GET["result"] == "error":
            message = "Maksutapahtuma epäonnistui maksupalvelussa tapahtuneen virheen vuoksi."
            return render(request,
                          "payment_fail.html",
                          {"title": "Maksu epäonnistui",
                           "message": message})
        else:
            message = "Peruit maksutapahtuman, tiliäsi ei veloitettu"
            return render(request,
                          "payment_fail.html",
                          {"title": "Maksu peruttu",
                           "message": message})
    except:
        return HttpResponseRedirect("/")
