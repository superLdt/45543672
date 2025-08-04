from flask import Blueprint, render_template

planning_bp = Blueprint('planning_bp', __name__, template_folder='templates')

@planning_bp.route('/')
def index():
    return render_template('planning/index.html')

@planning_bp.route('/routes')
def route_planning():
    return render_template('planning/routes.html', title='路线规划')

@planning_bp.route('/optimization')
def path_optimization():
    return render_template('planning/optimization.html', title='路径优化')

@planning_bp.route('/forecast')
def capacity_forecast():
    return render_template('planning/forecast.html', title='运力预测')