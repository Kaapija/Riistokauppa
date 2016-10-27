from django.test import TestCase, Client
from django.db import models
from .models import Game, Player, Developer, FacebookUser
from .forms import LoginForm
from django.contrib.auth.models import User
import json

class ModelTests(TestCase):
    fixtures = ["shopdata.xml"]

    def testHasBoughtMethod(self):
        player = Player.objects.get(pk=1)
        self.assertTrue(player.hasBought("Dummy Game"))

    def testIsDeveloperMethod(self):
        dev = Developer.objects.get(pk=1)
        self.assertTrue(dev.isDeveloperOf("Dummy Game"))

    def testAddBuyer(self):
        game = Game.objects.get(pk=1)
        user = User.objects.create_user(username="test_user")
        player = Player.objects.create(user=user)
        game.addBuyer(player)
        self.assertTrue(any(user == buyer.user for buyer in game.buyers.all()))

    def testSearchGames(self):
        games = Game.searchGames({"gameName": "dummy",
                                  "developerName": "",
                                  "maxPrice": 13,
                                  "minPrice": None,
                                  "categories": []}, 2)
        self.assertTrue(any(game.name == "Dummy Game" for game in games.all()))

class LoginViewTests(TestCase):
    fixtures = ["shopdata.xml"]
    loginTemplate = "login.html"
    loginUrl = "/login"

    def setUp(self):
        self.client = Client()

    def testSuccesfulLogin(self):
        response = self.client.post(self.loginUrl, {"username": "devaaja", "password": "dev1"}, follow=True)
        self.assertRedirects(response, "/")

    def testUnsuccesfulLogin(self):
        response = self.client.post(self.loginUrl, {"username": "roska", "password": "feikki"}, follow=True)
        self.assertTrue(response.status_code == 403)
        self.assertTemplateUsed(response, "login.html")

    def testAlreadyLoggedIn(self):
        self.client.login(username="devaaja", password="dev1")
        response = self.client.get(self.loginUrl)
        self.assertTrue(response.status_code == 302)
        self.assertRedirects(response, "/")

    def testMissingPassword(self):
        response = self.client.post(self.loginUrl, {"username": "user", "password": ""})
        self.assertFormError(response, "form", "password", "Salasana on pakollinen")

    def testMissingUsername(self):
        response = self.client.post(self.loginUrl, {"username": "", "password": "pw"})
        self.assertFormError(response, "form", "username", "Käyttäjätunnus on pakollinen")

class RegisterViewTests(TestCase):
    fixtures = ["shopdata.xml"]
    registerUrl = "/register"

    def setUp(self):
        self.client = Client()

    def testAlreadyLoggedIn(self):
        self.client.login(username="devaaja", password="dev1")
        response = self.client.get(self.registerUrl)
        self.assertTrue(response.status_code == 302)
        self.assertRedirects(response, "/")

    def testSomeMissingFields(self):
        response = self.client.post(self.registerUrl, {"firstName": "P", "lastName": "Z"})
        self.assertTrue(response.status_code == 400)
        self.assertTemplateUsed(response, "registration.html")

    def testSuccesfulRegistration(self):
        username = "asdasd"
        userType = "developer"
        response = self.client.post(self.registerUrl,
                                    {"firstName": "P",
                                     "lastName": "Z",
                                     "username": username,
                                     "password": "aaaaxx",
                                     "passwordAgain": "aaaaxx",
                                     "email": "aa@aa.fi",
                                     "userType": userType})
        user = User.objects.get(username=username)
        self.assertTrue(user.is_active == False)
        self.assertTrue(hasattr(user, "useractivation"))
        self.assertTrue(hasattr(user, "developer"))

