from flask import Flask, render_template, jsonify, request, send_from_directory
from datetime import datetime, date
import threading
import os
import sys

# Import utility modules
from utility import DBQueryExecutor, JiraAuth, utils, AutoTriageUtility
from utility import CompareSimilarity, LocalDBQueries, UpdateMetesRun
import wats_feature_triage as wft
import AddComment
import WebTriageSkipped

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = 'your-secret-key-here-change-in-production'
app.config['DEBUG'] = True

# Global variables to track task status
task_status = {}


@app.route('/')
def home():
    """Home page route"""
    return render_template('index.html')


@app.route('/api/hello')
def hello_api():
    """Sample API endpoint"""
    return jsonify({
        'message': 'Hello from WATS Auto-Triage Flask API!',
        'timestamp': datetime.now().isoformat(),
        'status': 'success'
    })


@app.route('/api/features', methods=['GET'])
def get_features():
    """Get list of available features for triage"""
    features = ['customerobsession', 'u4b', 'londongrat', 'rider', 'freight', 'driver', 'tooling']
    return jsonify({
        'status': 'success',
        'features': features
    })


@app.route('/api/triage/run', methods=['POST'])
def run_triage():
    """
    Run the auto-triage process for a specific feature
    
    Request Body:
        {
            "feature_name": "driver"  // Required: feature name to triage
        }
    """
    try:
        data = request.get_json()
        
        if not data or 'feature_name' not in data:
            return jsonify({
                'status': 'error',
                'message': 'feature_name is required'
            }), 400
        
        feature_name = data['feature_name']
        
        # Validate feature name
        valid_features = ['customerobsession', 'u4b', 'londongrat', 'rider', 'freight', 'driver', 'tooling']
        if feature_name not in valid_features:
            return jsonify({
                'status': 'error',
                'message': f'Invalid feature_name. Must be one of: {", ".join(valid_features)}'
            }), 400
        
        # Run triage in background thread
        task_id = f"{feature_name}_{datetime.now().timestamp()}"
        task_status[task_id] = {
            'status': 'running',
            'feature': feature_name,
            'started_at': datetime.now().isoformat()
        }
        
        def run_triage_task():
            try:
                triaged_data = wft.get_triaged_data_from_wats()
                if len(triaged_data) < 2:
                    triaged_data = wft.get_triaged_data_from_wats()
                
                untriaged_data = wft.get_untriaged_data_from_wats(feature_name)
                
                task_status[task_id]['untriaged_count'] = len(untriaged_data)
                task_status[task_id]['triaged_count'] = len(triaged_data)
                
                wft.iterate_matching_failure_for_wats(untriaged_data, triaged_data, feature_name)
                
                task_status[task_id]['status'] = 'completed'
                task_status[task_id]['completed_at'] = datetime.now().isoformat()
            except Exception as e:
                task_status[task_id]['status'] = 'failed'
                task_status[task_id]['error'] = str(e)
                task_status[task_id]['completed_at'] = datetime.now().isoformat()
        
        thread = threading.Thread(target=run_triage_task)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'status': 'success',
            'message': f'Triage process started for {feature_name}',
            'task_id': task_id
        }), 202
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/triage/status/<task_id>', methods=['GET'])
def get_triage_status(task_id):
    """Get the status of a triage task"""
    if task_id not in task_status:
        return jsonify({
            'status': 'error',
            'message': 'Task not found'
        }), 404
    
    return jsonify({
        'status': 'success',
        'task': task_status[task_id]
    })


