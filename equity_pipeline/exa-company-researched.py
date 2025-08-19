import os
import exa_py as exa
from typing import Dict, List, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize Exa client
client = exa.Exa(os.environ.get("EXA_API_KEY"))

def research_company(company_name: str) -> Dict:
    """Research a public company and find investor relations info and social profiles."""
    results = {}
    
    # Find investor relations page
    ir_response = client.search_and_contents(
        f"{company_name} investor relations official page",
        num_results=3,
        type="auto",
        category="company",
        text={"max_characters": 3000},
        summary={"query": f"What are the key investor relations resources for {company_name}?"}
    )
    results["investor_relations"] = ir_response.results
    
    # Find latest investor presentations
    presentations = client.search_and_contents(
        f"{company_name} latest investor presentation pdf",
        num_results=3,
        type="auto",
        category="financial report",
        text=False,
        summary={"query": f"What are the key points in this investor presentation?"}
    )
    results["presentations"] = presentations.results
    
    # Find social media profiles
    social_profiles = client.search(
        f"{company_name} official social media profiles LinkedIn Twitter Facebook",
        num_results=5,
        type="auto"
    )
    results["social_profiles"] = social_profiles.results
    
    return results

def format_company_research(research_data: Dict) -> str:
    """Format the research results into a readable report."""
    report = []
    
    # Format investor relations info
    report.append("## Investor Relations Resources")
    for result in research_data["investor_relations"]:
        report.append(f"- [{result.title}]({result.url})")
        if result.summary:
            report.append(f"  Summary: {result.summary}")
    
    # Format presentation info
    report.append("\n## Latest Investor Presentations")
    for result in research_data["presentations"]:
        report.append(f"- [{result.title}]({result.url})")
        if result.summary:
            report.append(f"  Summary: {result.summary}")
    
    # Format social profiles
    report.append("\n## Social Media Profiles")
    for result in research_data["social_profiles"]:
        report.append(f"- [{result.title}]({result.url})")
    
    return "\n".join(report)

# Example usage
if __name__ == "__main__":
    company = input("Enter company name: ")
    research = research_company(company)
    report = format_company_research(research)
    print(report)