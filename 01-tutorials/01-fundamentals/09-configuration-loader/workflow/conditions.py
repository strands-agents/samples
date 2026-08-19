"""Condition functions for graph routing.

This module contains condition functions used by the conditional graph
configuration to determine routing between nodes based on classification results.
"""

def is_technical(state):
    """Check if the classifier result indicates a technical classification.
    
    Args:
        state: GraphState containing execution results
        
    Returns:
        bool: True if the classification contains 'technical', False otherwise
    """
    classifier_result = state.results.get("classifier")
    if not classifier_result:
        return False
    result_text = str(classifier_result.result)
    return "technical" in result_text.lower()


def is_business(state):
    """Check if the classifier result indicates a business classification.
    
    Args:
        state: GraphState containing execution results
        
    Returns:
        bool: True if the classification contains 'business', False otherwise
    """
    classifier_result = state.results.get("classifier")
    if not classifier_result:
        return False
    result_text = str(classifier_result.result)
    return "business" in result_text.lower()
