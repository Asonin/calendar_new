"""
LLM Client for Agentic Calendar.
Provides abstraction over OpenAI and Anthropic APIs with prompt templates.
"""

import json
import os
import base64
import requests
import re
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Optional, Literal
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def search_web(query: str, num_results: int = 3) -> list[dict]:
    """
    Search the web using DuckDuckGo and return real results.
    Returns list of {title, url, description} dicts.
    """
    try:
        # Use DuckDuckGo HTML search (no API key needed)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }

        # DuckDuckGo HTML search
        encoded_query = urllib.parse.quote_plus(query)
        url = f"https://html.duckduckgo.com/html/?q={encoded_query}"

        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        results = []
        html = response.text

        # Parse results using regex (simple extraction)
        # Find all result blocks
        result_pattern = r'<a rel="nofollow" class="result__a" href="([^"]+)"[^>]*>(.+?)</a>'
        snippet_pattern = r'<a class="result__snippet"[^>]*>(.+?)</a>'

        links = re.findall(result_pattern, html)
        snippets = re.findall(snippet_pattern, html)

        for i, (link, title) in enumerate(links[:num_results]):
            # Clean up title (remove HTML tags)
            clean_title = re.sub(r'<[^>]+>', '', title).strip()

            # Get snippet if available
            description = ""
            if i < len(snippets):
                description = re.sub(r'<[^>]+>', '', snippets[i]).strip()

            # Determine resource type
            resource_type = "article"
            if "youtube.com" in link or "youtu.be" in link:
                resource_type = "video"
            elif "github.com" in link:
                resource_type = "documentation"
            elif any(x in link for x in ["docs.", "documentation", "tutorial"]):
                resource_type = "tutorial"

            results.append({
                "title": clean_title,
                "url": link,
                "type": resource_type,
                "description": description[:200] if description else None
            })

        return results
    except Exception as e:
        print(f"Search failed: {e}")
        return []


def search_youtube(query: str, num_results: int = 2) -> list[dict]:
    """
    Search YouTube and return real video results.
    Uses YouTube's search page scraping (no API key needed).
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
        }

        encoded_query = urllib.parse.quote_plus(query)
        url = f"https://www.youtube.com/results?search_query={encoded_query}"

        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        results = []

        # Extract video IDs and titles from the page
        # YouTube embeds data in a script tag as JSON
        video_pattern = r'"videoId":"([a-zA-Z0-9_-]{11})".*?"title":\{"runs":\[\{"text":"([^"]+)"\}'
        matches = re.findall(video_pattern, response.text)

        seen_ids = set()
        for video_id, title in matches:
            if video_id in seen_ids:
                continue
            seen_ids.add(video_id)

            if len(results) >= num_results:
                break

            results.append({
                "title": title,
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "type": "video",
                "description": f"YouTube video: {title}"
            })

        return results
    except Exception as e:
        print(f"YouTube search failed: {e}")
        return []


def search_resources_for_task(search_query: str) -> list[dict]:
    """
    Search for learning resources related to a task.
    Combines YouTube and web search results.
    """
    resources = []

    # Search YouTube for video tutorials
    youtube_results = search_youtube(search_query, num_results=1)
    resources.extend(youtube_results)

    # Search web for articles/documentation
    web_results = search_web(f"{search_query} guide tutorial", num_results=2)
    resources.extend(web_results)

    return resources[:3]  # Return max 3 resources per task


def search_resources_parallel(tasks: list[dict], max_workers: int = 3) -> dict[int, list[dict]]:
    """
    Search for resources for multiple tasks in parallel.
    Returns dict mapping task index to list of resources.
    """
    results = {}

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_idx = {}
        for idx, task in enumerate(tasks):
            # Use search_query from LLM if available, otherwise use title
            query = task.get("search_query") or f"{task.get('title', '')} tutorial"
            future = executor.submit(search_resources_for_task, query)
            future_to_idx[future] = idx

        for future in as_completed(future_to_idx):
            idx = future_to_idx[future]
            try:
                resources = future.result()
                results[idx] = resources
            except Exception:
                results[idx] = []

    return results


# Prompt Templates
GOAL_UNDERSTANDING_PROMPT = """You are an intelligent planning assistant. Analyze the user's goal and provide a structured understanding.

