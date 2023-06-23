from typing import Type

from flask import Response, flash, g, redirect, render_template, request, url_for
from flask_login import current_user
from markupsafe import Markup

from odp.const import ODPScope
from odp.lib.client import ODPAPIError
from odp.ui.base import api
from odp.ui.base.forms import BaseForm


def get_tag_instance(obj: dict, tag_id: str, user: bool = False) -> dict | None:
    """Get a single tag instance for a record or collection.

    The tag should have cardinality 'one' or 'user'; if 'user',
    set `user=True` to get the tag instance for the current user.
    """
    return next(
        (tag for tag in obj['tags'] if tag['tag_id'] == tag_id and (
                not user or tag['user_id'] == current_user.id
        )), None
    )


def get_tag_instances(obj: dict, tag_id: str) -> dict:
    """Get a page result of tag instances (with cardinality
    'user' or 'multi') for a record or collection."""
    return pagify(
        [tag for tag in obj['tags'] if tag['tag_id'] == tag_id]
    )


def tag_singleton(obj_type: str, obj_id: str, tag_id: str) -> None:
    """Set a singleton tag (cardinality 'one') on a record or collection."""
    api.post(f'/{obj_type}/{obj_id}/tag', dict(
        tag_id=tag_id,
        data={},
    ))
    flash(f'{tag_id} tag has been set.', category='success')


def untag_singleton(obj_type: str, obj_id: str, tag_id: str) -> None:
    """Remove a singleton tag (cardinality 'one') from a record or collection."""
    api_route = f'/{obj_type}/'
    if obj_type == 'collection':
        admin_scope = ODPScope.COLLECTION_ADMIN
    elif obj_type == 'record':
        admin_scope = ODPScope.RECORD_ADMIN

    if admin_scope in g.user_permissions:
        api_route += 'admin/'

    obj = api.get(f'/{obj_type}/{obj_id}')
    if tag_instance := get_tag_instance(obj, tag_id):
        api.delete(f'{api_route}{obj_id}/tag/{tag_instance["id"]}')
        flash(f'{tag_id} tag has been removed.', category='success')


def tag_vocabulary_term(
        obj_type: str,
        obj_id: str,
        tag_id: str,
        vocab_id: str,
        form_cls: Type[BaseForm],
) -> Response | str:
    """Set a vocabulary keyword tag on a record or collection.

    This is a view function and returns either a redirect or a rendered template;
    a template named {collection|record}_tag_{vocab}.html must exist.
    """
    obj = api.get(f'/{obj_type}/{obj_id}')
    vocab_field = vocab_id.lower()

    if request.method == 'POST':
        form = form_cls(request.form)
    else:
        # vocabulary tags have cardinality 'multi', so this will
        # always be an insert - i.e. don't populate form for update
        form = form_cls()

    populate_vocabulary_term_choices(form[vocab_field], vocab_id, include_none=True)

    if request.method == 'POST' and form.validate():
        try:
            api.post(f'/{obj_type}/{obj_id}/tag', dict(
                tag_id=tag_id,
                data={
                    vocab_field: form[vocab_field].data,
                    'comment': form.comment.data,
                },
            ))
            flash(f'{tag_id} tag has been set.', category='success')
            return redirect(url_for('.view', id=obj_id))

        except ODPAPIError as e:
            if response := api.handle_error(e):
                return response

    return render_template(f'{obj_type}_tag_{vocab_field}.html', **{f'{obj_type}': obj}, form=form)


def untag_vocabulary_term(
        obj_type: str,
        obj_id: str,
        tag_id: str,
        tag_instance_id: str,
) -> Response:
    """Remove a vocabulary keyword tag from a record or collection.

    This is a view function and returns a redirect to the record or
    collection view page.
    """
    api_route = f'/{obj_type}/'
    if obj_type == 'collection':
        admin_scope = ODPScope.COLLECTION_ADMIN
    elif obj_type == 'record':
        admin_scope = ODPScope.RECORD_ADMIN

    if admin_scope in g.user_permissions:
        api_route += 'admin/'

    api.delete(f'{api_route}{obj_id}/tag/{tag_instance_id}')
    flash(f'{tag_id} tag has been removed.', category='success')

    return redirect(url_for('.view', id=obj_id))


def pagify(item_list: list) -> dict:
    """Convert a flat object list to a page result."""
    return {
        'items': item_list,
        'total': len(item_list),
        'page': 1,
        'pages': 1,
    }


def populate_collection_choices(field, include_none=False):
    collections = api.get('/collection/', sort='key')['items']
    field.choices = [('', '(None)')] if include_none else []
    field.choices += [
        (collection['id'], Markup(f"{collection['key']} &mdash; {collection['name']}"))
        for collection in collections
    ]


def populate_provider_choices(field, include_none=False):
    providers = api.get('/provider/', sort='key')['items']
    field.choices = [('', '(None)')] if include_none else []
    field.choices += [
        (provider['id'], Markup(f"{provider['key']} &mdash; {provider['name']}"))
        for provider in providers
    ]


def populate_metadata_schema_choices(field):
    schemas = api.get('/schema/', schema_type='metadata')['items']
    field.choices = [
        (schema['id'], schema['id'])
        for schema in schemas
        if schema['id'].startswith('SAEON')
    ]


def populate_scope_choices(field, scope_types=None):
    scopes = api.get('/scope/')['items']
    field.choices = [
        (scope['id'], scope['id'])
        for scope in scopes
        if scope_types is None or scope['type'] in scope_types
    ]


def populate_role_choices(field):
    roles = api.get('/role/')['items']
    field.choices = [
        (role['id'], role['id'])
        for role in roles
    ]


def populate_vocabulary_term_choices(field, vocabulary_id, include_none=False):
    vocabulary = api.get(f'/vocabulary/{vocabulary_id}')
    field.choices = [('', '(None)')] if include_none else []
    field.choices += [
        (term['id'], term['id'])
        for term in vocabulary['terms']
    ]
