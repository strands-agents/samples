"""
Entry point for the NL2SQL agent.
"""
import argparse
import logging

from src.agent import create_nl2sql_agent

def setup_logging(level=logging.INFO):
    """
    Configure logging for the application.
    
    Args:
        level: Logging level (default: INFO)
    """
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def main():
    """
    Main entry point for the NL2SQL agent.
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="NL2SQL Agent using Strands SDK")
    parser.add_argument("--question", "-q", type=str, help="Natural language question to convert to SQL")
    parser.add_argument(
        "--engine", 
        "-e", 
        choices=["sqllite","athena"],
        default="sqllite" , 
        type=str, 
        help="Query engine, by default sqllite, can support athena"
    )
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.INFO
    setup_logging(level=log_level)
    
    logger = logging.getLogger(__name__)
    logger.info("Starting NL2SQL agent")

    query_engine = args.engine or ""
    
    # Create the agent
    agent = create_nl2sql_agent(query_engine)
    
    # If a question was provided, process it
    if args.question:
        logger.info(f"Processing question: {args.question}")
        agent(args.question)

    logger.info("NL2SQL agent finished")

if __name__ == "__main__":
    main()
