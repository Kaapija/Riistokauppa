from django.shortcuts import render
from django.http import HttpResponseRedirect, Http404, HttpResponse
from gameshop.models import Score, Game
import json

def highscore(request):
    games = Game.objects.all()
    urls = {}
    for game in games:
        urls[game.name] = request.build_absolute_uri(request.get_full_path()) + "/" + str(game.pk)
    return HttpResponse(json.dumps(urls), content_type="application/json")

def gameHighscore(request, id):
    try:
        game = Game.objects.get(pk=id)
        # Python dicts require unique keys so parsing has to be done manually here.
        scoreJson = "{ "
        scores = game.getSortedScoreList()
        if scores:
            for score in scores[:-1]:
                scoreJson += score[0].user.username + ": " + str(score[1]) + ", "
            else:
                scoreJson += scores[-1][0].user.username + ": " + str(scores[-1][1])
        scoreJson += " }"
        return HttpResponse(scoreJson, content_type="application/json")
    except:
        raise Http404("No such game")
