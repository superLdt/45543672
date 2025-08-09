from flask import Blueprint, render_template

scheduling_bp = Blueprint('scheduling_bp', __name__, template_folder='templates')

@scheduling_bp.route('/')
def index():
    return render_template('scheduling/index.html')

@scheduling_bp.route('/vehicles')
def vehicle_management():
    return render_template('scheduling/vehicles.html', title='车辆管理')

@scheduling_bp.route('/tasks')
def task_assignment():
    return render_template('scheduling/tasks.html', title='任务分配')

@scheduling_bp.route('/monitoring')
def realtime_monitoring():
    return render_template('scheduling/monitoring.html', title='实时监控')
