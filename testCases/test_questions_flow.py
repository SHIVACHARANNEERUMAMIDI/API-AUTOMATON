import pytest
from utilities.api_client import API_CLIENT

@pytest.mark.questions
class TestQuestionsFlow:
    """Verify pre-registration questionnaire public REST endpoints."""

    def test_get_questionnaire_categories(self):
        """Verify that questionnaire categories can be retrieved successfully without authorization."""
        print("\n[STEP 1] Fetching questionnaire categories (public endpoint)...")
        res = API_CLIENT.get_rest("pre-registration-questionnaire/categories", _include_auth=False)
        
        assert res.status_code == 200, f"Expected 200 but got {res.status_code}: {res.text}"
        categories = res.json()
        assert isinstance(categories, list), "Expected response to be a list of categories"
        assert len(categories) > 0, "Categories list should not be empty"
        
        # Verify specific category fields
        first_category = categories[0]
        assert "categoryId" in first_category, "categoryId key missing from category details"
        assert "categoryName" in first_category, "categoryName key missing from category details"
        
        # Verify existence of C1 (Insurance) and C5 (Mental Health Assessments)
        category_ids = [c.get("categoryId") for c in categories]
        assert "C1" in category_ids, "Expected category C1 (Insurance) in retrieved categories"
        assert "C5" in category_ids, "Expected category C5 (Mental Health Assessments) in retrieved categories"
        
        print(f"Retrieved {len(categories)} categories successfully. Found key categories: {category_ids}")

    def test_get_pre_registration_questionnaire(self):
        """Verify that questionnaire items can be fetched by category IDs without authorization."""
        print("\n[STEP 1] Fetching questionnaire items for categories C1, C3, C5 (public endpoint)...")
        params = {"categoryIds": "C1,C3,C5"}
        res = API_CLIENT.get_rest("pre-registration-questionnaire", params=params, _include_auth=False)
        
        assert res.status_code == 200, f"Expected 200 but got {res.status_code}: {res.text}"
        data = res.json()
        
        # Verify payload structure
        assert "assessmentSessionId" in data, "assessmentSessionId missing from response"
        assert "categories" in data, "categories list missing from response"
        
        categories_list = data["categories"]
        assert isinstance(categories_list, list), "categories should be a list"
        assert len(categories_list) > 0, "categories list should not be empty"
        
        # Verify categories content
        category_names = [c.get("category") for c in categories_list]
        assert "Insurance" in category_names, "Expected 'Insurance' category in retrieved questionnaire"
        
        # Verify questions structure in category
        first_cat = categories_list[0]
        questions = first_cat.get("questions", [])
        assert isinstance(questions, list), "questions should be a list"
        if len(questions) > 0:
            first_q = questions[0]
            assert "questionText" in first_q, "questionText key missing from question"
            assert "options" in first_q, "options key missing from question"
            assert isinstance(first_q.get("options"), list), "options should be a list"
            
        print(f"Questionnaire fetched successfully. Assessment Session ID: {data['assessmentSessionId']}")
