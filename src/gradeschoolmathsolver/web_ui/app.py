"""
Web UI Service
Flask-based web interface for the GradeSchoolMathSolver system
"""
from typing import Any, Dict, List, Optional, Tuple, Union
from flask import Flask, render_template, request, jsonify, Response
from flask_cors import CORS
from gradeschoolmathsolver.config import Config
from gradeschoolmathsolver.models import (
    ExamRequest, AgentConfig, ImmersiveExamConfig,
    ImmersiveExamAnswer, ParticipantType, RevealStrategy
)
from gradeschoolmathsolver.services.account import AccountService
from gradeschoolmathsolver.services.exam import ExamService
from gradeschoolmathsolver.services.agent_management import AgentManagementService
from gradeschoolmathsolver.services.immersive_exam import ImmersiveExamService
from gradeschoolmathsolver.services.mistake_review import MistakeReviewService


app = Flask(__name__, template_folder='templates')
CORS(app)

config = Config()
account_service = AccountService()
exam_service = ExamService()
agent_management = AgentManagementService()
immersive_exam_service = ImmersiveExamService()
mistake_review_service = MistakeReviewService()

# Create default agents on startup
agent_management.create_default_agents()

# Type alias for Flask response types
FlaskResponse = Union[Response, str, Tuple[Response, int], Tuple[str, int]]


@app.route('/')
def index() -> str:
    """Home page"""
    return render_template('index.html')


@app.route('/users')
def users() -> str:
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
def user_detail(username: str) -> FlaskResponse:
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
def exam_page() -> str:
    """Exam page"""
    return render_template('exam.html',
                           difficulty_levels=config.DIFFICULTY_LEVELS)


@app.route('/agents')
def agents_page() -> str:
    """Agents management page"""
    agent_names = agent_management.list_agents()
    agents = []

    for name in agent_names:
        agent_config = agent_management.get_agent(name)
        if agent_config:
            agents.append(agent_config)

    return render_template('agents.html', agents=agents)


@app.route('/mistakes')
def mistake_review_page() -> str:
    """Mistake review page"""
    return render_template('mistake_review.html')


@app.route('/immersive')
def immersive_exam_page() -> str:
    """Immersive exam creation page"""
    agent_names = agent_management.list_agents()
    return render_template('immersive_exam_create.html',
                           difficulty_levels=config.DIFFICULTY_LEVELS,
                           agents=agent_names)


@app.route('/immersive/<exam_id>')
def immersive_exam_live(exam_id: str) -> str:
    """Live immersive exam page"""
    return render_template('immersive_exam_live.html', exam_id=exam_id)


@app.route('/immersive/<exam_id>/results')
def immersive_exam_results(exam_id: str) -> str:
    """Immersive exam results page"""
    return render_template('immersive_exam_results.html', exam_id=exam_id)


# API Routes

@app.route('/api/users', methods=['GET'])
def api_list_users() -> Response:
    """API: List all users"""
    usernames = account_service.list_users()
    users_data = []

    for username in usernames:
        stats = account_service.get_user_stats(username)
        if stats:
            users_data.append(stats.model_dump())

    return jsonify(users_data)


@app.route('/api/users', methods=['POST'])
def api_create_user() -> FlaskResponse:
    """API: Create a new user"""
    data: Dict[str, Any] = request.json or {}
    username = data.get('username')

    if not username:
        return jsonify({'error': 'Username is required'}), 400

    # Check database connection first
    if not account_service._is_connected():
        error_msg = 'Database not connected. Please ensure the database service is running and try again.'
        return jsonify({'error': error_msg}), 503

    success = account_service.create_user(username)

    if success:
        return jsonify({'message': 'User created', 'username': username}), 201
    else:
        return jsonify({'error': 'User already exists or invalid username format'}), 409


