import csv
import re
from datetime import datetime

from allauth.socialaccount.models import SocialAccount
from django.contrib.auth import get_user_model, logout
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import View
from django.core.mail import send_mail

from . import forms
from .forms import UsernameForm, GameForm, MyResultForm, OpResultForm, AddListForm, ApproveResultForm, MyHalfResultForm, \
    OpHalfResultForm, AddListToResultForm, UnitsPointsForm, MyUnitPointsResultForm
from .helpers import Ranking, ListParser, HelpFunctions, SendEmail
from .models import Results, Lists, Games, Army, UserRenamed, GamingGroup, Units, ListsUnits, HalfResults, UnitsPoints


class HomeView(View):
    def get(self, request):
        renamed = True
        if self.request.user.id:
            if not UserRenamed.objects.filter(user_id=self.request.user.id).exists() \
                    and SocialAccount.objects.filter(user_id=self.request.user.id).exists():
                renamed = False

        head = '9th age results'
        to_be_approved = Results.objects.filter(Q(approved__isnull=True) & Q(player_id=self.request.user.id))
        my_results = Results.objects.filter(Q(player_id=self.request.user.id)).values('game_id')
        waiting_for_approval = Results.objects.filter(
            Q(approved__isnull=True) & ~Q(player_id=self.request.user.id) & Q(game_id__in=my_results))
        for r in to_be_approved:
            r.opponent = Results.objects.get(~Q(player_id=r.player_id)
                                             & Q(game_id=r.game_id))
        for r in waiting_for_approval:
            r.myself = Results.objects.get(~Q(player_id=r.player_id)
                                           & Q(game_id=r.game_id))

        list_to_be_added = HalfResults.objects.filter(
            Q(list_id__isnull=True) & Q(player_id=self.request.user.id) & Q(closed=False))
        for r in list_to_be_added:
            r.opponent = HalfResults.objects.get(~Q(player_id=r.player_id)
                                                 & Q(game_id=r.game_id))
        half_results = HalfResults.objects.filter(
            Q(player_id=self.request.user.id) & ~Q(closed=True) & Q(list_id__isnull=False))
        for r in half_results:
            r.opponent = HalfResults.objects.get(~Q(player_id=r.player_id)
                                                 & Q(game_id=r.game_id))

        rankingL = Ranking(Lists)
        rankingA = Ranking(Army)
        rankingP = Ranking(User)
        results = Results.objects.filter(approved__isnull=False)

        for r in results:
            rankingL.add(r.list_id, r.result, r.score)
            rankingA.add(r.list.army_id, r.result, r.score)
            rankingP.add(r.player_id, r.result, r.score)

        return render(
            request,
            'home.html',
            context={
                'rankings': [
                    {
                        'name': "Players",
                        'id': "table-players",
                        'sortable': True,
                        'ranking': rankingP.get_list(),
                    },
                    {
                        'name': "Armies",
                        'id': "table-armies",
                        'sortable': True,
                        'ranking': rankingA.get_list(),
                    },
                    {
                        'name': "Lists",
                        'id': "table-lists",
                        'sortable': True,
                        'ranking': rankingL.get_list(),
                    }
                ],
                'to_be_approved': to_be_approved,
                'waiting_for_approval': waiting_for_approval,
                'list_to_be_added': list_to_be_added,
                'head': head,
                'user_renamed': renamed,
                'half_results': half_results,
            }
        )


class ApproveResultView(LoginRequiredMixin, View):
    def get(self, request, pk=0):
        head = 'Approve result'
        result = Results.objects.get(id=pk)
        list = 0
        if isinstance(result.list_id, int):
            list = result.list
        else:
            help_result = Results.objects.filter(Q(player_id=self.request.user.id) & Q(list_id__isnull=False)).order_by(
                '-id')
            if help_result:
                list = help_result[0].list
        initial = {
            'list': list,
            'approved': True,
        }
        form = ApproveResultForm(initial=initial, instance=result)
        if isinstance(result.list_id, int):
            form.fields['list'].queryset = Lists.objects.filter(id=result.list_id)
        else:
            form.fields['list'].queryset = Lists.objects.filter(
                owner_id=self.request.user.id)  # shows only my lists, modify options on the fly

        return render(
            request,
            'approve-result.html',
            context={
                'form': form,
                'head': head
            }
        )

    def post(self, request, pk=0):
        form = forms.ApproveResultForm(request.POST)
        if form.is_valid():

            check_list = Lists.objects.filter(Q(id=form.instance.list_id) & Q(owner_id=self.request.user.id)).count()
            result = Results.objects.get(id=pk)
            if check_list == 1 and result.player_id == self.request.user.id:
                result.approved = form.instance.approved
                result.list_id = form.instance.list_id
                result.comment = form.instance.comment
                result.save()
            return redirect('t9a:home')


