from app.features.email_obj import Send_email
from app.features.tasks import tasks
from app.features.calender import calendar_obj, event
# from app.features.google_cred.Google import Create_Service
from app.features.models import user
from app.features.forms import login_form, sign_up_form, edit_profile_form, create_tasks_form, send_email_form, create_event_form
from flask import session, request, flash, redirect, render_template, url_for
from flask_login import login_user, logout_user, fresh_login_required, current_user, login_required
from googleapiclient.errors import HttpError
from app import myapp_obj, db


@myapp_obj.before_request
def create_db():
    db.create_all()

@myapp_obj.route("/")
def landing():
    return render_template('landing.html')

@myapp_obj.route("/login/", methods=['GET', 'POST'])
def login():
    # SECRET_FILE = 'credentials.json'
    # SCOPES = ["https://www.googleapis.com/auth/gmail.send",'https://www.googleapis.com/auth/calendar', ]
    logout_user()
    form = login_form()
    if form.validate_on_submit():
        site_user = user.query.filter_by(username=form.username.data).first()
        if site_user and site_user.check_password(form.password.data) == True:
            login_user(site_user)

            return redirect('/home/')
        else:
            flash("Please register for an account.")
            return render_template('login.html', form=form)
    return render_template('login.html', form=form)

@myapp_obj.route("/logout/")
def logout():
    logout_user()
    flash("You have been logged out.")
    return redirect('/login/')

@myapp_obj.route("/sign_up/",methods = ['POST', 'GET'])
def sign_up():
    logout_user()
    form = sign_up_form()
    if form.validate_on_submit():
        existing_user = user.query.filter_by(username=form.username.data).first()
        if existing_user == None:
            # create new user
            new_user = user(username = form.username.data)
            # pass into set_password()
            new_user.set_password(form.password.data)
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            return redirect("/home/")
        else:
            flash("User name is already registered.")
    return render_template('signup.html', form=form)
    
@myapp_obj.route("/home/", methods=['GET', 'POST'])
@login_required
def home():
    return render_template('test.html', user = current_user)

@myapp_obj.route("/deactivate/", methods = ['POST', 'GET'])
@login_required
def delete_account():
    account = user.query.filter(user.id == current_user.id).first()
    db.session.delete(account)
    db.session.commit()
    flash("Your account has been deactivated.")
    return redirect(url_for('login'))

@myapp_obj.route("/edit_profile/", methods=['GET', 'POST'])
@login_required
def edit_user_profile():
    form = edit_profile_form()
    if form.validate_on_submit():
        user_id = current_user.id 
        # user_var = user.query.filter(user.id == current_user.id)
        user_var = user.query.get_or_404(current_user.id)
        exists = user.query.filter(user.username == form.new_username.data).first() is not None
        if exists:
            flash("Username is already taken")
        else:
            user_var.username = form.new_username.data
            user_var.set_password(form.new_password.data)
            db.session.add(user_var)
            db.session.commit()
            return redirect('/home/')
    return render_template('edit_profile.html', form=form)


@myapp_obj.route("/send_email/", methods=['GET', 'POST'])
@login_required
def send_email_pop():
    form = send_email_form()
    if form.validate_on_submit():
        subject = form.subject.data
        recipient = form.recipient.data
        body = form.body.data
        samp = Send_email()
        samp.add_recipient(recipient)
        samp.set_body_text(body)
        samp.set_subject_text(subject)
        samp.send()
        flash("Your email has been sent.")
        return redirect('/home/')
    return render_template('send_email.html', form = form)

@myapp_obj.route("/tasks/",methods = ['POST', 'GET'])
@login_required
def create_tasks():
    form = create_tasks_form()
    if form.validate_on_submit():
        title = form.title.data
        body = form.task_subject.data
        email = form.email.data
        obj = tasks()
        creds = obj.get_cred(email)
        if creds:
            obj.submit(creds)
            obj.insert_tasklist(title)
            obj.add_task(body, title)
            flash("Task has been added, check your google tasks")
            return redirect("/home/")
        else:
            flash("Something went wrong. Try again later.")
    return render_template('create_tasks.html', form=form)

@myapp_obj.route("/events/",methods = ['POST', 'GET'])
@login_required
def add_event():
    form = create_event_form()
    if form.validate_on_submit():
        mycal = calendar_obj()
        my_event = event(form.title.data)
        my_event.add_attendee(form.attendees.data)
        my_event.set_start_time(form.start_time.data)
        my_event.set_end_time(form.end_time.data)
        try:
            mycal.add_event(my_event)
            flash("Event has been added, check your google calendar")
            return redirect("/home/")
        except HttpError:
            flash("Invalid Event")
    return render_template('event_form.html', form=form)
