#!/usr/bin/env python3

"""
Example usage of the Medical Document Processing Assistant
"""

from strands import Agent, tool
from strands.models import BedrockModel
from document_processor import process_document
from medical_coding_tools import (
    get_icd, get_rx, get_snomed,
    link_icd, link_rx, link_snomed
)

model = BedrockModel(
    model_id="anthropic.claude-3-5-haiku-20241022-v1:0",
    # region_name="us-east-1",
    # boto_client_config=Config(
    #    read_timeout=900,
    #    connect_timeout=900,
    #    retries=dict(max_attempts=3, mode="adaptive"),
    # ),
    # temperature=0.9,
    # max_tokens=2048,
)
# Create the medical document processing agent
system_prompt="You are a specialized medical document analysis system designed to process clinical documents (PDFs, images) and enrich them with standardized medical codes."

medical_agent = Agent(
    model=model,
    system_prompt=system_prompt,
    tools=[
        process_document,
        get_icd, get_rx, get_snomed,
        link_icd, link_rx, link_snomed
    ]
)

# Example clinical note
CLINICAL_NOTE = """
Carlie had a seizure 2 weeks ago. She is complaining of frequent headaches
Nausea is also present. She also complains of eye trouble with blurry vision
Meds : Topamax 50 mgs at breakfast daily,
Send referral order to neurologist
Follow-up as scheduled
"""

def run_example():
    print("\n🏥 Medical Document Processing Example 🏥\n")
    print("Clinical Note:")
    print("-" * 50)
    print(CLINICAL_NOTE)
    print("-" * 50)
    
    print("\nProcessing clinical note...\n")
    
    # Process the clinical note
    response = medical_agent(
        f"Process this clinical note and extract diagnoses, medications, and treatments with their respective medical codes: {CLINICAL_NOTE}"
    )
    
    print("\nProcessing complete!\n")
    print("Usage metrics:")
    print(medical_agent.event_loop_metrics)

if __name__ == "__main__":
    run_example()
