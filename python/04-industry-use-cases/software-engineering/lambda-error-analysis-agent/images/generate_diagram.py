#!/usr/bin/env python3
"""
Lambda Error Analysis Architecture Diagram Generator
Uses the diagrams library to generate the architecture diagram
"""

from diagrams import Diagram, Edge, Cluster, Node
from diagrams.aws.compute import Lambda
from diagrams.aws.integration import Eventbridge
from diagrams.aws.ml import Bedrock
from diagrams.aws.storage import S3
from diagrams.aws.management import CloudwatchLogs
from diagrams.aws.database import Dynamodb
# from diagrams.aws.messaging import SNS  # Not needed
from diagrams.aws.general import Users, Toolkit, GenericDatabase, Forums
from diagrams.aws.analytics import AmazonOpensearchService

def generate_lambda_error_analysis_diagram():
    """Generate the Lambda Error Analysis Architecture diagram"""
    
    with Diagram("Lambda Error Analysis Architecture", show=False, direction="LR", filename="lambda-error-analysis-architecture"):
        # Left side - Source System with User positioned better
        with Cluster("Source System"):
            # Changed from Developer to User - makes more sense
            user = Users("User")
            
            # Force 3 Lambda functions to be aligned horizontally with shorter text
            with Cluster("Lambda Functions with @decorator"):
                # Create them with shorter, more concise labels
                lambdas = [
                    Lambda("Business Logic\nLambda 1\n@decorator"),
                    Lambda("Business Logic\nLambda 2\n@decorator"), 
                    Lambda("Business Logic\nLambda 3\n@decorator")
                ]
        
        # Center - Event routing
        eventbridge = Eventbridge("EventBridge\nEvent Router")
        
        # Right side - Agent Error Analyzer with Strands SDK - also shorter text
        with Cluster("Agent Error Analyzer Lambda"):
            analyzer_lambda = Lambda("Agent Error\nAnalyzer\n(Strands SDK)")
            
            # 3 tools in a cluster with shorter names
            with Cluster("@tools"):
                tools = [
                    Toolkit("fetch_source\n_code()"),
                    GenericDatabase("fetch_cloudwatch\n_logs()"),  
                    Forums("search_knowledge\n_base()")
                ]
            
            # LLM Model with proper AWS service name
            bedrock_model = Bedrock("Amazon Bedrock\nLLMs")
        
        # Data Sources with shorter AWS service names that fit in boxes
        with Cluster("Analysis Data Sources"):
            s3_source = S3("Source Code &\nKnowledge Docs\nS3")
            cloudwatch = CloudwatchLogs("Execution Logs\nCloudWatch")
            
            # Knowledge Base with underlying OpenSearch Serverless
            with Cluster("Knowledge Base Infrastructure"):
                knowledge_base = Bedrock("Knowledge Base\nAmazon Bedrock")
                opensearch_index = AmazonOpensearchService("Vector Index\nOpenSearch")
            
            dynamodb = Dynamodb("Analysis Results\nAmazon DynamoDB")
        
        # Flow connections - Left to Right with consistent arrows
        user >> Edge(label="executes") >> lambdas
        
        # Decorator captures failures - consistent dashed red arrows
        lambdas[0] >> Edge(label="failure captured\nby @decorator", color="red", style="dashed") >> eventbridge
        lambdas[1] >> Edge(label="failure captured\nby @decorator", color="red", style="dashed") >> eventbridge
        lambdas[2] >> Edge(label="failure captured\nby @decorator", color="red", style="dashed") >> eventbridge
        
        # AI Analysis trigger - solid arrow with error payload info
        eventbridge >> Edge(label="triggers with\nerror payload", color="darkblue") >> analyzer_lambda
        
        # Agent directly uses tools and model - with shorter LLM description
        analyzer_lambda >> Edge(label="invokes LLM\nprocesses outputs", style="dashed", color="purple") >> bedrock_model
        analyzer_lambda >> Edge(label="uses", color="blue", style="dashed") >> tools[0]
        analyzer_lambda >> Edge(label="uses", color="orange", style="dashed") >> tools[1]
        analyzer_lambda >> Edge(label="uses", color="darkred", style="dashed") >> tools[2]
        
        # Tools connect to data sources - consistent dotted arrows with matching colors
        tools[0] >> Edge(label="fetches from", color="blue", style="dotted") >> s3_source
        tools[1] >> Edge(label="retrieves from", color="orange", style="dotted") >> cloudwatch
        tools[2] >> Edge(label="searches", color="darkred", style="dotted") >> knowledge_base
        
        # Knowledge Base infrastructure flow - showing the hidden OpenSearch layer
        knowledge_base >> Edge(label="queries", color="purple", style="dotted") >> opensearch_index
        s3_source >> Edge(label="documents\nfeed to", color="darkgreen", style="dotted") >> opensearch_index
        opensearch_index >> Edge(label="returns\ncontext", color="purple", style="dotted") >> knowledge_base
        
        # Agent stores results in DynamoDB - dotted arrow
        analyzer_lambda >> Edge(label="stores analysis", color="darkgreen", style="dotted") >> dynamodb
        
        # Direct response from DynamoDB to user (no SNS)
        dynamodb >> Edge(label="enhanced error\nanalysis", color="green") >> user

