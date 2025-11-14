"""Admin interface for download audit logs and reporting."""
import os
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash
import requests
from urllib.parse import urlencode

bp = Blueprint('downloads', __name__)


def get_api_base_url():
    """Get the base URL for API calls from environment variable or use default."""
    return os.getenv('ODP_API_URL', 'http://localhost:2020')


@bp.route('/')
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
        # Call the backend API
        api_url = f"{get_api_base_url()}/download/logs"
        response = requests.get(api_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        return render_template(
            'download_index.html',
            downloads=data.get('items', []),
            total=data.get('total', 0),
            page=page,
            total_pages=data.get('total_pages', 0),
            size=data.get('size', 50),
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
        api_url = f"{get_api_base_url()}/download/stats"
        response = requests.get(api_url, params=params, timeout=10)
        response.raise_for_status()
        stats = response.json()

        return render_template(
            'download_analytics.html',
            stats=stats,
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
        # Call the backend API
        api_url = f"{get_api_base_url()}/download/export/csv"
        response = requests.get(api_url, params=params, timeout=30)
        response.raise_for_status()

        # The response should already be a CSV with proper headers
        return response.content, 200, {
            'Content-Disposition': f'attachment; filename="download_logs.csv"',
            'Content-Type': 'text/csv',
        }

    except requests.RequestException as e:
        flash(f'Error exporting download logs: {str(e)}', category='error')
        return redirect(request.referrer or url_for('.index'))
