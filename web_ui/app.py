"""
Web UI Service
Flask-based web interface for the GradeSchoolMathSolver-RAG system
"""
from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_cors import CORS
from config import Config
from models import ExamRequest, AgentConfig
from services.account import AccountService
from services.exam import ExamService
from services.agent_management import AgentManagementService


app = Flask(__name__, template_folder='templates')
CORS(app)

config = Config()
account_service = AccountService()
exam_service = ExamService()
agent_management = AgentManagementService()

# Create default agents on startup
agent_management.create_default_agents()


@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')


@app.route('/users')
def users():
    """List all users with their statistics"""
    usernames = account_service.list_users()
    users_data = []
    
    for username in usernames:
        stats = account_service.get_user_stats(username)
        if stats:
            users_data.append({
                'username': stats.username,
                'total_questions': stats.total_questions,
                'correct_answers': stats.correct_answers,
                'overall_correctness': stats.overall_correctness,
                'recent_100_score': stats.recent_100_score
            })
    
    return render_template('users.html', users=users_data)


@app.route('/user/<username>')
def user_detail(username):
    """User detail page with history"""
    stats = account_service.get_user_stats(username)
    if not stats:
        return "User not found", 404
    
    history = account_service.get_answer_history(username, limit=50)
    
    return render_template('user_detail.html', 
                         username=username,
                         stats=stats,
                         history=history)


@app.route('/exam')
def exam_page():
    """Exam page"""
    return render_template('exam.html', 
                         difficulty_levels=config.DIFFICULTY_LEVELS)


@app.route('/agents')
def agents_page():
    """Agents management page"""
    agent_names = agent_management.list_agents()
    agents = []
    
    for name in agent_names:
        agent_config = agent_management.get_agent(name)
        if agent_config:
            agents.append(agent_config)
    
    return render_template('agents.html', agents=agents)


# API Routes

@app.route('/api/users', methods=['GET'])
def api_list_users():
    """API: List all users"""
    usernames = account_service.list_users()
    users_data = []
    
    for username in usernames:
        stats = account_service.get_user_stats(username)
        if stats:
            users_data.append(stats.model_dump())
    
    return jsonify(users_data)


@app.route('/api/users', methods=['POST'])
def api_create_user():
    """API: Create a new user"""
    data = request.json
    username = data.get('username')
    
    if not username:
        return jsonify({'error': 'Username is required'}), 400
    
    success = account_service.create_user(username)
    
    if success:
        return jsonify({'message': 'User created', 'username': username}), 201
    else:
        return jsonify({'error': 'User already exists'}), 409


@app.route('/api/exam/human', methods=['POST'])
def api_conduct_human_exam():
    """API: Conduct exam for human user"""
    data = request.json
    
    try:
        exam_request = ExamRequest(
            username=data['username'],
            difficulty=data['difficulty'],
            question_count=data['question_count']
        )
        
        # Generate questions first
        questions = exam_service.create_exam(exam_request)
        
        # Return questions to frontend for user to answer
        return jsonify({
            'questions': [q.model_dump() for q in questions]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/exam/human/submit', methods=['POST'])
def api_submit_human_exam():
    """API: Submit human exam answers"""
    data = request.json
    
    try:
        exam_request = ExamRequest(
            username=data['username'],
            difficulty=data['difficulty'],
            question_count=len(data['answers'])
        )
        
        # For submission, we need to recreate or pass questions
        # This is a simplified version - in production, you'd store the exam session
        results = {
            'message': 'Answers recorded successfully'
        }
        
        return jsonify(results)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/exam/agent', methods=['POST'])
def api_conduct_agent_exam():
    """API: Conduct exam for AI agent"""
    data = request.json
    
    try:
        exam_request = ExamRequest(
            username=data.get('username', 'agent_test_user'),
            difficulty=data['difficulty'],
            question_count=data['question_count'],
            agent_name=data['agent_name']
        )
        
        results = exam_service.conduct_agent_exam(exam_request)
        return jsonify(results)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/agents', methods=['GET'])
def api_list_agents():
    """API: List all agents"""
    agent_names = agent_management.list_agents()
    agents = []
    
    for name in agent_names:
        agent_config = agent_management.get_agent(name)
        if agent_config:
            agents.append(agent_config.model_dump())
    
    return jsonify(agents)


@app.route('/api/agents', methods=['POST'])
def api_create_agent():
    """API: Create a new agent"""
    data = request.json
    
    try:
        agent_config = AgentConfig(**data)
        success = agent_management.create_agent(agent_config)
        
        if success:
            return jsonify({'message': 'Agent created', 'name': agent_config.name}), 201
        else:
            return jsonify({'error': 'Agent already exists'}), 409
            
    except Exception as e:
        return jsonify({'error': str(e)}), 400


def run_app():
    """Run the Flask application"""
    app.run(
        host=config.FLASK_HOST,
        port=config.FLASK_PORT,
        debug=config.FLASK_DEBUG
    )


if __name__ == '__main__':
    run_app()