class ChangeUsernameView(LoginRequiredMixin, View):
    def get(self, request, opt="nothing"):
        if opt == "disregard":
            u_r = UserRenamed.objects.create(user_id=self.request.user.id, old_username=self.request.user.username,
                                             new_username=self.request.user.username)
            return redirect('t9a:home')

        head = 'My account'
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
                'form': form,
                'head': head
            }
        )

    def post(self, request):
        user = get_user_model().objects.get(id=self.request.user.id)
        old_username = self.request.POST.get('username')
        username = self.request.POST.get('new_username')
        user.username = username
        user.save()
        u_r = UserRenamed.objects.create(user_id=self.request.user.id, old_username=old_username, new_username=username)

        return redirect('t9a:home')


class ResultView(LoginRequiredMixin, View):
    def get(self, request, pk=""):

        if pk == "":
            my_result = Results.objects.filter(player_id=self.request.user.id)
            head = 'My results'
        else:
            head = 'Results'
            check = re.match('user:(\d+)', pk)
            if check:
                my_result = Results.objects.filter(player_id=int(check.group(1)))
            check = re.match('lists:(\d+)', pk)
            if check:
                lists = Lists.objects.filter(id=int(check.group(1)))
                my_result = Results.objects.filter(list_id__in=lists)
            check = re.match('army:(\d+)', pk)
            if check:
                lists = Lists.objects.filter(army_id=int(check.group(1)))
                game_id = Results.objects.filter(Q(list_id__in=lists)).values_list('game_id', flat=True)
                my_result = Results.objects.filter(Q(game_id__in=game_id) & Q(first=True))

        for r in my_result:
            r.opponent = Results.objects.get(~Q(player_id=r.player_id)
                                             & Q(game_id=r.game_id))
        return render(
            request,
            'results.html',
            context={
                'results': my_result,
                'head': head
            }
        )


class ListsView(LoginRequiredMixin, View):
    def get(self, request, pk=0):
        if pk == 0:
            head = 'My lists'
        else:
            head = 'List details'
        my_list = Lists.objects.filter(Q(owner_id=self.request.user.id) & Q(id=pk))
        if pk == 0:
            lists = Lists.objects.filter(owner_id=self.request.user.id)
        elif my_list:
            lists = my_list
        elif self.request.user.is_superuser:
            lists = Lists.objects.filter(id=pk)
        else:
            # if pk exists in approved result in game I played
            my_games = Results.objects.filter(Q(player_id=self.request.user.id) & Q(approved=True)).values_list(
                'game_id', flat=True)
            list_games = Results.objects.filter(Q(list_id=pk) & Q(approved=True)).values_list('game_id', flat=True)
            if set(my_games) & set(list_games):
                lists = Lists.objects.filter(id=pk)
            else:
                lists = []

        return render(
            request,
            'lists.html',
            context={
                'lists': lists,
                'head': head
            }
        )


class ParseList(LoginRequiredMixin, View):
    def get(self, request, pk):
        head = 'List parser'
        list = Lists.objects.get(id=pk)
        parser = ListParser()
        parsed_list = parser.parser(list.list)
        if not list.parsed:
            for pl in parsed_list:
                if Units.objects.filter(Q(unit=pl['unit']) & Q(points=pl['points'])).exists():
                    unit = Units.objects.get(Q(unit=pl['unit']) & Q(points=pl['points']))
                else:
                    unit = Units.objects.create(unit=pl['unit'], points=pl['points'], special=pl['special'],
                                                army=list.army)
                ListsUnits.objects.create(unit=unit, list=list, owner=list.owner)
            list.parsed = True
            list.save()
        return render(
            request,
            'parse-list.html',
            context={
                'head': head,
                'parsed_list': parsed_list
            }
        )


