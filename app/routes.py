from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, request, jsonify, flash, abort, session
from flask_login import login_user, logout_user, current_user, login_required
from urllib.parse import urlparse, urljoin
from app import db, limiter
from app.models import User, StudentProfile, SecurityLog
from app.forms import LoginForm, RegistrationForm, ProfileCompletionForm, AdminAddStudentForm, AdminEditStudentForm
from app.utils import admin_required, log_security_event, sanitize_input

# Définition des Blueprints
main_bp = Blueprint('main', __name__)
auth_bp = Blueprint('auth', __name__)
admin_bp = Blueprint('admin', __name__)

# ==================== MIDDLEWARE & FILTRES DE SÉCURITÉ ====================

@main_bp.before_app_request
def force_profile_completion_and_session_settings():
    """
    Hook de pré-requête global :
    1. Active la persistance des sessions (pour appliquer le délai d'expiration).
    2. Empêche un étudiant connecté n'ayant pas de profil de naviguer ailleurs 
       que sur la page de complétion ou de déconnexion.
    """
    # 1. Rendre la session permanente pour appliquer le délai d'expiration de 15 minutes
    session.permanent = True

    # Ignorer la redirection pour les fichiers statiques
    if request.endpoint == 'static':
        return

    # 2. Forcer la complétion du profil pour les étudiants uniquement
    if current_user.is_authenticated and not current_user.is_admin:
        # Vérifie si le profil existe
        profile_exists = current_user.student_profile is not None
        
        # Liste des endpoints autorisés tant que le profil n'est pas rempli
        allowed_endpoints = [
            'main.complete_profile',
            'auth.logout',
            'static'
        ]
        
        if not profile_exists and request.endpoint not in allowed_endpoints:
            flash("Please complete your student profile before accessing the application.", "warning")
            return redirect(url_for('main.complete_profile'))


# Fonction auxiliaire pour rediriger de manière sécurisée (évite les redirections ouvertes)
def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc


# ==================== ROUTE PRINCIPALES (MAIN BLUEPRINT) ====================

@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('admin.admin_dashboard'))
        return redirect(url_for('main.dashboard'))
    return render_template('index.html')


@main_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.is_admin:
        return redirect(url_for('admin.admin_dashboard'))
    return render_template('dashboard.html', user=current_user, profile=current_user.student_profile)


@main_bp.route('/complete-profile', methods=['GET', 'POST'])
@login_required
def complete_profile():
    # Si l'utilisateur est admin, il n'a pas besoin de compléter un profil étudiant
    if current_user.is_admin:
        return redirect(url_for('admin.admin_dashboard'))

    # Si le profil est déjà complété, rediriger vers le dashboard
    if current_user.student_profile:
        flash("Your profile is already complete.", "info")
        return redirect(url_for('main.dashboard'))

    form = ProfileCompletionForm()
    if form.validate_on_submit():
        # Assainissement des données pour éviter les injections HTML
        clean_matricule = sanitize_input(form.matricule.data).upper()
        clean_nom = sanitize_input(form.nom.data)
        clean_prenom = sanitize_input(form.prenom.data)
        clean_filiere = sanitize_input(form.filiere.data)
        boursier_val = form.est_boursier.data == '1'

        try:
            # Création du profil étudiant
            new_profile = StudentProfile(
                user_id=current_user.id,
                matricule=clean_matricule,
                nom=clean_nom,
                prenom=clean_prenom,
                filiere=clean_filiere,
                est_boursier=boursier_val
            )
            db.session.add(new_profile)
            db.session.commit()
            
            log_security_event(
                user_id=current_user.id,
                action=f"Complétion de profil étudiant réussie (Matricule: {clean_matricule})"
            )
            
            flash("Profile completed successfully! Welcome to your dashboard.", "success")
            return redirect(url_for('main.dashboard'))
        except Exception as e:
            db.session.rollback()
            flash("An error occurred while saving your profile. Please try again.", "danger")

    return render_template('complete_profile.html', form=form)


@main_bp.route('/api/student/<int:student_id>', methods=['GET'])
@login_required
def get_student_api(student_id):
    """
    Endpoint d'API protégé. Renvoie les détails de l'étudiant spécifié.
    - Seuls les administrateurs ou l'étudiant concerné peuvent interroger cet endpoint.
    """
    # Vérifier l'autorisation (admin ou l'étudiant lui-même)
    if not current_user.is_admin and current_user.id != student_id:
        log_security_event(
            user_id=current_user.id,
            action=f"Unauthorized access denied on student API ID: {student_id}"
        )
        return jsonify({"error": "Unauthorized access"}), 403

    user = User.query.get(student_id)
    if not user or user.role == 'admin':
        return jsonify({"error": "Student not found"}), 404

    profile = user.student_profile
    return jsonify({
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "role": user.role,
        "is_active": user.is_active,
        "created_at": user.created_at.strftime('%Y-%m-%d %H:%M:%S') if user.created_at else None,
        "profile": {
            "matricule": profile.matricule if profile else None,
            "nom": profile.nom if profile else None,
            "prenom": profile.prenom if profile else None,
            "filiere": profile.filiere if profile else None,
            "est_boursier": profile.est_boursier if profile else False
        }
    })


