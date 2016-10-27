from django import forms
from django.forms.utils import ErrorList
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from gameshop.models import Game
from hashlib import md5

class LoginForm(forms.Form):
    username = forms.CharField(label="Käyttäjätunnus",
                               error_messages= {"required": "Käyttäjätunnus on pakollinen"})
    password = forms.CharField(label="Salasana",
                               widget=forms.PasswordInput(),
                               error_messages={"required": "Salasana on pakollinen"})

    def clean(self):
        super(LoginForm, self).clean()
        username = self.cleaned_data.get("username")
        password = self.cleaned_data.get("password")
        if password and username:
            user = authenticate(username=username, password=password)
            if not user or not user.is_active:
                raise forms.ValidationError("Kirjautumistiedoilla ei löytynyt käyttäjää")
        return self.cleaned_data

    def login(self):
        username = self.cleaned_data["username"]
        password = self.cleaned_data["password"]
        user = authenticate(username=username, password=password)
        return user

class RegistrationForm(forms.Form):
    firstName = forms.CharField(label="Etunimi",
                                error_messages= {"required": "Etunimi on pakollinen"})
    lastName = forms.CharField(label="Sukunimi",
                               error_messages= {"required": "Sukunimi on pakollinen"})

    username = forms.CharField(label="Käyttäjätunnus",
                               error_messages= {"required": "Käyttäjätunnus on pakollinen"})

    email = forms.EmailField(label="Sähköposti",
                             error_messages= {"required": "Sähköposti on pakollinen",
                                              "invalid": "Anna kelvollinen sähköpostiosoite"})
    password = forms.CharField(label="Salasana",
                               widget=forms.PasswordInput(),
                               error_messages={"required": "Pakollinen on pakollinen"})
    passwordAgain = forms.CharField(label="Salasana uudestaan",
                               widget=forms.PasswordInput(),
                               error_messages={"required": "Salasana täytyy toistaa"})

    userType = forms.ChoiceField(label="Tilin tyyppi",
                                 choices=[("player", "Pelaaja"), ("developer", "Kehittäjä")],
                                 initial="player",
                                 widget=forms.RadioSelect())

    def clean(self):
        password1 = self.cleaned_data.get("password")
        password2 = self.cleaned_data.get("passwordAgain")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Salasanat eivät vastaa toisiaan")

        username = self.cleaned_data.get("username")
        userWithUsername = User.objects.all().filter(username=username)
        if username and userWithUsername.exists():
            self.add_error("username", "Käyttäjätunnus on jo käytössä")

        email = self.cleaned_data.get("email")
        userWithEmail = User.objects.all().filter(email=email)
        if email and userWithEmail.exists():
            self.add_error("email", "Sähköpostiosoite on jo käytössä")

        return self.cleaned_data

class GameSearchForm(forms.Form):
    gameName = forms.CharField(label="Pelin nimi", required=False)
    developerName = forms.CharField(label="Kehittäjä", required=False)
    minPrice = forms.DecimalField(label="Hinta vähintään", max_digits=10, decimal_places=2, required=False)
    maxPrice = forms.DecimalField(label="Hinta enintään", max_digits=10, decimal_places=2, required=False)
    categories = forms.MultipleChoiceField(label="Kategoria",
                                           choices=Game.categories,
                                           widget=forms.CheckboxSelectMultiple(), required=False)

class GameAddForm(forms.Form):
    name = forms.CharField(label="Pelin nimi",
                               error_messages= {"required": "Nimi on pakollinen"})
    url = forms.CharField(label="Pelin url",
                               error_messages= {"required": "Url on pakollinen"})
    price = forms.DecimalField(label="Hinta", max_digits=10, decimal_places=2,
                                   error_messages= {"required": "Hinta on pakollinen"})
    description = forms.CharField(label="Pelin esittely",
                                      error_messages= {"required": "Kirjoita esittelyteksti"})
    categories = forms.MultipleChoiceField(label="Kategoria",
                                           choices=Game.categories,
                                           widget=forms.CheckboxSelectMultiple(),
                                           error_messages= {"required": "Valitse vähintään yksi kategoria"})

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(GameAddForm, self).__init__(*args, **kwargs)

    def clean(self):
        name = self.cleaned_data.get("name")
        gameWithName = Game.objects.all().filter(name=name)
        if name and gameWithName.exists():
            self.add_error("name", "Samanniminen peli on jo järjestelmässä")

        url = self.cleaned_data.get("url")
        gameWithUrl = Game.objects.all().filter(url=url)
        if url and gameWithUrl.exists():
            self.add_error("url", "Peli on jo järjestelmässä")
        return self.cleaned_data

class GameEditForm(forms.Form):
    name = forms.CharField(label="Pelin nimi",
                               error_messages= {"required": "Nimi on pakollinen"})
    url = forms.CharField(label="Pelin url",
                               error_messages= {"required": "Url on pakollinen"})
    price = forms.DecimalField(label="Hinta", max_digits=10, decimal_places=2,
                                   error_messages= {"required": "Hinta on pakollinen"})
    description = forms.CharField(label="Pelin esittely",
                                      error_messages= {"required": "Kirjoita esittelyteksti"})
    categories = forms.MultipleChoiceField(label="Kategoria",
                                           choices=Game.categories,
                                           widget=forms.CheckboxSelectMultiple(),
                                           error_messages= {"required": "Valitse vähintään yksi kategoria"})

