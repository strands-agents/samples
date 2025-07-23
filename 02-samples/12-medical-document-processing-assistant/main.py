#!/usr/bin/env python3

import logging
import os

from document_processor import process_document
from dotenv import load_dotenv
from medical_coding_tools import (
    get_icd,
    get_rx,
    get_snomed,
    link_icd,
    link_rx,
    link_snomed,
)
from strands import Agent
from strands_tools import file_read

# Load environment variables
load_dotenv()

# Configure logging
logging.getLogger("strands").setLevel(logging.INFO)
logging.basicConfig(
    format="%(levelname)s | %(name)s | %(message)s", handlers=[logging.StreamHandler()]
)

# System prompt for the medical document processing agent
SYSTEM_PROMPT = """
You are a Medical Document Processing Assistant specialized in extracting and analyzing medical information from clinical documents.

Your tasks include:
1. Processing medical documents (PDFs, images) to extract text
2. Identifying key medical information: diagnoses, medications, treatments
3. Enriching the extracted information with standardized medical codes:
   - ICD-10 codes for diagnoses
   - RxNorm codes for medications
   - SNOMED CT codes for treatments

Provide clear, accurate, and structured information that can be used by healthcare professionals.
"""

# Create the medical document processing agent
medical_agent = Agent(
    system_prompt=SYSTEM_PROMPT,
    tools=[
        file_read,
        process_document,
        get_icd,
        get_rx,
        get_snomed,
        link_icd,
        link_rx,
        link_snomed,
    ],
)


def main():
    print("\n🏥 Welcome to the Medical Document Processing Assistant! 🏥\n")
    print(
        "This assistant can process medical documents (PDFs or images) to extract and enrich medical information."
    )
    print(
        "It will identify diagnoses, medications, and treatments, and link them to standardized medical codes."
    )

    while True:
        print("\nOptions:")
        print("1. Process a document (provide file path)")
        print("2. Process a clinical note (text input)")
        print("3. Process a sample clinical note (automatically provided)")
        print("4. Exit")

        choice = input("\nEnter your choice (1-3): ")

        if choice == "1":
            file_path = input(
                "\nEnter the path to the medical document (PDF or image): "
            )
            if not os.path.exists(file_path):
                print(f"Error: File '{file_path}' not found.")
                continue

            response = medical_agent(
                f"Process this medical document and extract diagnoses, medications, and treatments with their respective medical codes: {file_path}"
            )
            print("\nProcessing complete!")

        elif choice == "2":
            print("\nEnter the clinical note (press Enter twice when done):")
            lines = []
            while True:
                line = input()
                if line.strip() == "":
                    break
                lines.append(line)

            clinical_note = "\n".join(lines)
            if not clinical_note.strip():
                print("Error: Empty clinical note.")
                continue

            response = medical_agent(
                f"Process this clinical note and extract diagnoses, medications, and treatments with their respective medical codes: {clinical_note}"
            )
            print("\nProcessing complete!")

        elif choice == "3":
            # Example clinical note
            CLINICAL_NOTE = """
            Carlie had a seizure 2 weeks ago. She is complaining of frequent headaches
            Nausea is also present. She also complains of eye trouble with blurry vision
            Meds : Topamax 50 mgs at breakfast daily,
            Send referral order to neurologist
            Follow-up as scheduled
            """
            response = medical_agent(
                f"Process this clinical note and extract diagnoses, medications, and treatments with their respective medical codes: {CLINICAL_NOTE}"
            )
            print("\nSample processing complete!")

        elif choice == "4":
            print(
                "\nThank you for using the Medical Document Processing Assistant. Goodbye! 👋\n"
            )
            break
        else:
            print("\nInvalid choice. Please try again.")

    print(f"\nAccumulated usage metrics:\n{medical_agent.event_loop_metrics}")


if __name__ == "__main__":
    main()