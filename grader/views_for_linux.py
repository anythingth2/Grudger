import datetime
import subprocess
import time
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render, render_to_response
from django.template import RequestContext
from django.utils import timezone
from .models import Student, Problem, Submission, ProblemCategorie, Lesson
from .forms import ProblemForm, Profile_PicForm
# Create your views here.

def generate_submission(request):
	student = Student.objects.get(user = request.user)
	problem_list = Problem.objects.all()
	for problem in problem_list:
		try:
			ps = Submission.objects.get(student = student, problem = problem)
		except:
			ps = Submission(student = student, problem = problem)
			ps.save()


@login_required(login_url='/login/')
def dashboard(request):
	data = {'page': 'dashboard'}
	data['user'] = request.user
	try:
		student = Student.objects.get(user = request.user)
	except:
		student = Student(user=request.user)
		student.nick_name = user.username
		student.save()
	data['student'] = student
	generate_submission(request)
	data['unseen'] = len(Submission.objects.all().filter(student = student, seen = False))
	return render(request, "dashboard.html", data)

@login_required(login_url='/login/')
def setting(request):
	data = {'page': 'setting'}
	data['user'] = request.user
	student = Student.objects.get(user = request.user)
	data['student'] = student
	error_message = ''
	if request.method == 'POST':
		if 'profilepic' in request.POST:
			form = Profile_PicForm(request.POST, request.FILES)
			pic = request.FILES['profile_pic']
			student.profile_pic = pic
			student.save()
			print('profilepic')
		elif 'general' in request.POST:
			firstname = request.POST.get('firstname', False)
			lastname = request.POST.get('lastname', False)
			email = request.POST.get('email', False)
			nick = request.POST.get('nick', False)
			user.first_name = firstname
			user.last_name = lastname
			user.email = email
			student.nick_name = nick
			student.save()
			user.save()
			print(firstname + ' ' + lastname + '  ' + email)
		elif 'password-changed' in request.POST:
			old = request.POST.get('old-pass', False)
			new1 = request.POST.get('new-pass1', False)
			new2 = request.POST.get('new-pass2', False)
			if user.check_password(old) == True:
				if new1 == new2:
					user.set_password(new1)
					user.save()
					return HttpResponseRedirect('/login/')
				else:
					error_message = 'New password do not match'
			else:
				error_message = 'Your old password is not correct'
	data['form'] = Profile_PicForm()
	data['error_message'] = error_message
	generate_submission(request)
	data['unseen'] = len(Submission.objects.all().filter(student = student, seen = False))
	return render(request, 'setting.html', data)


@login_required(login_url='/login/')
def gradebook(request):
	data = {'page': 'gradebook'}
	data['user'] = request.user
	student = Student.objects.get(user = request.user)
	data['student'] = student
	cata_list = ProblemCategorie.objects.all()
	score_list = []
	total = 0
	data['cata_list'] = cata_list
	print('cata_list')
	print(cata_list)
	for cata in cata_list:
		problem_list = Problem.objects.filter(catagories = cata)
		if not problem_list:
			print('empty problem_list in ' + cata.name)
			score_list.append(0)
			total += 0
		else:
			score_user = 0
			score_total = 0
			print('Cata: ' + cata.name + '\n-------------------------')
			for prob in problem_list:
				try:
					mysub = Submission.objects.get(student = student, problem = prob)
				except:
					mysub = Submission(student = student, problem = prob)
					mysub.save()
				score_user += mysub.user_score
				score_total += prob.total_score
				print(str(prob) + ' : ' + str(score_user) + ' : ' + str(score_total))
			try:
				perc = score_user/float(score_total)
			except:
				perc = 0
			print(perc)
			score_list.append(int(perc*100))
			print('Score List: ' + str(score_list))
			total += ((score_user / score_total)*cata.weight)
	score_list.append(total)
	data['score_list'] = score_list
	generate_submission(request)
	data['unseen'] = len(Submission.objects.all().filter(student = student, seen = False))
	return render(request, 'gradebook.html', data);


@login_required(login_url='/login/')
def syllabus(request):
	data = {'page': 'syllabus'}
	data['lesson_list'] = Lesson.objects.all()
	data['user'] = request.user
	try:
		student = Student.objects.get(user = request.user)
	except:
		student = Student(user=request.user)
		student.nick_name = user.username
		student.save()
	data['student'] = student
	generate_submission(request)
	data['unseen'] = len(Submission.objects.all().filter(student = student, seen = False))
	return render(request, "syllabus.html", data)


