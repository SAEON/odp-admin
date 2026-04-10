"""Admin interface for download audit logs and reporting."""
from datetime import datetime, timedelta

import requests
from flask import Blueprint, Response, render_template, request, redirect, url_for, flash

from odp.const import ODPScope
from odp.ui.base import api

bp = Blueprint('downloads', __name__)


@bp.route('/')
@api.view(ODPScope.CATALOG_READ)
def index():
    """Display paginated download logs with filtering options."""
    page = request.args.get('page', 1, type=int)
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    email = request.args.get('email', '')
    organisation = request.args.get('organisation', '')
    download_type = request.args.get('download_type', '')

    # Build query parameters
    params = {
        'page': page,
        'size': 50,
    }

    if start_date:
        params['start_date'] = start_date
    if end_date:
        params['end_date'] = end_date
    if email:
        params['email'] = email
    if organisation:
        params['organisation'] = organisation
    if download_type:
        params['download_type'] = download_type

    try:

        download_logs = api.get('/download/logs', params=params)

        return render_template(
            'download_index.html',
            downloads=download_logs.get('items', []),
            total=download_logs.get('total', 0),
            page=page,
            total_pages=download_logs.get('total_pages', 0),
            size=download_logs.get('size', 50),
            start_date=start_date,
            end_date=end_date,
            email=email,
            organisation=organisation,
            download_type=download_type,
        )

    except requests.RequestException as e:
        flash(f'Error retrieving download logs: {str(e)}', category='error')
        return render_template(
            'download_index.html',
            downloads=[],
            total=0,
            page=1,
            total_pages=0,
            size=50,
            error=str(e),
        )


@bp.route('/analytics')
@api.view(ODPScope.CATALOG_READ)
def analytics():
    """Display download analytics and statistics dashboard."""
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')

    # Default to last 30 days if not specified
    if not end_date:
        end_date = datetime.now().strftime('%Y-%m-%d')
    if not start_date:
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

    params = {}
    if start_date:
        params['start_date'] = start_date
    if end_date:
        params['end_date'] = end_date

    try:
        # Call the backend API for statistics
        download_stats = api.get('/download/stats', params=params)


        return render_template(
            'download_analytics.html',
            stats=download_stats,
            start_date=start_date,
            end_date=end_date,
        )


    except requests.RequestException as e:
        flash(f'Error retrieving download statistics: {str(e)}', category='error')
        return render_template(
            'download_analytics.html',
            stats={},
            error=str(e),
        )


@bp.route('/export')
@api.view(ODPScope.CATALOG_READ)
def export_csv():
    """Export download logs as CSV."""
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    email = request.args.get('email', '')
    organisation = request.args.get('organisation', '')
    download_type = request.args.get('download_type', '')

    # Build query parameters
    params = {}
    if start_date:
        params['start_date'] = start_date
    if end_date:
        params['end_date'] = end_date
    if email:
        params['email'] = email
    if organisation:
        params['organisation'] = organisation
    if download_type:
        params['download_type'] = download_type

    try:

        api_url = f"{api.api_url}/download/export/csv"
        response = api._send_request('GET', api_url, data=None, files=None, params=params, headers={}, stream=True)

        # Check for errors (this will raise ODPAPIError if the backend fails)
        response.raise_for_status()

        # Stream the CSV content directly to the browser
        return Response(
            response.iter_content(chunk_size=1024),
            content_type=response.headers.get('Content-Type', 'text/csv'),
            headers={
                'Content-Disposition': response.headers.get(
                    'Content-Disposition',
                    'attachment; filename="download_logs.csv"'
                )
            }
        )

    except Exception as e:
        flash(f'Error exporting download logs: {str(e)}', category='error')
        return redirect(request.referrer or url_for('.index'))
