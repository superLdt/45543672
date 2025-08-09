import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from flask import Blueprint, render_template
from flask_login import current_user
from modules.user_management import permission_required

reconciliation_bp = Blueprint('reconciliation_bp', __name__, template_folder='templates')

@reconciliation_bp.route('/')
@permission_required('reconciliation_view')
def index():
    return render_template('reconciliation/index.html', user=current_user)

@reconciliation_bp.route('/transactions')
@permission_required('reconciliation_view')
def transaction_records():
    return render_template('reconciliation/transactions.html', title='交易记录', user=current_user)

@reconciliation_bp.route('/financial')
@permission_required('reconciliation_view')
def financial_reconciliation():
    return render_template('reconciliation/financial.html', title='财务对账', user=current_user)

@reconciliation_bp.route('/reports')
@permission_required('reconciliation_view')
def generate_reports():
    return render_template('reconciliation/reports.html', title='报表生成', user=current_user)

@reconciliation_bp.route('/data_import')
@permission_required('reconciliation_view')
def data_import():
    return render_template('reconciliation/data_import.html', user=current_user)

@reconciliation_bp.route('/approval_process')
@permission_required('reconciliation_view')
def approval_process():
    return render_template('reconciliation/approval_process.html', user=current_user)

@reconciliation_bp.route('/exception_handling')
@permission_required('reconciliation_view')
def exception_handling():
    return render_template('reconciliation/exception_handling.html', user=current_user)

@reconciliation_bp.route('/feishu_collaboration')
@permission_required('reconciliation_view')
def feishu_collaboration():
    return render_template('reconciliation/feishu_collaboration.html', user=current_user)

@reconciliation_bp.route('/settlement_documents')
@permission_required('reconciliation_view')
def settlement_documents():
    return render_template('reconciliation/settlement_documents.html', user=current_user)

@reconciliation_bp.route('/data_query')
@permission_required('reconciliation_view')
def data_query():
    return render_template('reconciliation/data_query.html', user=current_user)