class AddListView(LoginRequiredMixin, View):
    def get(self, request, pk=0):
        if pk == 0:  # if there's no list view add new list
            head = 'Add list'
            form = AddListForm()
        else:
            head = 'Edit list'
            form = AddListForm(instance=Lists.objects.get(
                Q(id=pk) & Q(owner_id=self.request.user.id)))  # if list exist and list.id occurs in results
            if len(Results.objects.filter(list_id=pk)) > 0:  # field 'list' is read only in form
                form.fields['list'].disabled = True
                form.fields['army'].disabled = True

        return render(
            request,
            'add-list.html',
            context={
                'form': form,
                'head': head
            }
        )

    def post(self, request, pk=0):
        form = {}
        if pk != 0:  # if list exist return that list
            list = Lists.objects.get(Q(id=pk) & Q(owner_id=self.request.user.id))
            if list:
                if len(Results.objects.filter(list_id=list.id)) > 0:  # if list is connection with results,
                    POST = request.POST.copy()  # it's display and don't send in POST
                    POST['list'] = list.list  # we copy POST and overwrite value field 'list'
                    POST['army'] = list.army
                    form = AddListForm(POST)
        if not form:
            form = AddListForm(request.POST)
        owner = self.request.user.id
        if form.is_valid():
            if pk != 0:
                list = Lists.objects.get(Q(id=pk) & Q(owner_id=self.request.user.id))
                if list:
                    form.instance.id = list.id
                    if len(Results.objects.filter(list_id=list.id)) > 0:
                        form.instance.list = list.list
            form.instance.owner_id = owner
            form.save()
        return ListsView.get(self, request, form.instance.id)


class GameCreateView(LoginRequiredMixin, View):  # view to add games and results
    def get(self, request):
        head = 'Add game'
        result = Results.objects.filter(player_id=self.request.user.id).order_by('-id')
        if result:  # in form is displayed last  introduced value
            event = Games.objects.get(id=result[0].game_id).event
            points_event = Games.objects.get(id=result[0].game_id).points_event
            event_type = Games.objects.get(id=result[0].game_id).event_type
            list = result[0].list
        else:
            event = ''
            points_event = 4500
            list = 0
            event_type = 'test'

        init_game = {  # init value to game form
            'event': event,
            'points_event': points_event,
            'date': datetime.now().strftime("%Y-%m-%d"),
            'event_type': event_type
        }
        form_game = GameForm(initial=init_game)
        init_my_result = {  # init value to my result form
            'list': list
        }
        init_op_result = {
        }
        form_my_result = MyResultForm(initial=init_my_result, prefix='my')  # we used prefix to distinctions form
        form_my_result.fields['list'].queryset = Lists.objects.filter(
            owner_id=self.request.user.id)  # shows only my lists, modify options on the fly
        form_op_result = OpResultForm(initial=init_op_result, prefix='op')  # there are that same fields
        form_op_result.fields['player'].queryset = get_user_model().objects.filter(
            ~Q(id=self.request.user.id)).order_by('username')
        return render(
            request,
            'add-game.html',
            context={
                'form_game': form_game,
                'form_my_result': form_my_result,
                'form_op_result': form_op_result,
                'head': head,
                'save_name': 'add-game'
            }
        )

    def post(self, request):
        form_game = forms.GameForm(request.POST)
        form_my_result = forms.MyResultForm(request.POST, prefix='my')
        form_op_result = forms.OpResultForm(request.POST, prefix='op')
        if form_game.is_valid() and form_my_result.is_valid() and form_op_result.is_valid():
            fg = form_game.save(commit=False)  # first we save game form because results have FG to game
            fg.save()
        else:
            raise ValidationError('Something went wrong.')
        player = self.request.user.id
        form_my_result.instance.player_id = player
        count_score = HelpFunctions()
        form_my_result.instance.score = count_score.count_score \
            (form_game.instance.points_event, form_my_result.instance.points, form_op_result.instance.points,
             form_my_result.instance.secondary)
        score = form_my_result.instance.score
        form_my_result.instance.result = 1 if score > 10 else -1 if score < 10 else 0
        form_my_result.instance.game_id = form_game.instance.id
        form_my_result.instance.approved = True
        fmr = form_my_result.save(commit=False)
        fmr.save()

        form_op_result.instance.game_id = form_game.instance.id  # we assign value to opponent result based on our form
        form_op_result.instance.score = 20 - score
        form_op_result.instance.secondary = form_my_result.instance.secondary * -1
        form_op_result.instance.result = form_my_result.instance.result * -1
        form_op_result.instance.first = not form_my_result.instance.first
        #  form_op_result.instance.result = None

        fpr = form_op_result.save(commit=False)
        fpr.save()

        fpr.auto_approve(fmr.comment)
        send_email = SendEmail()
        send_email.send_approval_email(fpr.player.email,
                                       request.build_absolute_uri(reverse('t9a:approve-result', kwargs={'pk': fpr.id})),
                                       fpr.player.username)  # there is no exception handling because function
        # doesn't return error when email address doesn't exist

        return redirect('t9a:home')


