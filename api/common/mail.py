import typing as t

import email_validator
from flask import current_app
from flask_security.utils import config_value
from flask_security.proxies import _security

if t.TYPE_CHECKING:  # pragma: no cover
    import flask
    from .datastore import User

from werkzeug.local import LocalProxy
localize_callback = LocalProxy(lambda: _security.i18n_domain.gettext)

class MailUtil:
    """
    Utility class providing methods for validating, normalizing and sending emails.
    This default class uses the email_validator package to handle validation and
    normalization, and the flask_mail package to send emails.
    To provide your own implementation, pass in the class as ``mail_util_cls``
    at init time.  Your class will be instantiated once as part of app initialization.
    .. versionadded:: 4.0.0
    """

    def __init__(self, app: "flask.Flask"):
        """Instantiate class.
        :param app: The Flask application being initialized.
        """
        pass

    def send_mail(
        self,
        template: str,
        subject: str,
        recipient: str,
        sender: t.Union[str, tuple],
        body: str,
        html: str,
        user: "User",
        qrcode,
        **kwargs: t.Any
    ) -> None:
        """Send an email via the Flask-Mail extension.
        :param template: the Template name. The message has already been rendered
            however this might be useful to differentiate why the email is being sent.
        :param subject: Email subject
        :param recipient: Email recipient
        :param sender: who to send email as (see :py:data:`SECURITY_EMAIL_SENDER`)
        :param body: the rendered body (text)
        :param html: the rendered body (html)
        :param user: the user model
        """

        from flask_mail import Message

        msg = Message(subject, sender=sender, recipients=[recipient])
        msg.body = body
        msg.html = html

        try:
            # if attachment passed
            msg.attach('qr.png','image/png', qrcode.read(), 'inline', headers=[['Content-ID','<QRCode>'],])
        except Exception as E:
            pass

        mail = current_app.extensions.get("mail")
        mail.send(msg)  # type: ignore

    def normalize(self, email: str) -> str:
        """
        Given an input email - return a normalized version.
        Must be called in app context and uses :py:data:`SECURITY_EMAIL_VALIDATOR_ARGS`
        config variable to pass any relevant arguments to
        email_validator.validate_email() method.
        Will throw email_validator.EmailNotValidError if email isn't even valid.
        """
        validator_args = config_value("EMAIL_VALIDATOR_ARGS") or {}
        valid = email_validator.validate_email(email, **validator_args)
        return valid.email

    def validate(self, email: str) -> str:
        """
        Validate the given email.
        If valid, the normalized version is returned.
        ValueError is thrown if not valid.
        """

        validator_args = config_value("EMAIL_VALIDATOR_ARGS") or {}
        valid = email_validator.validate_email(email, **validator_args)
        return valid.email

def send_mail(subject, recipient, template, **context):
    """Send an email.
    :param subject: Email subject
    :param recipient: Email recipient
    :param template: The name of the email template
    :param context: The context to render the template with
    This formats the email and passes it off to :class:`.MailUtil` to actually send the
    message.
    """

    context.setdefault("security", _security)
    context.update(_security._run_ctx_processor("mail"))

    body = None
    html = None
    ctx = ("security/email", template)
    if config_value("EMAIL_PLAINTEXT"):
        body = _security.render_template("%s/%s.txt" % ctx, **context)
    if config_value("EMAIL_HTML"):
        html = _security.render_template("%s/%s.html" % ctx, **context)

    subject = localize_callback(subject)

    sender = _security.email_sender
    if isinstance(sender, LocalProxy):
        sender = sender._get_current_object()

    # In Flask-Mail, sender can be a two element tuple -- (name, address)
    if isinstance(sender, tuple) and len(sender) == 2:
        sender = (str(sender[0]), str(sender[1]))
    elif type(sender)==str:
        sender = ('DigiVax Enterprise', sender)
    else:
        sender = str(sender)

    _security._mail_util.send_mail(
        template, subject, recipient, sender, body, html, context.get("user", None), context.get("qrcode", None), 
    )
