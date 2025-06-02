from market_research_team import market_research_team
from writer_team import writer_team

if __name__ == "__main__":
    query = """Create a marketing strategy ofc the following:

    Project Name: FlyingCars wants to be the leading supplier of flying cars. 
    The project is to build an innovative marketing strategy to showcase FlyingCars' advanced 
    offerings, emphasizing ease of use, cost effectiveness, productivity, and safety. 
    Target high net worth individuals, highlighting success stories and transformative 
    potential. Be sure to include a draft for a video ad.
    """

    market_research = market_research_team(query)
    writer_team(market_research)
