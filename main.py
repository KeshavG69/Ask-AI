from agno.agent import Agent
from agno.models.openai import OpenAIChat
from web_crawler_tool import WebCrawlerTool
from agno.tools.reasoning import ReasoningTools
import os
from dotenv import load_dotenv

load_dotenv()


def create_web_support_agent(starting_urls: list):
    """Create a web support agent with crawling capabilities."""

    # Create the crawler tool - it will automatically extract allowed domains from starting URLs
    crawler_tool = WebCrawlerTool(starting_urls=starting_urls)

    # Create agent with intelligent instructions
    agent = Agent(
        model=OpenAIChat(id="gpt-4.1", api_key=os.getenv("OPENAI_API_KEY")),
        tools=[crawler_tool,ReasoningTools()],
        description=f"You are an agent that answers user queries based exclusively on content from the starting URLs: {', '.join(starting_urls)}. The starting URLs serve only as the content source - you crawl them to get information and answer questions based on that content.",
        instructions=[
            # CORE PURPOSE
            f"You answer user queries using ONLY content scraped from these starting URLs: {', '.join(starting_urls)}",
            "The starting URLs have no other role - they are simply your content source.",
            "",
            # WORKFLOW
            "🔍 WORKFLOW:",
            "1. Review the 'site_structure_and_imp_info' context (pre-discovered URLs from the starting websites)",
            "2. Select URLs relevant to the user's question",
            "3. Use crawl_selected_urls(['url1', 'url2', 'url3']) to get content",
            "4. Answer based ONLY on the scraped content",
            "5. If more info needed, crawl additional relevant URLs",
            "",
            # DATA RULES
            "🔒 CRITICAL RULES:",
            "- ONLY use information from scraped content",
            "- NEVER use external knowledge or training data",
            "- If info not found in scraped content, say so explicitly",
            "- Quote directly from scraped content when possible",
            "",
            # ANTI-HALLUCINATION
            "🚫 ANTI-HALLUCINATION RULES:",
            "- NEVER invent, assume, or guess information that is not explicitly stated in scraped content",
            "- NEVER fill knowledge gaps with general knowledge or training data",
            "- If asked about something not found in scraped content, clearly state 'This information is not available in the scraped content'",
            "- Do not make logical inferences beyond what is directly stated",
            "- When uncertain about any detail, explicitly say 'The scraped content does not specify this'",
            "- NEVER provide approximate, estimated, or 'typical' information",
            "- If only partial information is available, clearly indicate what is missing",
            "- Do not extrapolate or expand on limited information",
            "",
            # RESPONSE STYLE
            "💬 RESPONSE STYLE:",
            "- Provide direct answers without mentioning scraping, crawling, or website analysis",
            "- Do not tell users about the technical process of gathering information",
            "- Skip opening statements like 'I'll help you find...' or 'Let me search...'",
            "- Skip closing statements like 'Let me know if you need more...' or 'Hope this helps'",
            "- Do not add closing statements that reference where information came from",
            "- Do not add source attribution statements like 'Everything above was referenced from...'",
            "- Do not mention the documentation source at the end of responses",
            "- No disclaimers about information sources in closing statements",
            "- End responses immediately after providing the requested information",
            "- Give concise, direct responses that answer the question immediately",
            "",
            # REASONING TOOL USAGE
            "🧠 USE REASONING TOOL:",
            "- ALWAYS use the reasoning tool at least once per response to plan your approach",
            "- Use it at the beginning to analyze the question and plan which URLs to crawl",
            "- Use it to decide which URLs are most relevant to crawl first based on the question",
            "- Use it to analyze and connect information from multiple scraped pages",
            "- Use it to verify your answer completeness and accuracy before responding",
            "- Use it to break down multi-part questions into logical components",
            "- Use it when you need to determine if you have sufficient information or need more crawling",
            "- Use it to identify potential gaps in your knowledge from scraped content",
            "",
            # SELECTION TIPS
            "💡 URL SELECTION:",
            "- Match URL paths to user's question (e.g., '/faq' for questions, '/api' for technical)",
            "- Prioritize llms.txt URLs (AI-optimized)",
            "- Crawl 2-4 URLs at a time",
            "- Keep exploring until you have complete information",
        ],
        show_tool_calls=True,
        markdown=True,
        debug_mode=True,
        add_context=True,
        context={
            "answer_groundedness": f"CRITICAL REQUIREMENT: Every single piece of information in your answers must come exclusively from content you actually scraped from these specific websites: {', '.join(starting_urls)}. You are absolutely forbidden from using any external knowledge, training data, general facts, or assumptions. If information is not found in the scraped content, explicitly state 'This information was not found in the scraped website content.' Never fill knowledge gaps with external information.",
            "site_structure_and_imp_info": WebCrawlerTool(starting_urls=starting_urls).discover_site_structure(starting_urls),
        },
    )

    return agent