@app.route('/api/triage/triaged-data', methods=['GET'])
def get_triaged_data():
    """Get triaged data from WATS"""
    try:
        triaged_data = wft.get_triaged_data_from_wats()
        
        return jsonify({
            'status': 'success',
            'count': len(triaged_data),
            'data': triaged_data.to_dict(orient='records')
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/triage/untriaged-data', methods=['GET'])
def get_untriaged_data():
    """
    Get untriaged data from WATS for a specific feature
    Query Parameters:
        feature_name: Required feature name
    """
    feature_name = request.args.get('feature_name')
    
    if not feature_name:
        return jsonify({
            'status': 'error',
            'message': 'feature_name query parameter is required'
        }), 400
    
    try:
        untriaged_data = wft.get_untriaged_data_from_wats(feature_name)
        
        return jsonify({
            'status': 'success',
            'feature': feature_name,
            'count': len(untriaged_data),
            'data': untriaged_data.to_dict(orient='records')
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/comments/add', methods=['POST'])
def add_comments():
    """
    Add comments to JIRA tickets for a specific date
    
    Request Body:
        {
            "exe_date": "2025-11-17",  // Optional: defaults to today
            "triage_by": "auto-triage"  // Optional: defaults to "auto-triage"
        }
    """
    try:
        data = request.get_json() or {}
        
        exe_date = data.get('exe_date', date.today().strftime("%Y-%m-%d"))
        triage_by = data.get('triage_by', 'auto-triage')
        
        # Run in background thread
        task_id = f"comment_{datetime.now().timestamp()}"
        task_status[task_id] = {
            'status': 'running',
            'exe_date': exe_date,
            'triage_by': triage_by,
            'started_at': datetime.now().isoformat()
        }
        
        def add_comments_task():
            try:
                AddComment.add_comment_for(exe_date, triage_by)
                task_status[task_id]['status'] = 'completed'
                task_status[task_id]['completed_at'] = datetime.now().isoformat()
            except Exception as e:
                task_status[task_id]['status'] = 'failed'
                task_status[task_id]['error'] = str(e)
                task_status[task_id]['completed_at'] = datetime.now().isoformat()
        
        thread = threading.Thread(target=add_comments_task)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'status': 'success',
            'message': f'Comment addition started for {exe_date}',
            'task_id': task_id
        }), 202
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/triage/skipped', methods=['POST'])
def process_skipped():
    """Process skipped triage items"""
    try:
        task_id = f"skipped_{datetime.now().timestamp()}"
        task_status[task_id] = {
            'status': 'running',
            'started_at': datetime.now().isoformat()
        }
        
        def process_skipped_task():
            try:
                today_triaged_data = DBQueryExecutor.get_today_triaged_data_from_wats()
                today_skipped_data = DBQueryExecutor.get_untriaged_skipped_data_from_wats()
                
                task_status[task_id]['triaged_count'] = len(today_triaged_data)
                task_status[task_id]['skipped_count'] = len(today_skipped_data)
                
                processed = 0
                for _idx, data in today_skipped_data.iterrows():
                    filter_triaged_data = today_triaged_data.loc[
                        today_triaged_data['execution_uuid'] == data['execution_uuid']
                    ]
                    if len(filter_triaged_data) != 0:
                        UpdateMetesRun.triage_wats_run(
                            run_uuid=data['run_uuid'],
                            triage_category_l1=filter_triaged_data.iloc[0]['triage_category_l1'],
                            triage_category_l2=filter_triaged_data.iloc[0]['triage_category_l2'],
                            jira_ticket=filter_triaged_data.iloc[0]['jira_ticket'],
                            triaged_by=filter_triaged_data.iloc[0]['triaged_by']
                        )
                        processed += 1
                
                task_status[task_id]['status'] = 'completed'
                task_status[task_id]['processed'] = processed
                task_status[task_id]['completed_at'] = datetime.now().isoformat()
            except Exception as e:
                task_status[task_id]['status'] = 'failed'
                task_status[task_id]['error'] = str(e)
                task_status[task_id]['completed_at'] = datetime.now().isoformat()
        
        thread = threading.Thread(target=process_skipped_task)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'status': 'success',
            'message': 'Skipped triage processing started',
            'task_id': task_id
        }), 202
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/clean', methods=['POST'])
def clean_files():
    """Clean up temporary files and databases"""
    try:
        utils.remove_path("new_ticket")
        utils.remove_path("testImg")
        LocalDBQueries.delete_all_execution_status_dbs()
        
        return jsonify({
            'status': 'success',
            'message': 'Cleanup completed successfully'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/tasks', methods=['GET'])
def get_all_tasks():
    """Get status of all tasks"""
    return jsonify({
        'status': 'success',
        'tasks': task_status
    })


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({'error': 'Internal server error', 'message': str(error)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