def generate_transparent_diagram():
    """Generate the same diagram with transparent background and specific white text labels"""
    
    with Diagram("Lambda Error Analysis Architecture", 
                 show=False, 
                 direction="LR", 
                 filename="lambda-error-analysis-architecture-transparent",
                 graph_attr={
                     "bgcolor": "transparent"
                 },
                 node_attr={
                     "fontcolor": "black"  # Default nodes to black
                 }):
        
        # Left side - Source System with User positioned better
        with Cluster("Source System"):
            user = Users("User")
            
            # Force 3 Lambda functions to be aligned horizontally with shorter text
            with Cluster("Lambda Functions with @decorator"):
                lambdas = [
                    Lambda("Business Logic\nLambda 1\n@decorator"),
                    Lambda("Business Logic\nLambda 2\n@decorator"), 
                    Lambda("Business Logic\nLambda 3\n@decorator")
                ]
        
        # Center - Event routing with WHITE text
        eventbridge = Eventbridge("EventBridge\nEvent Router", fontcolor="white")
        
        # Right side - Agent Error Analyzer with Strands SDK
        with Cluster("Agent Error Analyzer Lambda"):
            analyzer_lambda = Lambda("Agent Error\nAnalyzer\n(Strands SDK)")
            
            # 3 tools in a cluster with shorter names
            with Cluster("@tools"):
                tools = [
                    Toolkit("fetch_source\n_code()"),
                    GenericDatabase("fetch_cloudwatch\n_logs()"),  
                    Forums("search_knowledge\n_base()")
                ]
            
            # LLM Model with proper AWS service name
            bedrock_model = Bedrock("Amazon Bedrock\nLLMs")
        
        # Data Sources with shorter AWS service names that fit in boxes
        with Cluster("Analysis Data Sources"):
            s3_source = S3("Source Code &\nKnowledge Docs\nS3")
            cloudwatch = CloudwatchLogs("Execution Logs\nCloudWatch")
            
            # Knowledge Base with underlying OpenSearch Serverless
            with Cluster("Knowledge Base Infrastructure"):
                knowledge_base = Bedrock("Knowledge Base\nAmazon Bedrock")
                opensearch_index = AmazonOpensearchService("Vector Index\nOpenSearch")
            
            dynamodb = Dynamodb("Analysis Results\nAmazon DynamoDB")
        
        # Flow connections - Left to Right with consistent arrows
        user >> Edge(label="executes") >> lambdas
        
        # Decorator captures failures - WHITE TEXT for these labels
        lambdas[0] >> Edge(label="failure captured\nby @decorator", color="red", style="dashed", fontcolor="white") >> eventbridge
        lambdas[1] >> Edge(label="failure captured\nby @decorator", color="red", style="dashed", fontcolor="white") >> eventbridge
        lambdas[2] >> Edge(label="failure captured\nby @decorator", color="red", style="dashed", fontcolor="white") >> eventbridge
        
        # AI Analysis trigger - WHITE TEXT for this label
        eventbridge >> Edge(label="triggers with\nerror payload", color="darkblue", fontcolor="white") >> analyzer_lambda
        
        # Agent directly uses tools and model
        analyzer_lambda >> Edge(label="invokes LLM\nprocesses outputs", style="dashed", color="purple") >> bedrock_model
        analyzer_lambda >> Edge(label="uses", color="blue", style="dashed") >> tools[0]
        analyzer_lambda >> Edge(label="uses", color="orange", style="dashed") >> tools[1]
        analyzer_lambda >> Edge(label="uses", color="darkred", style="dashed") >> tools[2]
        
        # Tools connect to data sources - WHITE TEXT for these labels
        tools[0] >> Edge(label="fetches from", color="blue", style="dotted", fontcolor="white") >> s3_source
        tools[1] >> Edge(label="retrieves from", color="orange", style="dotted", fontcolor="white") >> cloudwatch
        tools[2] >> Edge(label="searches", color="darkred", style="dotted", fontcolor="white") >> knowledge_base
        
        # Knowledge Base infrastructure flow
        knowledge_base >> Edge(label="queries", color="purple", style="dotted") >> opensearch_index
        s3_source >> Edge(label="documents\nfeed to", color="darkgreen", style="dotted") >> opensearch_index
        opensearch_index >> Edge(label="returns\ncontext", color="purple", style="dotted") >> knowledge_base
        
        # Agent stores results in DynamoDB - WHITE TEXT for this label
        analyzer_lambda >> Edge(label="stores analysis", color="darkgreen", style="dotted", fontcolor="white") >> dynamodb
        
        # Direct response from DynamoDB to user - WHITE TEXT for this label
        dynamodb >> Edge(label="enhanced error\nanalysis", color="green", fontcolor="white") >> user

if __name__ == "__main__":
    print("Generating Lambda Error Analysis Architecture diagrams...")
    
    # Generate regular diagram
    generate_lambda_error_analysis_diagram()
    print("✅ Regular diagram generated: lambda-error-analysis-architecture.png")
    
    # Generate transparent background diagram
    generate_transparent_diagram()
    print("✅ Transparent diagram generated: lambda-error-analysis-architecture-transparent.png")
    
    print("\nTo run this script:")
    print("1. Install dependencies: pip install diagrams")
    print("2. Run: python generate_diagram.py")
    print("3. Outputs:")
    print("   - lambda-error-analysis-architecture.png (white background)")
    print("   - lambda-error-analysis-architecture-transparent.png (transparent background)")