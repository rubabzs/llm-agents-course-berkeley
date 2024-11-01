from typing import Dict, List
from autogen import ConversableAgent
import sys
import os
import math

def fetch_restaurant_data(restaurant_name: str) -> Dict[str, List[str]]:
    # Example:
    # > fetch_restaurant_data("Applebee's")
    # {"Applebee's": ["The food at Applebee's was average, with nothing particularly standing out.", ...]}
    with open("restaurant-data.txt", "r") as rest_data:
        reviews = {}
        for line in rest_data:
            restaurant, review = line.strip().split('. ', 1)
            if restaurant.lower() == restaurant_name.lower():
                if restaurant not in reviews:
                    reviews[restaurant] = []
                reviews[restaurant].append(review)
    return reviews


def calculate_overall_score(restaurant_name: str, food_scores: List[int], customer_service_scores: List[int]) -> Dict[str, float]:
    N = len(food_scores)
    
    # Calculate the weighted score
    total_score = sum(math.sqrt(food_scores[i]**2 * customer_service_scores[i]) / math.sqrt(125) for i in range(N))
    
    # Normalize and scale to a range of 0 to 10
    final_score = (1 / N) * total_score * 10

    # Format the final score to have 5 decimal places
    final_score = "{:.5f}".format(final_score)

    return final_score


def get_data_fetch_agent_prompt(restaurant_query: str) -> str:
    return f'''Extract the restaurant name from this query: {restaurant_query}. Fetch the restaurant reviews data. 
    Fix the name if no reviews are found.'''

def init_agents(e_msg, d_msg, r_msg, s_msg):
    llm_config = {"config_list": [{"model": "gpt-4o-mini", "api_key": os.environ.get("OPENAI_API_KEY")}]}

    # the main/entrypoint agent 
    e_agent = ConversableAgent("entrypoint_agent", 
                                system_message=e_msg, 
                                llm_config=llm_config,
                                human_input_mode="NEVER",
                                is_termination_msg=lambda msg: "terminate" in (msg["content"].lower() if msg["content"] else ""))
    # data fetch agent
    d_agent = ConversableAgent("data_fetch_agent",
                                system_message=d_msg,
                                llm_config=llm_config,
                                human_input_mode="NEVER")
    # review analyzer agent
    r_agent = ConversableAgent("review_analyzer_agent",
                                system_message=r_msg,
                                llm_config=llm_config,
                                human_input_mode="NEVER")
    # scoring agent
    s_agent = ConversableAgent("scoring_agent",
                                system_message=s_msg,
                                llm_config=llm_config,
                                max_consecutive_auto_reply=1,
                                human_input_mode="NEVER")
    
    return e_agent, d_agent, r_agent, s_agent

# Do not modify the signature of the "main" function.
def main(user_query: str):
    # system messages for all agents
    entrypoint_agent_system_message = """You are a supervisor responsible for starting and ending a task. 
    Look for keyword terminate in the replies and end the converstaion then."""

    data_fetch_agent_system_message = """You have to fetch data for restaurant reviews and return the 
    keyword terminate when you are done. List all reviews without missing any."""

    review_analyzer_agent_system_message = """You are a review analyst and have to compute food_score and 
    customer_service_score for all reviews of a restaurant. The scoring method is as follows:
    - Score 1/5 has one of these adjectives: awful, horrible, or disgusting.
    - Score 2/5 has one of these adjectives: bad, unpleasant, or offensive.
    - Score 3/5 has one of these adjectives: average, uninspiring, or forgettable.
    - Score 4/5 has one of these adjectives: good, enjoyable, or satisfying.
    - Score 5/5 has one of these adjectives: awesome, incredible, or amazing.
    
    Each review has exactly only two of these keywords. Return two lists. One for food_scores and the other
    for customer_service_score. Add terminate in your reply when you are done."""

    scoring_agent_system_message = """You are responsible for calculating overall scores from individual lists 
    of scores based on a function."""

    # the main entrypoint/supervisor agent
    entrypoint_agent, data_fetch_agent, review_analyzer_agent, scoring_agent = init_agents(entrypoint_agent_system_message,
                                                                                            data_fetch_agent_system_message,
                                                                                            review_analyzer_agent_system_message,
                                                                                            scoring_agent_system_message)

    # register tool calls for all relevant agents
    entrypoint_agent.register_for_llm(name="fetch_restaurant_data", description="""Fetches the reviews for a 
                                      specific restaurant.""")(fetch_restaurant_data)
    entrypoint_agent.register_for_execution(name="fetch_restaurant_data")(fetch_restaurant_data)

    entrypoint_agent.register_for_llm(name="calculate_overall_score", description="""Calculates overall score from 
                                      lists of food_scores and customer_service_score")(calculate_overall_score""")
    entrypoint_agent.register_for_execution(name="calculate_overall_score")(calculate_overall_score)

    data_fetch_agent.register_for_llm(name="fetch_restaurant_data", description="""Fetches the reviews for a specific 
                                      restaurant.""")(fetch_restaurant_data)
    data_fetch_agent.register_for_execution(name="fetch_restaurant_data")(fetch_restaurant_data)

    scoring_agent.register_for_llm(name="calculate_overall_score", description="""Calculates overall score from lists 
                                   of food_scores and customer_service_score""")(calculate_overall_score)
    scoring_agent.register_for_execution(name="calculate_overall_score")(calculate_overall_score)
    

    result = entrypoint_agent.initiate_chats([
                                                {"recipient": data_fetch_agent,
                                                "message": get_data_fetch_agent_prompt(user_query),
                                                "summary_method": "last_msg"}, 
                                                {"recipient": review_analyzer_agent,
                                                "message": "These are the restaurant reviews.",
                                                "summary_method": "last_msg"},
                                                {"recipient": scoring_agent,
                                                 "message": "These are the scores for food and customer service of all reviews.",
                                                 "summary_method": "last_msg"}
                                                 
                                            ])
    return result
    
# DO NOT modify this code below.
if __name__ == "__main__":
    assert len(sys.argv) > 1, "Please ensure you include a query for some restaurant when executing main."
    main(sys.argv[1])