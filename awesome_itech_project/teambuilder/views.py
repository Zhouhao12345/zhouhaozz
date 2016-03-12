from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth import authenticate, login, logout
from teambuilder.forms import UserForm,TeamForm,CourseForm
from teambuilder.models import Team, Course, Memberrequest
from teambuilder.forms import UserForm,TeamForm
from django.contrib.auth.decorators import login_required

# Create your views here.
def index(request):
    teams = Team.objects.order_by('-creation_date')[:5]
    courses = Course.objects.order_by('add_date')[:5]
    context_dict = {}
    context_dict['teams'] = teams
    context_dict['courses'] = courses
    return render(request, 'teambuilder/index.html', context_dict)

def about(request):
    return render(request, 'teambuilder/about.html', {})

def register(request):

    context_dict = {}
    if request.method == 'POST':
        user_form = UserForm(data=request.POST)

        if user_form.is_valid():
            user = user_form.save()
            user.set_password(user.password)
            user.save()
            context_dict['registered'] = True

        else:
            context_dict['errors'] = user_form.errors

    else:
        user_form = UserForm();
        context_dict['user_form'] = user_form

    return render(request, 'teambuilder/register.html', context_dict)

def reset_password(request):
    return render(request, 'teambuilder/reset_password.html', {})

def user_login(request):
    if request.user.is_authenticated():
        return HttpResponseRedirect('/teambuilder/')

    if request.method=='POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)

        if user:
            login(request,user)
            return HttpResponseRedirect('/teambuilder/')

        else:
            return render(request, 'teambuilder/login.html', {'message':'Invalid username/password provided'})
    else:
        return render(request, 'teambuilder/login.html', {})

def user_logout(request):
    logout(request)
    return HttpResponseRedirect('/teambuilder/')

@login_required
def create_team(request):
    context_dict = {}
    if request.method=='POST':
        team_form = TeamForm(data=request.POST)

        if team_form.is_valid():
            user = request.user
            team = team_form.save(commit=False)
            team.creator = user
            team.name = team.name.title()
            team.save()
            context_dict['created'] = True
            return HttpResponseRedirect('/teambuilder/team/'+team.slug+'/details/')

        else:
            context_dict['errors'] = team_form.errors

    else:
        team_form = TeamForm();
        context_dict['team_form'] = team_form
    return render(request, 'teambuilder/create_team.html', context_dict)

def profile(request, username):
    return render(request, 'teambuilder/profile.html', {'username':username})

def edit_profile(request):
    return render(request, 'teambuilder/edit_profile.html', {})

def team_details(request, team_name_slug):

    context_dict = {}
    try:
        team = Team.objects.get(slug=team_name_slug)
        context_dict['team'] = team
        available_slots = team.course.team_size - team.current_size
        context_dict['available_slots'] = available_slots

        #check if user has previously requested to join the team
        user = request.user
        if user.is_authenticated():
            try:
                mr = Memberrequest.objects.get(team=team,user=user,status="pending")
                context_dict['member_request'] = mr

            except Memberrequest.DoesNotExist:
                pass

            #check if user has an already accepted request for that team
            try:
                mr2 = Memberrequest.objects.get(team=team,user=user,status="accepted")
                if mr2:
                    context_dict['accepted_request'] = True

            except Memberrequest.DoesNotExist:
                pass

    except Team.DoesNotExist:
        pass

    return render(request, 'teambuilder/team_detail.html', context_dict)


def find_team(request):
    return render(request, 'teambuilder/find_team.html', {})

@login_required
def add_course(request):
    context_dic= {}
    if request.method=='POST':
        course_form=CourseForm(request.POST)

        if course_form.is_valid():
            course=course_form.save(commit=False)
            course.creator= request.user
            course.save()
            context_dic['created']=True

        else:
            context_dic['errors']=course_form.errors
    else:
        course_form=CourseForm()
        context_dic['course_form']=course_form
    return render(request,'teambuilder/add_course.html',context_dic)

@login_required
def join_team(request, team_name_slug):
    user = request.user
    team = Team.objects.get(slug=team_name_slug)
    Memberrequest.objects.get_or_create(user=user, team=team, status="pending")

    return HttpResponseRedirect('/teambuilder/team/'+team_name_slug+'/details/')

@login_required
def cancel_request(request, team_name_slug):
    user = request.user
    team = Team.objects.get(slug=team_name_slug)
    mr = Memberrequest.objects.get(user=user, team=team, status="pending")
    mr.status = "cancelled"
    mr.save()

    return HttpResponseRedirect('/teambuilder/team/'+team_name_slug+'/details/')

@login_required
def view_requests(request, team_name_slug):
    user = request.user
    team = Team.objects.get(slug=team_name_slug)

    if team.creator == user:
        requests = Memberrequest.objects.filter(team = team).order_by('-request_date')

        return render(request, 'teambuilder/view_requests.html', {'requests':requests, 'team':team})

    else:
        return HttpResponse("You are not authorized to access this page")

@login_required
def accept_request(request, request_id):
    try:
        mr = Memberrequest.objects.get(pk=request_id)
        team = mr.team

        if request.user == team.creator:
            mr.status = "accepted"

            team.current_size = team.current_size + 1
            team.save()
            mr.save()

        else:
            return HttpResponse("You are not authorized to perform this action")

    except Memberrequest.DoesNotExist:
        return HttpResponse("Invalid request ID")

    return HttpResponseRedirect('/teambuilder/team/'+mr.team.slug+'/view-requests/')

@login_required
def reject_request(request, request_id):
    try:
        mr = Memberrequest.objects.get(pk=request_id)
        team = mr.team

        if request.user == team.creator:
            mr.status = "rejected"
            mr.save()

        else:
            return HttpResponse("You are not authorized to perform this action")

    except Memberrequest.DoesNotExist:
        return HttpResponseRedirect("Invalid request ID")

    return HttpResponseRedirect('/teambuilder/team/'+mr.team.slug+'/view-requests/')

@login_required
def my_sent_requests(request):
    user = request.user
    mrs = Memberrequest.objects.filter(user=user).order_by('-request_date')
    return render(request, 'teambuilder/my_sent_requests.html', {'requests':mrs})

@login_required
def view_team_members(request, team_name_slug):
    user = request.user
    context_dict = {}
    try:
        team = Team.objects.get(slug=team_name_slug)
        if team.creator == user:
            requests = Memberrequest.objects.filter(team=team,status="accepted")
            context_dict['requests'] = requests
            context_dict['team'] = team

    except Team.DoesNotExist:
        return HttpResponse("Invalid team provided")

    return render(request, 'teambuilder/view_team_members.html', context_dict)



