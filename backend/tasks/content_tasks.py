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
from agents import build_researcher_agent, build_writer_agent


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