def demo_web_support_bot():
    """Demo the web support bot with example websites."""

    print("=== Web Support Bot Demo ===\n")

    # Example: Create agent for a hypothetical e-commerce site
    starting_urls = ["https://docs.agno.com/introduction"]

    agent = create_web_support_agent(starting_urls)

    # Get the automatically extracted domains for display
    allowed_domains = agent.tools[0].allowed_domains

    print("🤖 Web Support Agent created!")
    print(f"📝 Starting URLs: {', '.join(starting_urls)}")
    print(f"🌐 Auto-detected allowed domains: {', '.join(allowed_domains)}")
    print("\n" + "=" * 50 + "\n")

    # Example questions
    questions = [
        "create a agent which uses web scraper  to answer questions only from a particular website using jina",
        # This should be refused
    ]

    for i, question in enumerate(questions, 1):
        print(f"❓ Question {i}: {question}")
        print("-" * 40)

        try:
            agent.print_response(question)
        except Exception as e:
            print(f"Error: {e}")

        print("\n" + "=" * 50 + "\n")


def interactive_mode():
    """Interactive mode where user can specify their own URLs and ask questions."""

    print("=== Interactive Web Support Bot ===\n")

    # Get starting URLs from user
    print("Enter starting URLs (comma-separated):")
    urls_input = input("> ")
    starting_urls = [url.strip() for url in urls_input.split(",") if url.strip()]

    if not starting_urls:
        print("❌ No valid URLs provided. Using example.com as default.")
        starting_urls = ["https://example.com"]

    # Create agent - domains will be auto-extracted
    agent = create_web_support_agent(starting_urls)

    # Get the automatically extracted domains for display
    allowed_domains = agent.tools[0].allowed_domains

    print(f"\n🤖 Web Support Agent created!")
    print(f"📝 Starting URLs: {', '.join(starting_urls)}")
    print(f"🌐 Auto-detected allowed domains: {', '.join(allowed_domains)}")
    print("\n" + "=" * 50)
    print("Ask questions about the website(s). Type 'quit' to exit.\n")

    while True:
        question = input("❓ Your question: ").strip()

        if question.lower() in ["quit", "exit", "q"]:
            print("👋 Goodbye!")
            break

        if not question:
            continue

        print("-" * 40)

        try:
            agent.print_response(question)
        except Exception as e:
            print(f"❌ Error: {e}")

        print("\n" + "=" * 50 + "\n")


if __name__ == "__main__":
    # Check if OpenAI API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Please set your OPENAI_API_KEY in the .env file")
        exit(1)

    print("Choose mode:")
    print("1. Demo mode (uses example.com)")
    print("2. Interactive mode (specify your own URLs)")

    choice = input("Enter choice (1 or 2): ").strip()

    if choice == "1":
        demo_web_support_bot()
    elif choice == "2":
        interactive_mode()
    else:
        print("Invalid choice. Running demo mode...")
        demo_web_support_bot()