class AddGameHalfView(LoginRequiredMixin, View):
    def get(self, request):
        head = 'Add game'
        result = Results.objects.filter(player_id=self.request.user.id).order_by('-id')
        if result:  # in form is displayed last  introduced value
            event = Games.objects.get(id=result[0].game_id).event
            points_event = Games.objects.get(id=result[0].game_id).points_event
            event_type = Games.objects.get(id=result[0].game_id).event_type
            list = result[0].list
        else:
            event = ''
            points_event = 4500
            list = 0
            event_type = 'test'

        init_game = {  # init value to game form
            'event': event,
            'points_event': points_event,
            'date': datetime.now().strftime("%Y-%m-%d"),
            'event_type': event_type
        }
        form_game = GameForm(initial=init_game)
        init_my_result = {  # init value to my result form
            'list': list
        }
        form_my_result = MyHalfResultForm(initial=init_my_result, prefix='my')  # we used prefix to distinctions form
        form_my_result.fields['list'].queryset = Lists.objects.filter(
            Q(owner_id=self.request.user.id) & Q(parsed=True))  # shows only my lists, modify options on the fly
        form_op_result = OpHalfResultForm(prefix='op')  # there are that same fields
        form_op_result.fields['player'].queryset = get_user_model().objects.filter(
            ~Q(id=self.request.user.id)).order_by('username')

        return render(
            request,
            'add-game.html',
            context={
                'form_game': form_game,
                'form_my_result': form_my_result,
                'form_op_result': form_op_result,
                'head': head,
                'save_game': 'add-short-game',
            }
        )

    def post(self, request):
        form_game = forms.GameForm(request.POST)
        form_my_result = forms.MyHalfResultForm(request.POST, prefix='my')
        form_op_result = forms.OpHalfResultForm(request.POST, prefix='op')
        if form_game.is_valid() and form_my_result.is_valid() and form_op_result.is_valid():
            fg = form_game.save(commit=False)  # first we save game form because results have FG to game
            fg.save()
        else:
            raise ValidationError('Something went wrong.')
        player = self.request.user.id
        form_my_result.instance.player_id = player
        form_my_result.instance.game_id = form_game.instance.id
        fmr = form_my_result.save(commit=False)
        fmr.save()

        form_op_result.instance.game_id = form_game.instance.id  # we assign value to opponent result based on our form
        #  form_op_result.instance.result = None

        fpr = form_op_result.save(commit=False)
        fpr.save()

        return redirect('t9a:home')


class AddListToResultView(LoginRequiredMixin, View):
    def get(self, request, pk=0):
        head = 'Add list to result'
        result = Results.objects.filter(player_id=self.request.user.id).order_by('-id')
        if result:  # in form is displayed last  introduced value
            list = result[0].list
        else:
            list = 0
        result = HalfResults.objects.get(id=pk)
        initial = {
            'list': list,
        }
        form = AddListToResultForm(initial=initial)
        form.fields['list'].queryset = Lists.objects.filter(
            Q(owner_id=self.request.user.id) & Q(parsed=True))  # shows only my lists, modify options on the fly

        return render(
            request,
            'approve-result.html',
            context={
                'form': form,
                'head': head
            }
        )

    def post(self, request, pk):
        result = HalfResults.objects.get(Q(id=pk) & Q(player_id=self.request.user.id))
        form = AddListToResultForm(request.POST, instance=result)

        if form.is_valid():
            form.save()
        return redirect('t9a:home')


