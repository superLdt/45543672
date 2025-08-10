from flask import Blueprint, render_template
from flask_login import login_required, current_user

scheduling_bp = Blueprint('scheduling_bp', __name__, template_folder='templates')

@scheduling_bp.route('/')
@login_required
def index():
    return render_template('scheduling/index.html', user=current_user)

@scheduling_bp.route('/vehicles')
def vehicle_management():
    return render_template('scheduling/vehicles.html', title='车辆管理')

@scheduling_bp.route('/tasks')
def task_assignment():
    return render_template('scheduling/tasks.html', title='任务分配')

@scheduling_bp.route('/monitoring')
def realtime_monitoring():
    return render_template('scheduling/monitoring.html', title='实时监控')