User's Goal: {goal}
{deadline_info}
{context_info}

Respond with a JSON object containing:
{{
    "summary": "A clear, actionable summary of what the user wants to achieve",
    "feasibility": "high" | "medium" | "low",
    "assumptions": ["List of assumptions you're making about this goal"],
    "missing_information": ["Any critical information that would help plan better"]
}}

Be realistic about feasibility. Consider time constraints, complexity, and typical effort required.
Respond ONLY with valid JSON, no additional text."""


TASK_DECOMPOSITION_PROMPT = """You are an intelligent planning assistant. Break down the following goal into concrete, actionable tasks.

Goal Summary: {goal_summary}
Overall Deadline: {deadline}
Today's Date: {today}

Requirements:
1. Create 3-8 task blocks that logically decompose this goal
2. Each task should be completable in 1-4 hours
3. Order tasks by dependency (what needs to happen first)
4. Be specific and actionable
5. For each task, provide a search_query that can be used to find relevant learning resources (tutorials, videos, documentation)

Respond with a JSON object:
{{
    "tasks": [
        {{
            "title": "Short, clear task title",
            "description": "What specifically needs to be done",
            "estimated_hours": 1.5,
            "priority": "must" | "nice",
            "order": 1,
            "search_query": "A good search query to find tutorials/resources for this task (e.g., 'python pandas dataframe tutorial beginner')"
        }}
    ]
}}

Respond ONLY with valid JSON, no additional text."""


IMAGE_ANALYSIS_PROMPT = """Analyze this image which appears to be a calendar or schedule screenshot.
Extract any relevant information about:
1. Existing appointments or events
2. Busy time slots
3. Any goals or tasks mentioned