class AddUnitsPointsView(LoginRequiredMixin, View):
    def get(self, request, pk):
        head = 'Add unit points'
        game = Games.objects.get(id=pk)
        my_comment = HalfResults.objects.get(Q(game_id=pk) & Q(player_id=self.request.user.id)).comment
        form_game = GameForm(instance=game)
        my_list = HalfResults.objects.get(Q(game_id=game.id) & Q(player_id=self.request.user.id))
        op_list = HalfResults.objects.get(Q(game_id=game.id) & ~Q(player_id=self.request.user.id))
        my_units = ListsUnits.objects.filter(Q(list_id=my_list.list_id))
        op_units = ListsUnits.objects.filter(Q(list_id=op_list.list_id))
        my_form_res = MyUnitPointsResultForm(initial={'comment': my_comment})
        return render(
            request,
            'units-points.html',
            context={
                'my_list.id': my_list.id,
                'form_game': form_game,
                'my_list': my_list,
                'my_form_res': my_form_res,
                'op_list': op_list,
                'my_units': my_units,
                'op_units': op_units,
                'head': head
            }
        )

    def post(self, request, pk):
        form_game = forms.GameForm(request.POST, instance=Games.objects.get(id=pk))
        my_form_res = forms.MyUnitPointsResultForm(request.POST)
        if form_game.is_valid():
            form_game.save()
        if not my_form_res.is_valid():
            raise ("błąd")
        player = self.request.user.id
        game_id = form_game.instance.id
        count_score = HelpFunctions()
        my_points = int(request.POST.get('my-sum'))
        op_points = int(request.POST.get('op-sum'))
        my_half_result = HalfResults.objects.get(Q(game_id=pk) & Q(player_id=self.request.user.id))
        op_half_result = HalfResults.objects.get(Q(game_id=pk) & ~Q(player_id=self.request.user.id))
        opponent = op_half_result.player_id
        my_list = my_half_result.list_id
        op_list = op_half_result.list_id
        if my_points < 0 and op_points < 0:
            temp = my_points
            my_points = -1 * op_points
            op_points = -1 * temp
        my_score = count_score.count_score \
            (form_game.instance.points_event, my_points, op_points, my_form_res.instance.secondary)
        result = 1 if my_score > 10 else -1 if my_score < 10 else 0

        my_result = Results.objects.create(
            game_id=game_id,
            player_id=player,
            secondary=my_form_res.instance.secondary,
            score=my_score,
            result=result,
            points=my_points,
            list_id=my_list,
            first=my_form_res.instance.first,
            comment=my_form_res.instance.comment,
            approved=True,
        )
        op_result = Results.objects.create(
            game_id=game_id,
            player_id=opponent,
            secondary=my_form_res.instance.secondary * -1,
            score=20 - my_score,
            result=result * -1,
            points=op_points,
            list_id=op_list,
            first=not my_form_res.instance.first,
            comment=op_half_result.comment,
        )

        my_half_result.closed = True
        my_half_result.save()
        op_half_result.closed = True
        op_half_result.save()

        unit = HelpFunctions()
        unit.create_unit_points(request, 'my-', my_list, my_result.id)
        unit.create_unit_points(request, 'op-', op_list, op_result.id)

        op_result.auto_approve(my_result.comment)

        return redirect('t9a:home')


class AllResultsView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        return redirect('t9a:home')

    def get(self, request, pk=0):
        head = 'All results'

        waiting_for_approval = Results.objects.filter(Q(approved__isnull=True))
        for r in waiting_for_approval:
            r.myself = Results.objects.get(~Q(player_id=r.player_id) & Q(game_id=r.game_id))

        if self.request.GET.get("q") is None:
            all_results = Results.objects.all()
            query = ''
        else:
            query = self.request.GET.get("q")
            player = User.objects.filter(Q(username__icontains=query)).values("id")
            list = Lists.objects.filter(Q(name__icontains=query)).values("id")
            army = Army.objects.filter(Q(name__icontains=query)).values("id")
            all_results = Results.objects.filter(
                Q(player_id__in=player) | Q(list_id__in=list)  # | Q(army_id__in=army)
            )
        duplicates = []
        for r in all_results:
            if r.game_id in duplicates:
                r = None
            else:
                r.opponent = Results.objects.get(~Q(player_id=r.player_id)
                                                 & Q(game_id=r.game_id))
                duplicates.append(r.game_id)
        return render(
            request,
            'all-results.html',
            context={
                'results': all_results,
                'query': query,
                'head': head,
                'waiting_for_approval': waiting_for_approval,
            }
        )


