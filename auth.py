from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from extensions import db, bcrypt
from models import User
from email_utils import send_email, mail_configured

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        remember = request.form.get("remember") == "on"

        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password_hash, password):
            login_user(user, remember=remember)
            next_page = request.args.get("next")
            flash(f"Bem-vindo de volta, {user.name}! 👋", "success")
            return redirect(next_page or url_for("main.dashboard"))
        else:
            flash("E-mail ou senha incorretos.", "danger")

    return render_template("login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        if not name or not email or not password:
            flash("Preencha todos os campos.", "danger")
            return render_template("register.html")

        if password != confirm:
            flash("As senhas não coincidem.", "danger")
            return render_template("register.html")

        if len(password) < 6:
            flash("A senha deve ter pelo menos 6 caracteres.", "danger")
            return render_template("register.html")

        if User.query.filter_by(email=email).first():
            flash("Este e-mail já está cadastrado.", "danger")
            return render_template("register.html")

        pw_hash = bcrypt.generate_password_hash(password).decode("utf-8")
        user = User(name=name, email=email, password_hash=pw_hash)
        db.session.add(user)
        db.session.commit()

        login_user(user)
        flash(f"Conta criada com sucesso! Bem-vindo, {name}! 🎉", "success")
        return redirect(url_for("main.bmr"))

    return render_template("register.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Você saiu da sua conta.", "info")
    return redirect(url_for("auth.login"))


def _get_serializer():
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"])


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        user = User.query.filter_by(email=email).first()

        if user:
            s = _get_serializer()
            token = s.dumps(user.email, salt="password-reset")
            reset_url = url_for("auth.reset_password", token=token, _external=True)
            sent = False
            if mail_configured():
                sent = send_email(
                    user.email,
                    "Redefinir senha — NutriTrack",
                    _reset_email_html(user.name, reset_url),
                    f"Olá {user.name},\n\nPara redefinir sua senha, abra este link (vale 30 minutos):\n{reset_url}\n\nSe você não pediu isso, ignore este e-mail.",
                )
            else:
                current_app.logger.error("MAIL_SERVER não configurado — reset de senha não enviado.")

            if user and not sent:
                current_app.logger.error("Falha ao enviar e-mail de reset para usuário id=%s", user.id)

        # Sempre a mesma mensagem: não revela se o e-mail existe e nunca mostra o link.
        flash(
            "Se este e-mail estiver cadastrado, enviamos um link para redefinir a senha. "
            "Confira a caixa de entrada e o spam.",
            "info",
        )
        return render_template("forgot_password.html")

    return render_template("forgot_password.html")


@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    s = _get_serializer()
    try:
        email = s.loads(token, salt="password-reset", max_age=1800)  # 30 min
    except SignatureExpired:
        flash("Este link expirou. Solicite um novo.", "danger")
        return redirect(url_for("auth.forgot_password"))
    except BadSignature:
        flash("Link inválido.", "danger")
        return redirect(url_for("auth.forgot_password"))

    user = User.query.filter_by(email=email).first()
    if not user:
        flash("Usuário não encontrado.", "danger")
        return redirect(url_for("auth.forgot_password"))

    if request.method == "POST":
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        if not password or len(password) < 6:
            flash("A senha deve ter pelo menos 6 caracteres.", "danger")
            return render_template("reset_password.html", token=token)

        if password != confirm:
            flash("As senhas não coincidem.", "danger")
            return render_template("reset_password.html", token=token)

        user.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")
        db.session.commit()

        flash("Senha redefinida com sucesso! Faça login com a nova senha. 🎉", "success")
        return redirect(url_for("auth.login"))

    return render_template("reset_password.html", token=token)


def _reset_email_html(name, reset_url):
        from html import escape

        safe_name = escape(name)
        safe_url = escape(reset_url, quote=True)
        return f"""
        <div style="font-family:Arial,sans-serif;max-width:520px;margin:0 auto;padding:24px;background:#F8FAFC;color:#0F172A;border:1px solid #E2E8F0;border-radius:12px;">
            <h2 style="margin:0 0 12px;">🥗 NutriTrack</h2>
            <p>Olá, {safe_name}.</p>
            <p>Recebemos um pedido para redefinir a senha da sua conta. O link vale por <strong>30 minutos</strong>.</p>
            <p style="margin:24px 0;">
                <a href="{safe_url}" style="background:#2563EB;color:#fff;padding:12px 18px;border-radius:8px;text-decoration:none;font-weight:700;">
                    Redefinir senha
                </a>
            </p>
            <p style="font-size:13px;color:#64748B;word-break:break-all;">Se o botão não funcionar, copie o link de redefinição.</p>
            <p style="font-size:13px;color:#64748B;">Se você não pediu isso, ignore este e-mail.</p>
        </div>
        """
