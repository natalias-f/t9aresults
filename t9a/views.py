from datetime import datetime

from django.contrib.auth import get_user_model, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.shortcuts import render, redirect
from django.views import View

from . import forms
from .forms import UsernameForm, GameForm, MyResultForm, OpResultForm
from .models import Results, Lists, Games


class HomeView(View):
    def get(self, request):
        return render(
            request,
            'home.html',
        )


class ChangeUsernameView(LoginRequiredMixin, View):
    def get(self, request):
        user = get_user_model().objects.get(id=self.request.user.id)
        username = user.username
        init = {
            'username': username
        }

        form = UsernameForm(initial=init)
        return render(
            request,
            'my-account.html',
            context={
                'form': form

            }
        )

    def post(self, request):
        user = get_user_model().objects.get(id=self.request.user.id)
        username = self.request.POST.get('new_username')
        user.username = username
        user.save()

        return redirect('t9a:home')


class ResultView(LoginRequiredMixin, View):
    def get(self, request, pk=0):
        if pk == 0:
            my_result = Results.objects.filter(player_id=self.request.user.id)
        else:
            my_result = Results.objects.filter(Q(player_id=self.request.user.id) & Q(game_id=pk))
        for r in my_result:
            r.opponent = Results.objects.get(~Q(player_id=self.request.user.id)
                                             & Q(game_id=r.game_id))
        return render(
            request,
            'results.html',
            context={
                'results': my_result

            }
        )


class ListsView(LoginRequiredMixin, View):
    def get(self, request, pk=0):
        if pk == 0:
            lists = Lists.objects.filter(owner_id=self.request.user.id)
        else:
            lists = Lists.objects.filter(id=pk)

        return render(
            request,
            'lists.html',
            context={
                'lists': lists
            }
        )


class GameCreateView(View):
    def get(self, request):
        result = Results.objects.filter(player_id=self.request.user.id).order_by('-id')
        if result:
            event = Games.objects.get(id=result[0].game_id).event
            points_event = Games.objects.get(id=result[0].game_id).points_event
            list = result[0].list
        else:
            event = ''
            points_event = 4500
            list = 0

        init_game = {
            'event': event,
            'points_event': points_event,
            'date': datetime.now().strftime("%Y-%m-%d")
        }
        form_game = GameForm(initial=init_game)
        init_my_result = {
            'list': list
        }
        init_op_result = {
        }
        form_my_result = MyResultForm(initial=init_my_result, prefix='my')
        form_op_result = OpResultForm(initial=init_op_result, prefix='op')
        return render(
            request,
            'add-game.html',
            context={
                'form_game': form_game,
                'form_my_result': form_my_result,
                'form_op_result': form_op_result
            }
        )

    def post(self, request):
        form_game = forms.GameForm(request.POST)
        form_my_result = forms.MyResultForm(request.POST, prefix='my')
        form_op_result = forms.OpResultForm(request.POST, prefix='op')
        if form_game.is_valid() and form_my_result.is_valid() and form_op_result.is_valid():
            fg = form_game.save(commit=False)
            fg.save()
        else:
            raise ValidationError('Something went wrong.')
        player = self.request.user.id
        form_my_result.instance.player_id = player
        form_my_result.instance.score = self.count_score \
            (form_game.instance.points_event, form_my_result.instance.points, form_op_result.instance.points,
             form_my_result.instance.secondary)
        score = form_my_result.instance.score
        form_my_result.instance.result = 1 if score > 10 else -1 if score < 10 else 0
        form_my_result.instance.game_id = form_game.instance.id
        fmr = form_my_result.save(commit=False)
        fmr.save()

        form_op_result.instance.game_id = form_game.instance.id
        form_op_result.instance.score = 20 - score
        form_op_result.instance.secondary = form_my_result.instance.secondary * -1
        form_op_result.instance.result = form_my_result.instance.result * -1
        form_op_result.instance.first = not form_my_result.instance.first
      #  form_op_result.instance.result = None

        fpr = form_op_result.save(commit=False)
        fpr.save()

        return ResultView.get(self, request, form_game.instance.id)

    def count_score(self, points, my, op, scenario):
        difference = my - op
        fraction = abs(difference / points)
        score = 0
        if fraction <= 0.05:
            score += 10
        elif fraction <= 0.10:
            score += 11
        elif fraction <= 0.20:
            score += 12
        elif fraction <= 0.30:
            score += 13
        elif fraction <= 0.40:
            score += 14
        elif fraction <= 0.50:
            score += 15
        elif fraction <= 0.70:
            score += 16
        else:
            score += 17

        if difference < 0:
            score = 20 - score
        score += 3 * scenario
        return score


class LogoutView(View):
    def get(self, request):
        logout(request)
        return redirect('t9a:home')