class LogoutView(View):
    def get(self, request):
        logout(request)
        return redirect('t9a:home')


class CSVView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        return redirect('t9a:home')

    # Create the HttpResponse object with the appropriate CSV header.
    def get(self, request):
        filename = 'all-results-' + datetime.now().strftime('%Y-%m-%d') + '.csv'
        response = HttpResponse(
            content_type='text/csv',
            headers={'Content-Disposition': f'attachment; filename="{filename}"'},
        )

        writer = csv.writer(response)
        games = Games.objects.all()
        writer.writerow(Games().csv_array_header() + Results().csv_array_header())
        for g in games:
            results = Results.objects.filter(Q(game_id=g.id) & Q(approved=True))
            game_part = g.csv_array()
            for r in results:
                writer.writerow(game_part + r.csv_array())

        return response


class AddGamingGroup(LoginRequiredMixin, View):
    def get(self, request):
        head = 'Add group'
        form = forms.AddGamingGroupForm
        return render(
            request,
            'add-gaming-group.html',
            context={
                'form': form,
                'head': head
            }
        )

    def post(self, request):
        form = forms.AddGamingGroupForm(request.POST)
        if form.is_valid():
            form.save()

        return redirect('t9a:list-groups')


class GamingGroupListView(LoginRequiredMixin, View):
    def get(self, request):
        head = 'List groups'
        groups = GamingGroup.objects.all()
        for g in groups:
            g.flat_members = list(g.members.values_list('username', flat=True))
            g.iamin = self.request.user.username in g.flat_members

        return render(
            request,
            'list-groups.html',
            context={
                'groups': groups,
                'head': head
            }

        )


class JoinGroupView(LoginRequiredMixin, View):

    def get(self, request, pk):
        group = GamingGroup.objects.get(id=pk)
        member = get_user_model().objects.get(id=self.request.user.id)
        group.members.add(member)

        return redirect('t9a:list-groups')

    def post(self, request, pk):
        return self.get(request, pk)


class LeaveGroupView(LoginRequiredMixin, View):

    def get(self, request, pk):
        group = GamingGroup.objects.get(id=pk)
        member = get_user_model().objects.get(id=self.request.user.id)
        group.members.remove(member)

        return redirect('t9a:list-groups')

    def post(self, request, pk):
        return self.get(request, pk)


class GroupRankingView(LoginRequiredMixin, View):
    def get(self, request, pk):
        group = GamingGroup.objects.get(id=pk)
        head = f'Rankings for {group}'
        members = group.members.values_list('id', flat=True)
        results = Results.objects.filter(Q(player_id__in=members) & Q(approved=True))

        rankingI = Ranking(User)
        rankingE = Ranking(User)
        rankingA = Ranking(User)

        for r in results:
            is_opponent_in_group = Results.objects.filter(
                ~Q(player_id=r.player_id) & Q(player_id__in=members) & Q(game_id=r.game_id)
            ).count()
            rankingA.add(r.player_id, r.result, r.score)
            if is_opponent_in_group == 0:
                rankingE.add(r.player_id, r.result, r.score)
            else:
                rankingI.add(r.player_id, r.result, r.score)

        return render(
            request,
            'group-ranking.html',
            context={
                'rankings': [
                    {
                        'name': "Internal",
                        'id': "table-internal",
                        'sortable': True,
                        'ranking': rankingI.get_list(),
                    },
                    {
                        'name': "External",
                        'id': "table-external",
                        'sortable': True,
                        'ranking': rankingE.get_list(),
                    },
                    {
                        'name': "All",
                        'id': "table-all",
                        'sortable': True,
                        'ranking': rankingA.get_list(),
                    },
                ],
                'head': head,
            }
        )
