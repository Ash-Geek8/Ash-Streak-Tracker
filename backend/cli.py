import click
from flask.cli import with_appcontext
from .models import User,Note
from .notes_rag import rebuild_notes_index
def register_commands(app):
    @app.cli.command("rebuild-notes-index")
    @with_appcontext
    def rebuild_all():
        for u in User.query.all():
            result=rebuild_notes_index(u.id,Note.query.filter_by(user_id=u.id).all())
            click.echo(f"user={u.id}: indexed={result['indexed']} available={result['available']}")
