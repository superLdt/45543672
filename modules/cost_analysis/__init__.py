from flask import Blueprint, render_template
from flask_login import login_required, current_user

cost_analysis_bp = Blueprint('cost_analysis_bp', __name__, template_folder='templates')

@cost_analysis_bp.route('/')
@login_required
def index():
    return render_template('cost_analysis/index.html', user=current_user)

@cost_analysis_bp.route('/mail_route')
def mail_route_cost():
    return render_template('cost_analysis/mail_route.html', title='邮路成本分析')

@cost_analysis_bp.route('/reports')
def cost_reports():
    return render_template('cost_analysis/reports.html', title='成本报表')

@cost_analysis_bp.route('/optimization')
def cost_optimization():
    return render_template('cost_analysis/optimization.html', title='成本优化建议')