@app.route('/api/exam/human', methods=['POST'])
def api_conduct_human_exam() -> FlaskResponse:
    """API: Conduct exam for human user"""
    data: Dict[str, Any] = request.json or {}

    try:
        exam_request = ExamRequest(
            username=data.get('username', ''),
            difficulty=data.get('difficulty', 'easy'),
            question_count=data.get('question_count', 5)
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
def api_submit_human_exam() -> FlaskResponse:
    """API: Submit human exam answers"""
    data: Dict[str, Any] = request.json or {}

    try:
        # The frontend should send questions and answers together
        username = data.get('username')
        difficulty = data.get('difficulty', 'easy')
        questions_data: List[Dict[str, Any]] = data.get('questions', [])
        answers_data: List[Any] = data.get('answers', [])

        if not username or not questions_data or not answers_data:
            return jsonify({'error': 'Missing required fields'}), 400

        if len(questions_data) != len(answers_data):
            return jsonify({'error': 'Questions and answers count mismatch'}), 400

        # Reconstruct Question objects from the data
        from gradeschoolmathsolver.models import Question
        questions = [Question(**q) for q in questions_data]

        # Convert answers to proper type (List[Optional[int]])
        answers: List[Optional[int]] = [
            int(a) if a is not None else None for a in answers_data
        ]

        # Create exam request
        exam_request = ExamRequest(
            username=username,
            difficulty=str(difficulty),
            question_count=len(answers)
        )

        # Process using the new process_human_exam method with pre-generated questions
        results = exam_service.process_human_exam(exam_request, questions, answers)

        return jsonify(results)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 400


@app.route('/api/exam/agent', methods=['POST'])
def api_conduct_agent_exam() -> FlaskResponse:
    """API: Conduct exam for RAG bot"""
    data: Dict[str, Any] = request.json or {}

    try:
        exam_request = ExamRequest(
            username=data.get('username', 'agent_test_user'),
            difficulty=data.get('difficulty', 'easy'),
            question_count=data.get('question_count', 5),
            agent_name=data.get('agent_name')
        )

        results = exam_service.conduct_agent_exam(exam_request)
        return jsonify(results)

    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/agents', methods=['GET'])
def api_list_agents() -> Response:
    """API: List all agents"""
    agent_names = agent_management.list_agents()
    agents = []

    for name in agent_names:
        agent_config = agent_management.get_agent(name)
        if agent_config:
            agents.append(agent_config.model_dump())

    return jsonify(agents)


@app.route('/api/agents', methods=['POST'])
def api_create_agent() -> FlaskResponse:
    """API: Create a new agent"""
    data: Dict[str, Any] = request.json or {}

    try:
        agent_config = AgentConfig(**data)
        success = agent_management.create_agent(agent_config)

        if success:
            return jsonify({'message': 'Agent created', 'name': agent_config.name}), 201
        else:
            return jsonify({'error': 'Agent already exists'}), 409

    except Exception as e:
        return jsonify({'error': str(e)}), 400


# Immersive Exam API Routes

@app.route('/api/exam/immersive/create', methods=['POST'])
def api_create_immersive_exam() -> FlaskResponse:
    """API: Create an immersive exam"""
    data: Dict[str, Any] = request.json or {}

    try:
        # Parse difficulty distribution
        difficulty_distribution = data.get('difficulty_distribution', {})
        reveal_strategy = data.get('reveal_strategy', 'none')
        time_per_question = data.get('time_per_question')

        config = ImmersiveExamConfig(
            difficulty_distribution=difficulty_distribution,
            reveal_strategy=RevealStrategy(reveal_strategy),
            time_per_question=time_per_question
        )

        exam = immersive_exam_service.create_immersive_exam(config)

        return jsonify({
            'exam_id': exam.exam_id,
            'total_questions': len(exam.questions),
            'status': exam.status,
            'message': 'Immersive exam created successfully'
        }), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/exam/immersive/<exam_id>/register', methods=['POST'])
def api_register_participant(exam_id: str) -> FlaskResponse:
    """API: Register participant for immersive exam"""
    data: Dict[str, Any] = request.json or {}

    try:
        participant_id = data.get('participant_id')
        participant_type = data.get('participant_type', 'human')

        if not participant_id:
            return jsonify({'error': 'participant_id is required'}), 400

        success = immersive_exam_service.register_participant(
            exam_id=exam_id,
            participant_id=participant_id,
            participant_type=ParticipantType(participant_type)
        )

        if success:
            return jsonify({
                'message': 'Participant registered',
                'participant_id': participant_id
            }), 200
        else:
            return jsonify({'error': 'Failed to register participant'}), 400

    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/exam/immersive/<exam_id>/start', methods=['POST'])
def api_start_immersive_exam(exam_id: str) -> FlaskResponse:
    """API: Start immersive exam"""
    try:
        success = immersive_exam_service.start_exam(exam_id)

        if success:
            return jsonify({'message': 'Exam started'}), 200
        else:
            return jsonify({'error': 'Failed to start exam'}), 400

    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/exam/immersive/<exam_id>/status', methods=['GET'])
def api_get_immersive_exam_status(exam_id: str) -> FlaskResponse:
    """API: Get current status of immersive exam"""
    participant_id = request.args.get('participant_id')

    if not participant_id:
        return jsonify({'error': 'participant_id parameter is required'}), 400

    try:
        status = immersive_exam_service.get_exam_status(exam_id, participant_id)

        if status:
            return jsonify(status.model_dump()), 200
        else:
            return jsonify({'error': 'Exam or participant not found'}), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/exam/immersive/<exam_id>/answer', methods=['POST'])
def api_submit_immersive_answer(exam_id: str) -> FlaskResponse:
    """API: Submit answer for current question"""
    data: Dict[str, Any] = request.json or {}

    try:
        answer_submission = ImmersiveExamAnswer(
            exam_id=exam_id,
            participant_id=data.get('participant_id', ''),
            question_index=data.get('question_index', 0),
            answer=int(data.get('answer', 0))
        )

        success = immersive_exam_service.submit_answer(answer_submission)

        if success:
            # Check if all participants have answered
            all_answered = immersive_exam_service.check_all_answered_current(exam_id)

            return jsonify({
                'message': 'Answer submitted',
                'all_answered': all_answered
            }), 200
        else:
            return jsonify({'error': 'Failed to submit answer'}), 400

    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/exam/immersive/<exam_id>/advance', methods=['POST'])
def api_advance_immersive_exam(exam_id: str) -> FlaskResponse:
    """API: Advance to next question (admin/server control)"""
    try:
        success = immersive_exam_service.advance_to_next_question(exam_id)

        if success:
            exam = immersive_exam_service.get_exam(exam_id)
            return jsonify({
                'message': 'Advanced to next question',
                'current_question_index': exam.current_question_index if exam else None,
                'status': exam.status if exam else None
            }), 200
        else:
            return jsonify({'error': 'Failed to advance'}), 400

    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/exam/immersive/<exam_id>/results', methods=['GET'])
def api_get_immersive_exam_results(exam_id: str) -> FlaskResponse:
    """API: Get final results of immersive exam"""
    try:
        results = immersive_exam_service.get_exam_results(exam_id)

        if results:
            return jsonify(results), 200
        else:
            return jsonify({'error': 'Exam not found'}), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/exam/immersive/list', methods=['GET'])
def api_list_immersive_exams() -> FlaskResponse:
    """API: List all active immersive exams"""
    try:
        exam_ids = immersive_exam_service.list_active_exams()
        exams = []

        for exam_id in exam_ids:
            exam = immersive_exam_service.get_exam(exam_id)
            if exam:
                exams.append({
                    'exam_id': exam.exam_id,
                    'status': exam.status,
                    'total_questions': len(exam.questions),
                    'participants_count': len(exam.participants),
                    'created_at': exam.created_at.isoformat()
                })

        return jsonify(exams), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 400


# Mistake Review API Routes

@app.route('/api/mistakes/next/<username>', methods=['GET'])
def api_get_next_mistake(username: str) -> FlaskResponse:
    """API: Get the next mistake to review for a user"""
    try:
        mistake = mistake_review_service.get_next_mistake(username)

        if mistake:
            return jsonify(mistake.model_dump())
        else:
            return jsonify({'message': 'No mistakes to review'}), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/mistakes/count/<username>', methods=['GET'])
def api_get_mistake_count(username: str) -> FlaskResponse:
    """API: Get count of unreviewed mistakes for a user"""
    try:
        count = mistake_review_service.get_unreviewed_count(username)
        return jsonify({'username': username, 'unreviewed_count': count})

    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/mistakes/review', methods=['POST'])
def api_mark_mistake_reviewed() -> FlaskResponse:
    """API: Mark a mistake as reviewed"""
    data: Dict[str, Any] = request.json or {}

    try:
        username = data.get('username')
        mistake_id = data.get('mistake_id')

        if not username or mistake_id is None:
            return jsonify({'error': 'username and mistake_id are required'}), 400

        success = mistake_review_service.mark_as_reviewed(username, mistake_id)

        if success:
            return jsonify({'message': 'Mistake marked as reviewed', 'success': True})
        else:
            return jsonify({'error': 'Failed to mark mistake as reviewed'}), 400

    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/mistakes/all/<username>', methods=['GET'])
def api_get_all_mistakes(username: str) -> FlaskResponse:
    """API: Get all unreviewed mistakes for a user"""
    try:
        limit = request.args.get('limit', 100, type=int)
        mistakes = mistake_review_service.get_all_unreviewed_mistakes(username, limit=limit)

        return jsonify([m.model_dump() for m in mistakes])

    except Exception as e:
        return jsonify({'error': str(e)}), 400


def run_app() -> None:
    """Run the Flask application"""
    app.run(
        host=config.FLASK_HOST,
        port=config.FLASK_PORT,
        debug=config.FLASK_DEBUG
    )


def main() -> None:
    """Main entry point for the application"""
    run_app()


if __name__ == '__main__':
    run_app()
