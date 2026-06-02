import os
from dotenv import load_dotenv
from crewai import Agent
from utils.helpers import get_llm
from utils.logger import get_logger

load_dotenv()
os.environ["GEMINI_API_KEY"] = os.getenv("GEMINI_API_KEY", "")

logger = get_logger(__name__)


def build_translation_agent() -> Agent:
    logger.info("Building Translation Agent")
    llm = get_llm()

    agent = Agent(
        role="Expert Multilingual Translator",
        goal=(
            "Translate content accurately into the target language, preserving tone, "
            "structure, meaning, and cultural nuance"
        ),
        backstory=(
            "You are a professional translator with 20 years of experience in technical "
            "and literary translation across 15+ languages. You are deeply culturally aware "
            "and understand that true translation goes beyond word-for-word conversion. "
            "You never rely on machine-literal translations; instead, you craft output that "
            "reads naturally to native speakers while faithfully conveying the original "
            "author's intent, register, and stylistic choices. You are equally comfortable "
            "translating dense technical documentation, creative prose, marketing copy, and "
            "journalistic articles, always adapting idioms and cultural references so they "
            "resonate authentically with the target audience."
        ),
        llm=llm,
        tools=[],
        verbose=True,
        allow_delegation=False,
        max_iter=2,
        memory=False,
    )

    logger.info("Translation Agent built successfully")
    return agent
