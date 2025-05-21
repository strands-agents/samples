# DSQL-do is a tool to do things on a DSQL cluster

Setup:

    export DSQL_CLUSTER=<your dsql cluster name>
    export DSQL_CLUSTER_REGION=<your cluster region> # defaults to us-east-1 if not set
    uv run dsql-do.py <prompt>

Examples:

    uv run dsql-do.py "List all tables in the database"
    uv run dsql-do.py "Explain the following query and suggest ways to improve it: ..."
    uv run dsql-do.py "Create a table called bank with an id column and a balance column using appropriate data types."
    uv run dsql-do.py "Fill the bank table with 100 rows of random example data. Make sure the sum of all balance columns equals 1000."
    