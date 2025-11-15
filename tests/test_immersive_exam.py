"""
Tests for the Immersive Exam feature
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_immersive_exam_models():
    """Test immersive exam models"""
    from models import (
        ImmersiveExamConfig, ImmersiveExam, ImmersiveParticipant,
        RevealStrategy, ParticipantType, Question
    )
    from datetime import datetime
    
    # Test ImmersiveExamConfig
    config = ImmersiveExamConfig(
        difficulty_distribution={"easy": 3, "medium": 2, "hard": 1},
        reveal_strategy=RevealStrategy.REVEAL_TO_LATER_PARTICIPANTS
    )
    assert config.exam_mode == "immersive"
    assert config.difficulty_distribution["easy"] == 3
    assert config.reveal_strategy == RevealStrategy.REVEAL_TO_LATER_PARTICIPANTS
    
    # Test ImmersiveParticipant
    participant = ImmersiveParticipant(
        participant_id="test_user",
        participant_type=ParticipantType.HUMAN,
        order=0,
        answers=[None, None, None],
        scores=[False, False, False]
    )
    assert participant.participant_id == "test_user"
    assert participant.participant_type == ParticipantType.HUMAN
    assert participant.order == 0
    
    # Test ImmersiveExam
    questions = [
        Question(equation="2+2", question_text="What is 2+2?", answer=4.0, difficulty="easy"),
        Question(equation="5*3", question_text="What is 5*3?", answer=15.0, difficulty="medium")
    ]
    
    exam = ImmersiveExam(
        exam_id="test-exam-1",
        config=config,
        questions=questions,
        participants=[participant],
        current_question_index=0,
        status="waiting",
        created_at=datetime.now()
    )
    assert exam.exam_id == "test-exam-1"
    assert len(exam.questions) == 2
    assert len(exam.participants) == 1
    
    print("✅ Immersive Exam Models: All models validated")


def test_immersive_exam_service():
    """Test immersive exam service"""
    from services.immersive_exam import ImmersiveExamService
    from models import ImmersiveExamConfig, RevealStrategy, ParticipantType
    
    service = ImmersiveExamService()
    
    # Create exam
    config = ImmersiveExamConfig(
        difficulty_distribution={"easy": 2, "medium": 1},
        reveal_strategy=RevealStrategy.NONE
    )
    
    exam = service.create_immersive_exam(config)
    assert exam.exam_id is not None
    assert len(exam.questions) == 3  # 2 easy + 1 medium
    assert exam.status == "waiting"
    
    # Register participants
    success = service.register_participant(exam.exam_id, "student1", ParticipantType.HUMAN)
    assert success is True
    
    success = service.register_participant(exam.exam_id, "basic_agent", ParticipantType.AGENT)
    assert success is True
    
    exam = service.get_exam(exam.exam_id)
    assert len(exam.participants) == 2
    
    # Start exam
    success = service.start_exam(exam.exam_id)
    assert success is True
    
    exam = service.get_exam(exam.exam_id)
    assert exam.status == "in_progress"
    
    # Get status
    status = service.get_exam_status(exam.exam_id, "student1")
    assert status is not None
    assert status.current_question_index == 0
    assert status.total_questions == 3
    assert status.current_question is not None
    
    print("✅ Immersive Exam Service: Create, register, start, and status working")


def test_immersive_exam_answer_flow():
    """Test answer submission and advancement"""
    from services.immersive_exam import ImmersiveExamService
    from models import (
        ImmersiveExamConfig, RevealStrategy, ParticipantType, 
        ImmersiveExamAnswer
    )
    
    service = ImmersiveExamService()
    
    # Create exam
    config = ImmersiveExamConfig(
        difficulty_distribution={"easy": 2},
        reveal_strategy=RevealStrategy.REVEAL_ALL_AFTER_ROUND
    )
    
    exam = service.create_immersive_exam(config)
    
    # Register participants
    service.register_participant(exam.exam_id, "student1", ParticipantType.HUMAN)
    service.register_participant(exam.exam_id, "student2", ParticipantType.HUMAN)
    
    # Start exam
    service.start_exam(exam.exam_id)
    
    # Get first question
    exam = service.get_exam(exam.exam_id)
    first_question = exam.questions[0]
    
    # Submit answer from first participant
    answer1 = ImmersiveExamAnswer(
        exam_id=exam.exam_id,
        participant_id="student1",
        question_index=0,
        answer=first_question.answer  # Correct answer
    )
    
    success = service.submit_answer(answer1)
    assert success is True
    
    # Check if all answered
    all_answered = service.check_all_answered_current(exam.exam_id)
    assert all_answered is False  # student2 hasn't answered yet
    
    # Submit answer from second participant
    answer2 = ImmersiveExamAnswer(
        exam_id=exam.exam_id,
        participant_id="student2",
        question_index=0,
        answer=first_question.answer + 1  # Wrong answer
    )
    
    success = service.submit_answer(answer2)
    assert success is True
    
    # Check if all answered
    all_answered = service.check_all_answered_current(exam.exam_id)
    assert all_answered is True
    
    # Advance to next question
    success = service.advance_to_next_question(exam.exam_id)
    assert success is True
    
    exam = service.get_exam(exam.exam_id)
    assert exam.current_question_index == 1
    
    # Get participant scores
    participant1 = exam.participants[0]
    assert participant1.answers[0] == first_question.answer
    assert participant1.scores[0] is True  # Correct
    
    participant2 = exam.participants[1]
    assert participant2.scores[0] is False  # Incorrect
    
    print("✅ Immersive Exam Answer Flow: Submit, check, and advance working")


def test_reveal_strategies():
    """Test different reveal strategies"""
    from services.immersive_exam import ImmersiveExamService
    from models import (
        ImmersiveExamConfig, RevealStrategy, ParticipantType,
        ImmersiveExamAnswer
    )
    
    service = ImmersiveExamService()
    
    # Test reveal_to_later_participants
    config = ImmersiveExamConfig(
        difficulty_distribution={"easy": 1},
        reveal_strategy=RevealStrategy.REVEAL_TO_LATER_PARTICIPANTS
    )
    
    exam = service.create_immersive_exam(config)
    service.register_participant(exam.exam_id, "student1", ParticipantType.HUMAN)
    service.register_participant(exam.exam_id, "student2", ParticipantType.HUMAN)
    service.start_exam(exam.exam_id)
    
    # Student1 submits answer
    exam_obj = service.get_exam(exam.exam_id)
    answer1 = ImmersiveExamAnswer(
        exam_id=exam.exam_id,
        participant_id="student1",
        question_index=0,
        answer=exam_obj.questions[0].answer
    )
    service.submit_answer(answer1)
    
    # Student2 should see student1's answer (lower order)
    status = service.get_exam_status(exam.exam_id, "student2")
    assert status.can_see_previous_answers is True
    assert len(status.previous_answers) == 1
    assert status.previous_answers[0]['participant_id'] == "student1"
    
    # Student1 should not see others (no one before them)
    status = service.get_exam_status(exam.exam_id, "student1")
    assert status.can_see_previous_answers is True
    assert len(status.previous_answers) == 0
    
    print("✅ Reveal Strategies: Reveal to later participants working")


def test_exam_completion():
    """Test exam completion and results"""
    from services.immersive_exam import ImmersiveExamService
    from models import (
        ImmersiveExamConfig, RevealStrategy, ParticipantType,
        ImmersiveExamAnswer
    )
    
    service = ImmersiveExamService()
    
    config = ImmersiveExamConfig(
        difficulty_distribution={"easy": 2},
        reveal_strategy=RevealStrategy.NONE
    )
    
    exam = service.create_immersive_exam(config)
    service.register_participant(exam.exam_id, "student1", ParticipantType.HUMAN)
    service.start_exam(exam.exam_id)
    
    exam_obj = service.get_exam(exam.exam_id)
    
    # Answer all questions
    for i in range(len(exam_obj.questions)):
        answer = ImmersiveExamAnswer(
            exam_id=exam.exam_id,
            participant_id="student1",
            question_index=i,
            answer=exam_obj.questions[i].answer
        )
        service.submit_answer(answer)
        service.advance_to_next_question(exam.exam_id)
    
    # Check exam status
    exam_obj = service.get_exam(exam.exam_id)
    assert exam_obj.status == "completed"
    
    # Get results
    results = service.get_exam_results(exam.exam_id)
    assert results is not None
    assert results['status'] == "completed"
    assert results['total_questions'] == 2
    assert len(results['participants']) == 1
    assert results['participants'][0]['total_score'] == 2  # All correct
    assert results['participants'][0]['score_percentage'] == 100.0
    
    print("✅ Exam Completion: Completion and results working")


def run_all_tests():
    """Run all immersive exam tests"""
    print("\n🧪 Running Immersive Exam Tests")
    print("=" * 50)
    
    tests = [
        test_immersive_exam_models,
        test_immersive_exam_service,
        test_immersive_exam_answer_flow,
        test_reveal_strategies,
        test_exam_completion,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"❌ {test.__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Total: {passed + failed}")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
