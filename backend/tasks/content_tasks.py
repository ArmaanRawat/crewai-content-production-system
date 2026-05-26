"""
tasks/content_tasks.py
─────────────────────────────────────────────────────────────────
Task definitions for the content pipeline.

WHAT A TASK IS:
  - A specific assignment given to an agent
  - Has a description (instructions) and expected_output
  - Is linked to one agent

WHY SEPARATE FROM AGENTS:
  - Same agent can be reused with different tasks later
  - Tasks can be swapped without touching agent config
  - Cleaner separation of concerns
─────────────────────────────────────────────────────────────────
"""

from crewai import Task
from agents import build_researcher_agent, build_writer_agent, build_editor_agent, build_seo_agent, build_fact_checker_agent


def build_research_task(topic: str, audience: str) -> Task:
    """
    Task assigned to the Researcher Agent.
    """
    return Task(
        description=(
            f"Research the following topic thoroughly: '{topic}'\n\n"
            f"Target audience: {audience}\n\n"
            "Your job:\n"
            "1. Search for the most relevant and recent information\n"
            "2. Identify key facts, trends, and insights\n"
            "3. Note credible sources\n"
            "4. Summarize findings clearly for the Writer Agent"
        ),

        expected_output=(
            "A structured research summary containing:\n"
            "- Key facts and findings about the topic\n"
            "- Important trends or developments\n"
            "- Relevant statistics or data points\n"
            "- List of sources used\n"
            "Written in clear bullet points, ready for the writer to use."
        ),

        agent=build_researcher_agent(),
    )


def build_writing_task(topic: str, tone: str, word_count: int, audience: str) -> Task:
    """
    Task assigned to the Writer Agent.
    Depends on the research task output.
    """
    return Task(
        description=(
            f"Write a complete article on: '{topic}'\n\n"
            f"Using the research summary provided by the Researcher Agent.\n\n"
            f"Requirements:\n"
            f"- Tone: {tone}\n"
            f"- Target word count: {word_count} words\n"
            f"- Audience: {audience}\n"
            f"- Structure: Introduction, main sections with headings, conclusion\n"
            f"- Do not invent facts — only use what the research provided"
        ),

        expected_output=(
            f"A complete, publication-ready article of approximately {word_count} words.\n"
            "Must include:\n"
            "- Engaging headline\n"
            "- Clear introduction\n"
            "- Well-structured body with subheadings\n"
            "- Strong conclusion\n"
            f"Written in a {tone} tone for {audience}."
        ),

        agent=build_writer_agent(),
    )

def build_editing_task(topic: str, tone: str, audience: str) -> Task:
    """
    Task assigned to the Editor Agent.
    Depends on the writing task output.
    """
    return Task(
        description=(
            f"Edit and refine the draft article about '{topic}'.\n\n"
            f"Requirements:\n"
            f"- Tone must be: {tone}\n"
            f"- Audience: {audience}\n"
            f"- Fix any grammar or spelling issues\n"
            f"- Improve sentence flow and readability\n"
            f"- Remove filler words and redundant phrases\n"
            f"- Ensure headings are clear and consistent\n"
            f"- Do NOT change facts or add new information"
        ),

        expected_output=(
            "A fully edited, publication-ready article that:\n"
            "- Has correct grammar and spelling\n"
            "- Flows naturally from intro to conclusion\n"
            "- Matches the requested tone precisely\n"
            "- Is tighter and cleaner than the draft\n"
            "- Retains all original facts and structure"
        ),

        agent=build_editor_agent(),
    )    


def build_seo_task(topic: str, audience: str) -> Task:
    """
    Task assigned to the SEO Agent.
    Depends on the editing task output.
    """
    return Task(
        description=(
            f"Optimize the edited article about '{topic}' for search engines.\n\n"
            f"Your job:\n"
            f"1. Identify 3-5 primary keywords relevant to '{topic}'\n"
            f"2. Naturally integrate keywords into headings and body\n"
            f"3. Write a compelling meta description (150-160 characters)\n"
            f"4. Ensure H1, H2, H3 headings follow a logical hierarchy\n"
            f"5. Check keyword density — aim for 1-2% naturally\n"
            f"6. Suggest an SEO-optimized title if current one is weak\n"
            f"Target audience: {audience}"
        ),

        expected_output=(
            "The SEO-optimized article with:\n"
            "- Naturally integrated keywords throughout\n"
            "- Clear heading hierarchy (H1 → H2 → H3)\n"
            "- A meta description (150-160 chars) at the top\n"
            "- Primary keywords listed at the bottom\n"
            "- No keyword stuffing — reads naturally"
        ),

        agent=build_seo_agent(),
    )

def build_fact_check_task(topic: str) -> Task:
    """
    Task assigned to the Fact Checker Agent.
    Final task in the pipeline.
    """
    return Task(
        description=(
            f"Fact-check the SEO-optimized article about '{topic}'.\n\n"
            f"Your job:\n"
            f"1. Identify all factual claims, statistics, and named references\n"
            f"2. Verify each one against credible online sources\n"
            f"3. Flag anything that is inaccurate or cannot be verified\n"
            f"4. Correct any errors you find directly in the article\n"
            f"5. Add a short fact-check summary at the end of the article"
        ),

        expected_output=(
            "The final verified article with:\n"
            "- All facts checked and confirmed\n"
            "- Any errors corrected inline\n"
            "- A 'Fact Check Summary' section at the end listing:\n"
            "  * Claims verified ✅\n"
            "  * Claims corrected ⚠️\n"
            "  * Claims unverifiable ❓\n"
            "This is the final publication-ready output."
        ),

        agent=build_fact_checker_agent(),
    )