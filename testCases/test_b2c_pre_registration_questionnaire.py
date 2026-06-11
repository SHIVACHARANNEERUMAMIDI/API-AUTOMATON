import pytest
from underwriter_api.user_actions import UserActions
from utilities.customLogger import customLogger

logger = customLogger("TestPreRegistrationQuestionnaire")

@pytest.mark.questions
class TestPreRegistrationQuestionnaire:
    """Verify pre-registration questionnaire public REST endpoints."""

    @pytest.mark.P0
    @pytest.mark.Smoke
    def test_get_questionnaire_categories(self):
        """Verify that questionnaire categories can be retrieved successfully without authorization."""
        logger.info("Fetching questionnaire categories (public endpoint)...")
        res = UserActions.get_questionnaire_categories()
        
        assert res.status_code == 200, f"Expected 200 but got {res.status_code}: {res.text}"
        categories = res.json()
        assert isinstance(categories, list), "Expected response to be a list of categories"
        assert len(categories) > 0, "Categories list should not be empty"
        
        # Verify specific category fields & business data
        first_category = categories[0]
        assert "categoryId" in first_category, "categoryId key missing from category details"
        assert "categoryName" in first_category, "categoryName key missing from category details"
        
        category_ids = [c.get("categoryId") for c in categories]
        assert "C1" in category_ids, "Expected category C1 (Insurance) in retrieved categories"
        assert "C5" in category_ids, "Expected category C5 (Mental Health Assessments) in retrieved categories"
        
        logger.info(f"Retrieved {len(categories)} categories successfully. Found key categories: {category_ids}")

    @pytest.mark.P1
    @pytest.mark.Regression
    def test_get_pre_registration_questionnaire(self):
        """Verify that questionnaire items can be fetched by category IDs without authorization."""
        logger.info("Fetching questionnaire items for categories C1, C3, C5 (public endpoint)...")
        res = UserActions.get_pre_registration_questionnaire("C1,C3,C5")
        
        assert res.status_code == 200, f"Expected 200 but got {res.status_code}: {res.text}"
        data = res.json()
        
        # Verify business data and structure
        assert "assessmentSessionId" in data, "assessmentSessionId missing from response"
        assert "categories" in data, "categories list missing from response"
        
        categories_list = data["categories"]
        assert isinstance(categories_list, list), "categories should be a list"
        assert len(categories_list) > 0, "categories list should not be empty"
        
        category_names = [c.get("category") for c in categories_list]
        assert "Insurance" in category_names, "Expected 'Insurance' category in retrieved questionnaire"
        
        first_cat = categories_list[0]
        questions = first_cat.get("questions", [])
        assert isinstance(questions, list), "questions should be a list"
        if len(questions) > 0:
            first_q = questions[0]
            assert "questionText" in first_q, "questionText key missing from question"
            assert "options" in first_q, "options key missing from question"
            assert isinstance(first_q.get("options"), list), "options should be a list"
            
        logger.info(f"Questionnaire fetched successfully. Assessment Session ID: {data['assessmentSessionId']}")