# ==================== ROUTE AUTHENTIFICATION (AUTH BLUEPRINT) ====================

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    form = RegistrationForm()
    if form.validate_on_submit():
        clean_email = sanitize_input(form.email.data).lower()
        
        # Générer un nom d'utilisateur à partir du préfixe de l'email
        username_base = clean_email.split('@')[0]
        # S'assurer de l'unicité du username
        username = username_base
        counter = 1
        while User.query.filter_by(username=username).first() is not None:
            username = f"{username_base}{counter}"
            counter += 1

        new_user = User(
            username=username,
            email=clean_email,
            role='student',
            is_active=True
        )
        new_user.set_password(form.password.data)

        try:
            db.session.add(new_user)
            db.session.commit()
            
            # Logger l'inscription comme événement de sécurité
            log_security_event(
                user_id=new_user.id,
                action=f"Nouvel étudiant inscrit : {clean_email}"
            )
            
            flash("Your account has been created! You can now log in.", "success")
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash("An error occurred during registration.", "danger")

    return render_template('register.html', form=form)


@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute", methods=["POST"])
def login():
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('admin.admin_dashboard'))
        return redirect(url_for('main.dashboard'))

    form = LoginForm()
    if form.validate_on_submit():
        clean_email = sanitize_input(form.email.data).lower()
        user = User.query.filter_by(email=clean_email).first()

        if user and user.check_password(form.password.data):
            if not user.is_active:
                log_security_event(
                    user_id=user.id,
                    action=f"Failed login attempt: account blocked ({clean_email})"
                )
                flash("Your account has been blocked by the administrator.", "danger")
                return render_template('login.html', form=form)

            login_user(user)
            user.last_login = datetime.utcnow()
            db.session.commit()

            # Log de connexion réussie
            log_security_event(
                user_id=user.id,
                action="Connexion réussie"
            )

            # Redirection sécurisée vers la page demandée à l'origine
            next_page = request.args.get('next')
            if not next_page or not is_safe_url(next_page):
                if user.is_admin:
                    next_page = url_for('admin.admin_dashboard')
                else:
                    next_page = url_for('main.dashboard')

            return redirect(next_page)
        else:
            # Enregistrement de l'échec de connexion pour audit de sécurité
            user_id = user.id if user else None
            log_security_event(
                user_id=user_id,
                action=f"Failed login attempt: incorrect credentials for {clean_email}"
            )
            flash("Incorrect email address or password.", "danger")

    return render_template('login.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    log_security_event(
        user_id=current_user.id,
        action="User logged out"
    )
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for('main.index'))


# ==================== ROUTE ADMINISTRATIVES (ADMIN BLUEPRINT) ====================

@admin_bp.route('/')
@login_required
@admin_required
def admin_dashboard():
    """Tableau de bord de l'administrateur."""
    # Statistiques
    total_students = User.query.filter_by(role='student').count()
    active_students = User.query.filter_by(role='student', is_active=True).count()
    blocked_students = User.query.filter_by(role='student', is_active=False).count()
    
    # Nombre d'étudiants boursiers
    total_boursiers = StudentProfile.query.filter_by(est_boursier=True).count()
    
    # Taux de complétion des profils
    profiles_completed = StudentProfile.query.count()
    completion_rate = round((profiles_completed / total_students * 100), 1) if total_students > 0 else 0.0

    # Liste de tous les étudiants pour la table d'administration
    students = User.query.filter_by(role='student').order_by(User.created_at.desc()).all()

    # Récupérer les logs de sécurité récents pour affichage de sécurité
    security_logs = SecurityLog.query.order_by(SecurityLog.timestamp.desc()).limit(10).all()

    # Formulaires pré-initialisés pour les modaux dans le template
    form_add = AdminAddStudentForm()
    form_edit = AdminEditStudentForm()

    return render_template(
        'admin.html',
        total_students=total_students,
        active_students=active_students,
        blocked_students=blocked_students,
        total_boursiers=total_boursiers,
        completion_rate=completion_rate,
        students=students,
        security_logs=security_logs,
        form_add=form_add,
        form_edit=form_edit
    )