class FacebookLoginViewTests(TestCase):
    fixtures = ["shopdata.xml"]
    fbLoginUrl = "/facebook_login"

    def setUp(self):
        self.client = Client()

    def testFirstTimeFacebookLogin(self):
        response = self.client.post(self.fbLoginUrl, {"id": 11,
                                                      "firstName": "name",
                                                      "lastName": "last"},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        content = response.content.decode("utf-8")
        self.assertTrue( "html" in json.loads(content))

    def testExistingFacebookUser(self):
        facebookId = 11
        user = User.objects.get(pk=1)
        fbUser = FacebookUser.objects.create(user=user, facebookId=facebookId)
        response = self.client.post(self.fbLoginUrl, {"id": facebookId,
                                                      "firstName": "name",
                                                      "lastName": "last"},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertTrue(user.is_authenticated())
        jr = json.loads(response.content.decode("utf-8"))
        self.assertTrue(jr["url"] == "/")

    def testExistingUserWithMatchingEmail(self):
        oldFbUserCount = FacebookUser.objects.count()
        user = User.objects.get(pk=1)
        email = user.email
        response = self.client.post(self.fbLoginUrl, {"id": 1,
                                                      "firstName": "name",
                                                      "lastName": "last",
                                                      "email": email},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertTrue(user.is_authenticated())
        self.assertTrue(hasattr(user, "facebookuser"))
        newFbUserCount = FacebookUser.objects.count()
        self.assertTrue(newFbUserCount > oldFbUserCount)

class searchViewTests(TestCase):
    fixtures = ["shopdata.xml"]
    searchUrl = "/search"

    def setUp(self):
        self.client = Client()
        self.client.login(username="pelaaja", password="pel1")

    def testGet(self):
        response = self.client.get(self.searchUrl)
        self.assertTemplateUsed("search.html")

    def testSearch(self):
        response = self.client.post(self.searchUrl, {"gameName": "test",
                                                     "developerName": "test",
                                                     "minPrice": 10,
                                                     "maxPrice": 13,
                                                     "categories": []},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        jsonResponse = json.loads(response.content.decode("utf-8"))
        self.assertEqual(jsonResponse["status"], 1)
        self.assertEqual(response.status_code, 200)

class testGameView(TestCase):
    fixtures = ["shopdata.xml"]
    gameUrl = "/game"

    def setUp(self):
        self.client = Client()
        self.client.login(username="pelaaja", password="pel1")

    def testBoughtGame(self):
        game = Game.objects.get(pk=1)
        response = self.client.get(self.gameUrl + "/" + str(game.pk))
        self.assertTemplateUsed("game_play.html")

    def testUnboughtGame(self):
        game = Game.objects.get(pk=2)
        response = self.client.get(self.gameUrl + "/" + str(game.pk))
        self.assertTemplateUsed("game_examine.html")

class testSubmitScoreView(TestCase):
    fixtures = ["shopdata.xml"]
    submitUrl = "/submit_score"

    def setUp(self):
        self.client = Client()
        self.client.login(username="pelaaja", password="pel1")

    def testSubmit(self):
        game = Game.objects.get(pk=1)
        player = Player.objects.get(pk=1)
        points = 500.0
        response = self.client.post(self.submitUrl + "/" + str(game.pk),
                                    {"score": points},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        scores = player.getScoresForGame(game)
        self.assertTrue(any(score == points for score in scores))

class testGameStateView(TestCase):
    fixtures = ["shopdata.xml"]
    submitUrl = "/gamestate"

    def setUp(self):
        self.client = Client()
        self.client.login(username="pelaaja", password="pel1")

    def testSaveGame(self):
        game = Game.objects.get(pk=1)
        gameStateData = "{items: testrock}"
        response = self.client.post(self.submitUrl + "/" + str(game.pk),
                                    {"gameState": gameStateData},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertTrue(any(save.stateData == gameStateData for save in game.gamestates.filter()))

    def testLoadGame(self):
        game = Game.objects.get(pk=1)
        gameStateData = "{items: testrock}"
        response = self.client.post(self.submitUrl + "/" + str(game.pk),
                                    {"gameState": gameStateData},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        response = self.client.get(self.submitUrl + "/" + str(game.pk),
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(gameStateData, response.content.decode("utf-8"))