@login_required(login_url='/login/')
def problem_list(request):
	data = {'page': 'problem'}
	data['user'] = request.user
	student = Student.objects.get(user = request.user)
	data['student'] = student
	problem_list = Problem.objects.all()
	sub_prob = []
	for problem in problem_list:
		ps = Submission.objects.get(student = student, problem = problem)
		print('Active: ' + str(problem.catagories.due >= timezone.now() and problem.catagories.start <= timezone.now()))
		active = problem.catagories.due >= timezone.now() and problem.catagories.start <= timezone.now()
		sub_prob.append({'problem': problem, 'submission': ps, 'active': active})
	data['sub_prob_list'] = sub_prob
	data['unseen'] = len(Submission.objects.all().filter(student = student, seen = False))
	return render(request, 'problem_list.html', data)


@login_required(login_url='/login/')
def problem(request, problem_id):
	data = {'page': 'problem'}
	data['user'] = request.user
	student = Student.objects.get(user = request.user)
	data['student'] = student
	problem = Problem.objects.get(id = problem_id)
	data['problem'] = problem
	error_message = ''
	active = problem.catagories.due >= timezone.now() and problem.catagories.start <= timezone.now()
	if not active:
		error_message = 'Now This Problem Is Not Active'
	mysub = Submission.objects.get(student = student, problem = problem)
	mysub.seen = True
	data['mysub'] = mysub
	timeout = 0
	if request.method == 'POST' and active == True:
		form = ProblemForm(request.POST, request.FILES)
		if form.is_valid():
			student.score -= mysub.user_score
			mysub.user_score = 0
			testcases = problem.testcase_set.all()
			ufile = request.FILES['user_file']
			mysub.user_file = ufile
			mysub.save()
			print("gcc ./progfile/" + mysub.user_file.name[2:] + " -o opt")
			task0 = subprocess.Popen(shlex.split("gcc ./progfile/" + mysub.user_file.name[2:] + " -o opt"))
			task0.wait()
			# if compile not error V
			if task0.returncode == 0: 
				mysub.result = ''
				for case in testcases:
					task1 = subprocess.Popen(shlex.split("./opt"), stdout=subprocess.PIPE, stdin=subprocess.PIPE)
					# task1.stdin.write(case.case_input.encode('utf-8'))
					try:
						out, err = task1.communicate(input=case.case_input.encode('utf-8'), timeout = 3)
					# If it's timeout
					except:
						print('It\'s Timeout')
						mysub.result = 'Timeout'
						mysub.user_score = 0
						task1.kill()
						chk_0 = task0.poll()
						while chk_0 == None:
							task0.kill()
							time.sleep(1)
							chk_0 = task1.poll()
						print('Poll0: ->' + str(task0.poll()))
						chk_1 = task1.poll()
						while chk_1 == None:
							task1.kill()
							time.sleep(1)
							chk_1 = task1.poll()
						print('Poll1: ->' + str(task1.poll()))
						break
					print(repr(out.decode('ascii').replace('\r', ''))+'\n'+repr(case.case_output.replace('\r', '')))
					if(repr(out.decode('ascii').replace('\r', '')) == repr(case.case_output.replace('\r', ''))):
						mysub.result += 'P '
						mysub.user_score += problem.score_per_case
					else:
						mysub.result +='- '
					if task1.poll() == None:
						task1.kill()

				# Killing task_0
				chk_0 = task0.poll()
				while chk_0 == None:
					task0.kill()
					time.sleep(1)
					chk_0 = task0.poll()
				print('Task0.poll: ' + str(task0.poll()) + '\n')
				# Killing Task_1
				chk_1 = task1.poll()
				while chk_1 == None:
					task1.kill()
					time.sleep(1)
					chk_1 = task1.poll()
				print('Task1.poll: ' + str(task1.poll()))
			# if compile Error
			else:
				mysub.result = 'Compile Error'
				mysub.user_score = 0
			print(mysub.result+'\n'+str(mysub.user_score)+'/'+str(problem.total_score))
			student.score += mysub.user_score
			student.save()
			mysub.save()
			return HttpResponseRedirect('/grader/problem/'+problem_id+'/')
	else:
		data['form'] = ProblemForm()
		#Remove OPT
		# task3 = subprocess.Popen("rm -f opt.exe", shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
		# task3.wait(timeout=None)
	mysub.save()
	data['unseen'] = len(Submission.objects.all().filter(student = student, seen = False))
	return render(request, 'problem.html', data)