class ModifyDevForm(forms.Form):
    firstName = forms.CharField(label="Etunimi",
                                error_messages= {"required": "Etunimi on pakollinen"})
    lastName = forms.CharField(label="Sukunimi",
                               error_messages= {"required": "Sukunimi on pakollinen"})

    username = forms.CharField(label="Käyttäjätunnus",
                               error_messages= {"required": "Käyttäjätunnus on pakollinen"})

    email = forms.EmailField(label="Sähköposti",
                             error_messages= {"required": "Sähköposti on pakollinen",
                                              "invalid": "Anna kelvollinen sähköpostiosoite"})

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(ModifyDevForm, self).__init__(*args, **kwargs)

    def clean(self):
        username = self.cleaned_data.get("username")
        userWithUsername = User.objects.all().filter(username=username).exclude(pk=self.user.pk)
        if username and userWithUsername.exists():
            self.add_error("username", "Käyttäjätunnus on jo käytössä")

        email = self.cleaned_data.get("email")
        userWithEmail = User.objects.all().filter(email=email).exclude(pk=self.user.pk)
        if email and userWithEmail.exists():
            self.add_error("email", "Sähköpostiosoite on jo käytössä")

        return self.cleaned_data

class ModifyPlayerForm(forms.Form):
    firstName = forms.CharField(label="Etunimi",
                                error_messages= {"required": "Etunimi on pakollinen"})
    lastName = forms.CharField(label="Sukunimi",
                               error_messages= {"required": "Sukunimi on pakollinen"})

    username = forms.CharField(label="Käyttäjätunnus",
                               error_messages= {"required": "Käyttäjätunnus on pakollinen"})

    email = forms.EmailField(label="Sähköposti",
                             error_messages= {"required": "Sähköposti on pakollinen",
                                              "invalid": "Anna kelvollinen sähköpostiosoite"})

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(ModifyPlayerForm, self).__init__(*args, **kwargs)

    def clean(self):
        username = self.cleaned_data.get("username")
        userWithUsername = User.objects.all().filter(username=username).exclude(pk=self.user.pk)
        if username and userWithUsername.exists():
            self.add_error("username", "Käyttäjätunnus on jo käytössä")

        email = self.cleaned_data.get("email")
        userWithEmail = User.objects.all().filter(email=email).exclude(pk=self.user.pk)
        if email and userWithEmail.exists():
            self.add_error("email", "Sähköpostiosoite on jo käytössä")

        return self.cleaned_data

class ChangePasswordForm(forms.Form):
    oldPassword = forms.CharField(label="Nykyinen salasana",
                                  widget=forms.PasswordInput(),
                                  required=False)
    newPassword = forms.CharField(label="Uusi salasana",
                                  widget=forms.PasswordInput(),
                                  error_messages={"required": "Uusi salasana on pakollinen"})
    newPasswordAgain = forms.CharField(label="Uusi salasana uudestaan",
                                       widget=forms.PasswordInput(),
                                       error_messages={"required": "Salasana täytyy toistaa"})

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(ChangePasswordForm, self).__init__(*args, **kwargs)

    def clean(self):
        oldPassword = self.cleaned_data.get("oldPassword")
        password1 = self.cleaned_data.get("newPassword")
        password2 = self.cleaned_data.get("newPasswordAgain")

        if self.user.has_usable_password():
            if not oldPassword:
                raise forms.ValidationError("Nykyinen salasana on pakollinen")

            if not self.user.check_password(oldPassword):
                raise forms.ValidationError("Vanha salasana on väärin")

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Salasanat eivät vastaa toisiaan")
        return self.cleaned_data

class PaymentForm(forms.Form):
    pid = forms.CharField(widget=forms.HiddenInput())
    sid = forms.CharField(widget=forms.HiddenInput())
    success_url = forms.CharField(widget=forms.HiddenInput())
    cancel_url = forms.CharField(widget=forms.HiddenInput())
    error_url = forms.CharField(widget=forms.HiddenInput())
    checksum = forms.CharField(widget=forms.HiddenInput())
    amount = forms.CharField(widget=forms.HiddenInput())

    def setUpPayment(self, pid, sid, secret, amount, success, error, cancel):
        checkSumSeed = "pid={}&sid={}&amount={}&token={}".format(pid, sid, amount, secret)
        m = md5(checkSumSeed.encode("ascii"))
        checksum = m.hexdigest()

        self.initial["pid"] = pid
        self.initial["sid"] = sid
        self.initial["amount"] = amount
        self.initial["checksum"] = checksum
        self.initial["success_url"] = success
        self.initial["error_url"] = error
        self.initial["cancel_url"] = cancel
