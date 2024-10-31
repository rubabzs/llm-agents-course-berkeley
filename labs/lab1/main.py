from typing import Dict, List
from autogen import ConversableAgent
import sys
import os

def fetch_restaurant_data(restaurant_name: str) -> Dict[str, List[str]]:
    # TODO
    # This function takes in a restaurant name and returns the reviews for that restaurant. 
    # The output should be a dictionary with the key being the restaurant name and the value being a list of reviews for that restaurant.
    # The "data fetch agent" should have access to this function signature, and it should be able to suggest this as a function call. 
    # Example:
    # > fetch_restaurant_data("Applebee's")
    # {"Applebee's": ["The food at Applebee's was average, with nothing particularly standing out.", ...]}
    with open("restaurant-data.txt", "r") as rest_data:
        reviews = {}
        for line in rest_data:
            restaurant, review = line.strip().split('. ', 1)
            if restaurant == restaurant_name:
                if restaurant not in reviews:
                    reviews[restaurant] = []
                reviews[restaurant].append(review)
    return reviews


def calculate_overall_score(restaurant_name: str, food_scores: List[int], customer_service_scores: List[int]) -> Dict[str, float]:
    # TODO
    # This function takes in a restaurant name, a list of food scores from 1-5, and a list of customer service scores from 1-5
    # The output should be a score between 0 and 10, which is computed as the following:
    # SUM(sqrt(food_scores[i]**2 * customer_service_scores[i]) * 1/(N * sqrt(125)) * 10
    # The above formula is a geometric mean of the scores, which penalizes food quality more than customer service. 
    # Example:
    # > calculate_overall_score("Applebee's", [1, 2, 3, 4, 5], [1, 2, 3, 4, 5])
    # {"Applebee's": 5.048}
    # NOTE: be sure to that the score includes AT LEAST 3  decimal places. The public tests will only read scores that have 
    # at least 3 decimal places.
    pass

def get_data_fetch_agent_prompt(restaurant_query: str) -> str:
    return f'''Extract the restaurant name from this query: {restaurant_query}. '''
    # TODO
    # It may help to organize messages/prompts within a function which returns a string. 
    # For example, you could use this function to return a prompt for the data fetch agent 
    # to use to fetch reviews for a specific restaurant.
    # for instance extract restaurant name and return as a string for fetch_restaurant_data
    # where is agent coming into play?

def get_review_analysis_agent_prompt(reviews: Dict[str, List[str]]) -> Dict[str, Dict[str, int]]:
    # this should be prompt based
    # TODO: feel free to write as many additional functions as you'd like.
    pass

# Do not modify the signature of the "main" function.
def main(user_query: str):
    entrypoint_agent_system_message = """You are a supervisor that is responsible for coordinating between different agents. The agents available are data_fetch_agent and 
    review_analysis_agent. First get the data fetched then get the reviews analyzed. End the conversation with an agent when their role is done.""" # TODO
    data_fetch_agent_message = "You have to fetch data for restaurant reviews and return the keyword bye as well."
    review_analysis_agent_message = """You have to compute food_score and customer_service_score for all these reviews of a restaurant. The scoring method is as follows:
    - Score 1/5 has one of these adjectives: awful, horrible, or disgusting.
    - Score 2/5 has one of these adjectives: bad, unpleasant, or offensive.
    - Score 3/5 has one of these adjectives: average, uninspiring, or forgettable.
    - Score 4/5 has one of these adjectives: good, enjoyable, or satisfying.
    - Score 5/5 has one of these adjectives: awesome, incredible, or amazing.
    
    Return two lists. One for food_scores and the other for customer_service_score"""

    # example LLM config for the entrypoint agent
    llm_config = {"config_list": [{"model": "gpt-4o-mini", "api_key": os.environ.get("OPENAI_API_KEY")}]}
    # the main entrypoint/supervisor agent
    entrypoint_agent = ConversableAgent("entrypoint_agent", 
                                        system_message=entrypoint_agent_system_message, 
                                        llm_config=llm_config,
                                        human_input_mode="NEVER",
                                        max_consecutive_auto_reply=2)
    entrypoint_agent.register_for_llm(name="fetch_restaurant_data", description="Fetches the reviews for a specific restaurant.")(fetch_restaurant_data)
    entrypoint_agent.register_for_execution(name="fetch_restaurant_data")(fetch_restaurant_data)

    data_fetch_agent = ConversableAgent("data_fetch_agent",
                                        system_message=data_fetch_agent_message,
                                        llm_config=llm_config,
                                        human_input_mode="NEVER")
    data_fetch_agent.register_for_llm(name="fetch_restaurant_data", description="Fetches the reviews for a specific restaurant.")(fetch_restaurant_data)
    data_fetch_agent.register_for_execution(name="fetch_restaurant_data")(fetch_restaurant_data)

    review_analysis_agent = ConversableAgent(name="review_analysis_agent",
                                             system_message="review_analysis_agent_message",
                                             llm_config=llm_config,
                                             max_consecutive_auto_reply=1,
                                             human_input_mode="NEVER")
    
    
    # TODO
    # Create more agents here. 
    
    # TODO
    # Fill in the argument to `initiate_chats` below, calling the correct agents sequentially.
    # If you decide to use another conversation pattern, feel free to disregard this code.
    
    # Uncomment once you initiate the chat with at least one agent.
    result = entrypoint_agent.initiate_chats([{"recipient": data_fetch_agent,
                                               "message": get_data_fetch_agent_prompt(user_query),
                                               "summary_method": "last_msg"}, 
                                               {"recipient": review_analysis_agent,
                                                "message": review_analysis_agent_message,
                                                "summary_method": "last_msg"}])
    print(result)
    return result
    
# DO NOT modify this code below.
if __name__ == "__main__":
    assert len(sys.argv) > 1, "Please ensure you include a query for some restaurant when executing main."
    main(sys.argv[1])