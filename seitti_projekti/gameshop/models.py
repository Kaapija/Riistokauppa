from django.db import models
from django.contrib.auth.models import User
import hashlib, datetime, random
from django.utils import timezone

def createActivationCode(user):
    activationCode = hashlib.sha1(str(random.random()).encode("utf-8")).hexdigest()
    activationInfo = UserActivation.objects.create(activationCode=activationCode,
                                    expires=datetime.datetime.today() + datetime.timedelta(7),
                                    user=user)
    return activationCode

def createUser(userInfo, isActive=True):
    newUser = User.objects.create_user(username=userInfo["username"])

    if "email" in userInfo:
        newUser.email = userInfo["email"]

    if "password" in userInfo:
        newUser.set_password(userInfo["password"])

    if not isActive:
        newUser.is_active = False

    newUser.first_name = userInfo["firstName"]
    newUser.last_name = userInfo["lastName"]
    newUser.save()
    return newUser

def updateUser(user, userInfo):
    user.first_name = userInfo["firstName"]
    user.last_name = userInfo["lastName"]
    user.email = userInfo["email"]
    user.username = userInfo["username"]
    user.save()

class Developer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.user.username

    def isDeveloperOf(self, game_name):
        return any(game.name == game_name for game in self.games.all())

class Player(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.user.username;

    def hasBought(self, game_name):
        games = self.game_set.all()
        return any(game.name == game_name for game in games)

    def getScoresForGame(self, game):
        scores = Score.objects.filter(game=game, player=self)
        scorelist = map(lambda score: score.score, scores)
        return sorted(scorelist, reverse=True)

    def getRecentlyBoughtGames(self):
        payments = self.payments.exclude(status=0)
        recentPayments = filter(lambda p: timezone.now() - p.timestamp < datetime.timedelta(days=7), payments)
        games = map(lambda p: p.game, recentPayments)
        return games

class FacebookUser(models.Model):
    facebookId = models.CharField(unique=True, max_length=40)
    user = models.OneToOneField(User, on_delete=models.CASCADE)

class UserActivation(models.Model):
    activationCode = models.CharField(unique=True, max_length=40)
    expires = models.DateTimeField()
    user = models.OneToOneField(User, on_delete=models.CASCADE)

class Game(models.Model):
    categories = (
        (0, "Seikkailu"),
        (1, "Puzzle"),
        (2, "Tasohyppely"),
        (3, "Räiskintä"),
        (4, "Muu")
    )
    name = models.CharField(unique=True, max_length=30)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=300, default="")
    url = models.URLField()
    category = models.CharField(max_length=20, choices=categories, default=4)
    buyers = models.ManyToManyField(Player, blank=True)
    developer = models.ForeignKey(Developer, related_name="games", blank=True, null=True, on_delete=models.PROTECT)

    def __str__(self):
        return self.name

    def setPrice(self, newPrice):
        self.price = newPrice
        self.save()

    def addBuyer(self, buyer):
        self.buyers.add(buyer)
        self.save()

    def getTotalSales(self):
        total = 0
        for payment in self.payments.all():
            total += payment.amount
        return total

    def setDescription(self, newDescription):
        self.description = newDescription
        self.save()

    def getSortedScoreList(self):
        scores = self.scores.all()
        scoresAndPlayers = map(lambda score: (score.player, score.score), scores)
        return sorted(scoresAndPlayers, key=lambda score: score[1], reverse=True)

    @staticmethod
    def getPopularUnboughtGames(player):
        games = Game.objects.exclude(buyers=player)
        popular = sorted(games, key=lambda game: game.payments.exclude(status=0).count(), reverse=True)
        return popular[:5]

    @staticmethod
    def searchGames(searchTerms, player):
        games = Game.objects.filter(name__icontains=searchTerms["gameName"],
                                    developer__user__username__icontains=searchTerms["developerName"])

        if "maxPrice" in searchTerms and searchTerms["maxPrice"]:
            maxPrice = searchTerms["maxPrice"]
            games = games.filter(price__lte=maxPrice)
        if "minPrice" in searchTerms and searchTerms["minPrice"]:
            minPrice = searchTerms["minPrice"]
            games = games.filter(price__gte=minPrice)
        if searchTerms["categories"]:
            games = games.filter(category__in=searchTerms["categories"])

        games = games.exclude(buyers=player)
        return games

    @staticmethod
    def listGames(developerName):
        games = Game.objects.filter(developer__user__username__exact=developerName)
        return games

    def editGame(self, gameInfo):
        if gameInfo['name'] != self.name:
            gameWithName = Game.objects.all().filter(name=gameInfo['name'])
            if gameWithName.exists():
                # gameInfo.add_error("name", "Samanniminen peli on jo järjestelmässä")
                return False
        if gameInfo['url'] != self.url:
            gameWithUrl = Game.objects.all().filter(name=gameInfo['url'])
            if gameWithUrl.exists():
                # gameInfo.add_error("url", "Sama peli on jo järjestelmässä")
                return False
        self.name = gameInfo['name']
        self.url = gameInfo['url']
        self.description = gameInfo['description']
        self.categories = gameInfo['categories']
        self.save()
        return True

def createGame(gameInfo, user):
    game = Game.objects.create(name = gameInfo['name'], price = gameInfo['price'],
                               description = gameInfo['description'],
                               url = gameInfo['url'],
                               category = gameInfo['categories'],
                               developer = user)
    return game

class Payment(models.Model):
    states = (
        (0, "Pending"),
        (1, "Completed")
    )

    amount = models.DecimalField(max_digits=10, decimal_places=2)
    timestamp = models.DateTimeField()
    status = models.CharField(max_length=10, choices=states, default=0)
    player = models.ForeignKey(Player, related_name="payments", blank=True, null=True, on_delete=models.SET_NULL)
    game = models.ForeignKey(Game, related_name="payments", blank=True, null=True, on_delete=models.PROTECT)

    def complete(self):
        self.status = 1;
        self.save()
        game = self.game
        game.buyers.add(self.player)
        game.save()

class Score(models.Model):
    score = models.FloatField()
    game = models.ForeignKey(Game, related_name="scores", blank=True, null=True)
    player = models.ForeignKey(Player, related_name="scores", blank=True, null=True)

class GameState(models.Model):
    stateData = models.CharField(max_length=400, default="{}")
    game = models.ForeignKey(Game, related_name="gamestates", blank=True, null=True)
    player = models.ForeignKey(Player, related_name="gamestates", blank=True, null=True)

    @staticmethod
    def saveGame(game, player, stateData):
        # We only want to keep the most recent save
        oldSaves = GameState.objects.filter(player=player, game=game).delete()
        GameState.objects.create(stateData=stateData, player=player, game=game)