@admin_bp.route('/student/add', methods=['POST'])
@login_required
@admin_required
def add_student():
    form = AdminAddStudentForm()
    if form.validate_on_submit():
        clean_email = sanitize_input(form.email.data).lower()
        clean_matricule = sanitize_input(form.matricule.data).upper()
        clean_nom = sanitize_input(form.nom.data)
        clean_prenom = sanitize_input(form.prenom.data)
        clean_filiere = sanitize_input(form.filiere.data)
        boursier_val = form.est_boursier.data == '1'

        username_base = clean_email.split('@')[0]
        username = username_base
        counter = 1
        while User.query.filter_by(username=username).first() is not None:
            username = f"{username_base}{counter}"
            counter += 1

        try:
            # Créer l'utilisateur étudiant
            new_student = User(
                username=username,
                email=clean_email,
                role='student',
                is_active=True
            )
            new_student.set_password(form.password.data)
            db.session.add(new_student)
            db.session.flush() # Récupérer l'ID généré

            # Créer directement son profil étudiant
            new_profile = StudentProfile(
                user_id=new_student.id,
                matricule=clean_matricule,
                nom=clean_nom,
                prenom=clean_prenom,
                filiere=clean_filiere,
                est_boursier=boursier_val
            )
            db.session.add(new_profile)
            db.session.commit()

            log_security_event(
                user_id=current_user.id,
                action=f"Student created ID: {new_student.id} (Email: {clean_email}, Matricule: {clean_matricule}) by admin"
            )
            flash(f"Student {clean_email} created successfully!", "success")
        except Exception as e:
            db.session.rollback()
            from flask import current_app
            current_app.logger.error(f"[ADD_STUDENT] Exception: {e}")
            flash(f"Error during creation: {str(e)}", "danger")
    else:
        # Log all server-side validation errors
        from flask import current_app
        current_app.logger.warning(f"[ADD_STUDENT] Validation failed. Errors: {form.errors}")
        # Show all errors in flash messages
        for field_name, error_list in form.errors.items():
            if field_name == 'csrf_token':
                flash("Security error (CSRF). Please reload the page and try again.", "danger")
                continue
            try:
                label = getattr(form, field_name).label.text
            except AttributeError:
                label = field_name
            for error in error_list:
                flash(f"Field '{label}': {error}", "danger")

    return redirect(url_for('admin.admin_dashboard'))



@admin_bp.route('/student/edit/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def edit_student(user_id):
    student = User.query.get_or_404(user_id)
    if student.role == 'admin':
        flash("Unable to edit an administrator.", "danger")
        return redirect(url_for('admin.admin_dashboard'))

    form = AdminEditStudentForm(user_id=user_id)
    if form.validate_on_submit():
        clean_email = sanitize_input(form.email.data).lower()
        clean_matricule = sanitize_input(form.matricule.data).upper()
        clean_nom = sanitize_input(form.nom.data)
        clean_prenom = sanitize_input(form.prenom.data)
        clean_filiere = sanitize_input(form.filiere.data)
        boursier_val = form.est_boursier.data == '1'
        active_val = form.is_active.data == '1'

        try:
            # Mettre à jour l'utilisateur
            student.email = clean_email
            student.is_active = active_val

            # Mettre à jour ou créer le profil étudiant
            profile = student.student_profile
            if profile:
                profile.matricule = clean_matricule
                profile.nom = clean_nom
                profile.prenom = clean_prenom
                profile.filiere = clean_filiere
                profile.est_boursier = boursier_val
            else:
                new_profile = StudentProfile(
                    user_id=student.id,
                    matricule=clean_matricule,
                    nom=clean_nom,
                    prenom=clean_prenom,
                    filiere=clean_filiere,
                    est_boursier=boursier_val
                )
                db.session.add(new_profile)

            db.session.commit()

            log_security_event(
                user_id=current_user.id,
                action=f"Student updated ID: {student.id} (Email: {clean_email}) by administrator"
            )
            flash(f"Student information for {clean_email} has been updated.", "success")
        except Exception as e:
            db.session.rollback()
            flash("Error updating the student.", "danger")
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Field error '{getattr(form, field).label.text}': {error}", "danger")
                break
            break

    return redirect(url_for('admin.admin_dashboard'))


@admin_bp.route('/student/delete/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def delete_student(user_id):
    student = User.query.get_or_404(user_id)
    if student.role == 'admin':
        flash("Unable to delete an administrator account.", "danger")
        return redirect(url_for('admin.admin_dashboard'))

    email_deleted = student.email
    try:
        db.session.delete(student)
        db.session.commit()

        log_security_event(
            user_id=current_user.id,
            action=f"Student deleted {email_deleted} (ID: {user_id})"
        )
        flash(f"Student {email_deleted} has been permanently deleted.", "success")
    except Exception as e:
        db.session.rollback()
        flash("An error occurred while deleting the student.", "danger")

    return redirect(url_for('admin.admin_dashboard'))


@admin_bp.route('/student/reset-password/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def reset_password(user_id):
    student = User.query.get_or_404(user_id)
    if student.role == 'admin':
        flash("Unable to reset the password of an administrator account.", "danger")
        return redirect(url_for('admin.admin_dashboard'))

    new_password = request.form.get('new_password')
    if not new_password or len(new_password) < 8:
        flash("The password must be at least 8 characters long.", "danger")
        return redirect(url_for('admin.admin_dashboard'))

    # Optionnel: on peut valider la force du mot de passe ici
    from app.forms import check_password_strength
    if not check_password_strength(new_password):
        flash("The password is not strong enough (uppercase, lowercase, number, special character required).", "danger")
        return redirect(url_for('admin.admin_dashboard'))

    try:
        student.set_password(new_password)
        db.session.commit()

        log_security_event(
            user_id=current_user.id,
            action=f"Password reset for student {student.email} (ID: {user_id})"
        )
        flash(f"The password for {student.email} has been reset.", "success")
    except Exception as e:
        db.session.rollback()
        flash("Error resetting the password.", "danger")

    return redirect(url_for('admin.admin_dashboard'))