Provide a structured summary of what you see."""


class LLMClient:
    """Unified client for LLM API calls."""

    def __init__(self, provider: Literal["openai", "anthropic"] = "openai"):
        self.provider = provider
        self._openai_client = None
        self._anthropic_client = None

    @property
    def openai_client(self):
        if self._openai_client is None:
            from openai import OpenAI
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable not set")
            self._openai_client = OpenAI(api_key=api_key)
        return self._openai_client

    @property
    def anthropic_client(self):
        if self._anthropic_client is None:
            from anthropic import Anthropic
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY environment variable not set")
            self._anthropic_client = Anthropic(api_key=api_key)
        return self._anthropic_client

    def _call_openai(self, messages: list, model: str = "gpt-4o-mini") -> str:
        """Make a call to OpenAI API."""
        response = self.openai_client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.7,
            max_tokens=2000,
        )
        return response.choices[0].message.content

    def _call_anthropic(self, messages: list, model: str = "claude-3-haiku-20240307") -> str:
        """Make a call to Anthropic API."""
        # Convert OpenAI-style messages to Anthropic format
        system_msg = None
        claude_messages = []

        for msg in messages:
            if msg["role"] == "system":
                system_msg = msg["content"]
            else:
                claude_messages.append(msg)

        response = self.anthropic_client.messages.create(
            model=model,
            max_tokens=2000,
            system=system_msg or "You are a helpful assistant.",
            messages=claude_messages,
        )
        return response.content[0].text

    def _call_llm(self, messages: list) -> str:
        """Route to appropriate LLM provider."""
        if self.provider == "openai":
            return self._call_openai(messages)
        else:
            return self._call_anthropic(messages)

    def understand_goal(
        self,
        goal: str,
        deadline: Optional[datetime] = None,
        context: Optional[str] = None,
    ) -> dict:
        """Analyze and understand the user's goal."""
        deadline_info = f"Deadline: {deadline.strftime('%Y-%m-%d %H:%M')}" if deadline else "No specific deadline provided"
        context_info = f"Additional Context: {context}" if context else ""

        prompt = GOAL_UNDERSTANDING_PROMPT.format(
            goal=goal,
            deadline_info=deadline_info,
            context_info=context_info,
        )

        messages = [
            {"role": "system", "content": "You are a helpful planning assistant that outputs valid JSON."},
            {"role": "user", "content": prompt},
        ]

        try:
            response = self._call_llm(messages)
            # Clean up response - remove markdown code blocks if present
            response = response.strip()
            if response.startswith("```"):
                response = response.split("\n", 1)[1]
            if response.endswith("```"):
                response = response.rsplit("```", 1)[0]
            response = response.strip()
            return json.loads(response)
        except json.JSONDecodeError:
            return {
                "summary": goal,
                "feasibility": "medium",
                "assumptions": ["Unable to fully analyze goal - using as-is"],
                "missing_information": [],
            }
        except Exception as e:
            raise RuntimeError(f"LLM API call failed: {str(e)}")

    def decompose_goal(
        self,
        goal_summary: str,
        deadline: Optional[datetime] = None,
        search_resources: bool = True,
    ) -> list[dict]:
        """Break down a goal into task blocks and search for real resources."""
        today = datetime.now().strftime("%Y-%m-%d")
        deadline_str = deadline.strftime("%Y-%m-%d") if deadline else "No specific deadline"

        prompt = TASK_DECOMPOSITION_PROMPT.format(
            goal_summary=goal_summary,
            deadline=deadline_str,
            today=today,
        )

        messages = [
            {"role": "system", "content": "You are a helpful planning assistant that outputs valid JSON."},
            {"role": "user", "content": prompt},
        ]

        try:
            response = self._call_llm(messages)
            # Clean up response
            response = response.strip()
            if response.startswith("```"):
                response = response.split("\n", 1)[1]
            if response.endswith("```"):
                response = response.rsplit("```", 1)[0]
            response = response.strip()
            data = json.loads(response)
            tasks = data.get("tasks", [])

            # Search for real resources using web search
            if search_resources and tasks:
                # Search for resources for each task in parallel
                resource_results = search_resources_parallel(tasks)

                # Add resources to each task
                for idx, task in enumerate(tasks):
                    task["resources"] = resource_results.get(idx, [])

            return tasks
        except json.JSONDecodeError:
            # Return a simple fallback
            return [
                {
                    "title": "Complete main task",
                    "description": goal_summary,
                    "estimated_hours": 2.0,
                    "priority": "must",
                    "order": 1,
                    "resources": [],
                }
            ]
        except Exception as e:
            raise RuntimeError(f"LLM API call failed: {str(e)}")

    def analyze_image(self, image_path: str) -> str:
        """Analyze an image (calendar screenshot) using vision API."""
        if self.provider == "openai":
            return self._analyze_image_openai(image_path)
        else:
            return self._analyze_image_anthropic(image_path)

    def _analyze_image_openai(self, image_path: str) -> str:
        """Analyze image using OpenAI vision."""
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")

        # Determine image type
        suffix = Path(image_path).suffix.lower()
        media_type = "image/png" if suffix == ".png" else "image/jpeg"

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": IMAGE_ANALYSIS_PROMPT},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{media_type};base64,{image_data}"
                        },
                    },
                ],
            }
        ]

        response = self.openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=1000,
        )
        return response.choices[0].message.content

    def _analyze_image_anthropic(self, image_path: str) -> str:
        """Analyze image using Anthropic vision."""
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")

        suffix = Path(image_path).suffix.lower()
        media_type = "image/png" if suffix == ".png" else "image/jpeg"

        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_data,
                        },
                    },
                    {"type": "text", "text": IMAGE_ANALYSIS_PROMPT},
                ],
            }
        ]

        response = self.anthropic_client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=1000,
            messages=messages,
        )
        return response.content[0].text

    def fetch_url_content(self, url: str) -> str:
        """Fetch and summarize content from a URL."""
        import requests

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            # Simple text extraction (could be improved with BeautifulSoup)
            content = response.text[:5000]  # Limit content length

            # Ask LLM to summarize
            messages = [
                {"role": "system", "content": "Summarize the key information from this webpage content that would be relevant for planning or scheduling."},
                {"role": "user", "content": f"URL: {url}\n\nContent:\n{content}"},
            ]

            return self._call_llm(messages)
        except Exception as e:
            return f"Unable to fetch URL content: {str(e)}"


def get_llm_client(provider: Optional[str] = None) -> LLMClient:
    """Get an LLM client instance."""
    if provider is None:
        # Check which API key is available
        if os.getenv("OPENAI_API_KEY"):
            provider = "openai"
        elif os.getenv("ANTHROPIC_API_KEY"):
            provider = "anthropic"
        else:
            provider = "openai"  # Default, will fail if no key

    return LLMClient(provider=provider)
