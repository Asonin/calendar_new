"""
Agentic Calendar - Presentation Slide Generator

Generates a PowerPoint presentation introducing the Agentic Calendar project.
Run this script to generate the slides, then add your screenshots to the placeholder slides.
"""

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.util import Pt
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.dml.color import RGBColor
import os

# Color scheme
PRIMARY_COLOR = RGBColor(52, 152, 219)    # Blue
SECONDARY_COLOR = RGBColor(46, 204, 113)  # Green
ACCENT_COLOR = RGBColor(155, 89, 182)     # Purple
DARK_COLOR = RGBColor(44, 62, 80)         # Dark blue-gray
LIGHT_COLOR = RGBColor(236, 240, 241)     # Light gray


def add_title_slide(prs, title, subtitle=""):
    """Add a title slide."""
    slide_layout = prs.slide_layouts[6]  # Blank layout
    slide = prs.slides.add_slide(slide_layout)

    # Add background shape
    shape = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = PRIMARY_COLOR
    shape.line.fill.background()

    # Title
    title_box = slide.shapes.add_textbox(
        Inches(0.5), Inches(2.5), Inches(9), Inches(1.5)
    )
    title_frame = title_box.text_frame
    title_para = title_frame.paragraphs[0]
    title_para.text = title
    title_para.font.size = Pt(44)
    title_para.font.bold = True
    title_para.font.color.rgb = RGBColor(255, 255, 255)
    title_para.alignment = PP_ALIGN.CENTER

    # Subtitle
    if subtitle:
        sub_box = slide.shapes.add_textbox(
            Inches(0.5), Inches(4), Inches(9), Inches(1)
        )
        sub_frame = sub_box.text_frame
        sub_para = sub_frame.paragraphs[0]
        sub_para.text = subtitle
        sub_para.font.size = Pt(24)
        sub_para.font.color.rgb = RGBColor(255, 255, 255)
        sub_para.alignment = PP_ALIGN.CENTER

    return slide


def add_content_slide(prs, title, bullet_points, highlight_first=False):
    """Add a content slide with bullet points."""
    slide_layout = prs.slide_layouts[6]  # Blank layout
    slide = prs.slides.add_slide(slide_layout)

    # Header bar
    header = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, Inches(1.2)
    )
    header.fill.solid()
    header.fill.fore_color.rgb = PRIMARY_COLOR
    header.line.fill.background()

    # Title
    title_box = slide.shapes.add_textbox(
        Inches(0.5), Inches(0.3), Inches(9), Inches(0.7)
    )
    title_frame = title_box.text_frame
    title_para = title_frame.paragraphs[0]
    title_para.text = title
    title_para.font.size = Pt(32)
    title_para.font.bold = True
    title_para.font.color.rgb = RGBColor(255, 255, 255)

    # Content
    content_box = slide.shapes.add_textbox(
        Inches(0.7), Inches(1.5), Inches(8.6), Inches(5)
    )
    content_frame = content_box.text_frame
    content_frame.word_wrap = True

    for i, point in enumerate(bullet_points):
        if i == 0:
            para = content_frame.paragraphs[0]
        else:
            para = content_frame.add_paragraph()

        para.text = f"• {point}"
        para.font.size = Pt(22)
        para.font.color.rgb = DARK_COLOR
        para.space_after = Pt(14)

        if highlight_first and i == 0:
            para.font.bold = True
            para.font.color.rgb = PRIMARY_COLOR

    return slide


def add_architecture_slide(prs):
    """Add the system architecture slide."""
    slide_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(slide_layout)

    # Header
    header = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, Inches(1.2)
    )
    header.fill.solid()
    header.fill.fore_color.rgb = PRIMARY_COLOR
    header.line.fill.background()

    title_box = slide.shapes.add_textbox(
        Inches(0.5), Inches(0.3), Inches(9), Inches(0.7)
    )
    title_frame = title_box.text_frame
    title_para = title_frame.paragraphs[0]
    title_para.text = "System Architecture"
    title_para.font.size = Pt(32)
    title_para.font.bold = True
    title_para.font.color.rgb = RGBColor(255, 255, 255)

    # Draw architecture boxes
    components = [
        ("Frontend (Streamlit)", Inches(3), Inches(1.6), SECONDARY_COLOR),
        ("LLM Client", Inches(1), Inches(3), ACCENT_COLOR),
        ("Planner", Inches(3), Inches(3), ACCENT_COLOR),
        ("Web Search", Inches(5), Inches(3), ACCENT_COLOR),
        ("Storage (JSON)", Inches(1.5), Inches(4.6), RGBColor(230, 126, 34)),
        ("Calendar Export", Inches(4), Inches(4.6), RGBColor(230, 126, 34)),
    ]

    for name, left, top, color in components:
        box = slide.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE, left, top, Inches(2.2), Inches(0.8)
        )
        box.fill.solid()
        box.fill.fore_color.rgb = color
        box.line.fill.background()

        # Add text to box
        box.text_frame.paragraphs[0].text = name
        box.text_frame.paragraphs[0].font.size = Pt(14)
        box.text_frame.paragraphs[0].font.bold = True
        box.text_frame.paragraphs[0].font.color.rgb = RGBColor(255, 255, 255)
        box.text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER
        box.text_frame.paragraphs[0].space_before = Pt(8)

    # External services
    ext_box = slide.shapes.add_shape(
        MSO_SHAPE.CLOUD, Inches(7.2), Inches(2.8), Inches(2), Inches(1.2)
    )
    ext_box.fill.solid()
    ext_box.fill.fore_color.rgb = RGBColor(149, 165, 166)
    ext_box.text_frame.paragraphs[0].text = "OpenAI/\nAnthropic"
    ext_box.text_frame.paragraphs[0].font.size = Pt(12)
    ext_box.text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER

    return slide


def add_flow_slide(prs):
    """Add the user flow slide."""
    slide_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(slide_layout)

    # Header
    header = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, Inches(1.2)
    )
    header.fill.solid()
    header.fill.fore_color.rgb = PRIMARY_COLOR
    header.line.fill.background()

    title_box = slide.shapes.add_textbox(
        Inches(0.5), Inches(0.3), Inches(9), Inches(0.7)
    )
    title_frame = title_box.text_frame
    title_para = title_frame.paragraphs[0]
    title_para.text = "User Flow: 5-Step Process"
    title_para.font.size = Pt(32)
    title_para.font.bold = True
    title_para.font.color.rgb = RGBColor(255, 255, 255)

    # Flow steps
    steps = [
        ("1. Input", "Enter goal via\ntext/link/image"),
        ("2. Analysis", "LLM understands\nand decomposes"),
        ("3. Review", "Edit tasks\nand resources"),
        ("4. Schedule", "Set availability\nand generate"),
        ("5. Export", "Download .ics\nfor calendar"),
    ]

    colors = [
        RGBColor(52, 152, 219),   # Blue
        RGBColor(155, 89, 182),   # Purple
        RGBColor(46, 204, 113),   # Green
        RGBColor(241, 196, 15),   # Yellow
        RGBColor(231, 76, 60),    # Red
    ]

    start_x = Inches(0.3)
    for i, ((title, desc), color) in enumerate(zip(steps, colors)):
        # Circle with number
        circle = slide.shapes.add_shape(
            MSO_SHAPE.OVAL, start_x + Inches(i * 1.9), Inches(2), Inches(0.8), Inches(0.8)
        )
        circle.fill.solid()
        circle.fill.fore_color.rgb = color
        circle.line.fill.background()

        # Step box
        box = slide.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE,
            start_x + Inches(i * 1.9) - Inches(0.3),
            Inches(3),
            Inches(1.4),
            Inches(1.8)
        )
        box.fill.solid()
        box.fill.fore_color.rgb = LIGHT_COLOR
        box.line.color.rgb = color
        box.line.width = Pt(3)

        # Title text
        title_tb = slide.shapes.add_textbox(
            start_x + Inches(i * 1.9) - Inches(0.3),
            Inches(3.1),
            Inches(1.4),
            Inches(0.5)
        )
        tf = title_tb.text_frame
        tf.paragraphs[0].text = title
        tf.paragraphs[0].font.size = Pt(14)
        tf.paragraphs[0].font.bold = True
        tf.paragraphs[0].font.color.rgb = color
        tf.paragraphs[0].alignment = PP_ALIGN.CENTER

        # Description
        desc_tb = slide.shapes.add_textbox(
            start_x + Inches(i * 1.9) - Inches(0.3),
            Inches(3.6),
            Inches(1.4),
            Inches(1)
        )
        tf = desc_tb.text_frame
        tf.word_wrap = True
        tf.paragraphs[0].text = desc
        tf.paragraphs[0].font.size = Pt(11)
        tf.paragraphs[0].font.color.rgb = DARK_COLOR
        tf.paragraphs[0].alignment = PP_ALIGN.CENTER

        # Arrow (except last)
        if i < len(steps) - 1:
            arrow = slide.shapes.add_shape(
                MSO_SHAPE.RIGHT_ARROW,
                start_x + Inches(i * 1.9) + Inches(1.2),
                Inches(3.7),
                Inches(0.5),
                Inches(0.3)
            )
            arrow.fill.solid()
            arrow.fill.fore_color.rgb = RGBColor(189, 195, 199)
            arrow.line.fill.background()

    return slide


def add_code_slide(prs, title, code_snippet, description=""):
    """Add a code implementation slide."""
    slide_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(slide_layout)

    # Header
    header = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, Inches(1.2)
    )
    header.fill.solid()
    header.fill.fore_color.rgb = PRIMARY_COLOR
    header.line.fill.background()

    title_box = slide.shapes.add_textbox(
        Inches(0.5), Inches(0.3), Inches(9), Inches(0.7)
    )
    title_frame = title_box.text_frame
    title_para = title_frame.paragraphs[0]
    title_para.text = title
    title_para.font.size = Pt(32)
    title_para.font.bold = True
    title_para.font.color.rgb = RGBColor(255, 255, 255)

    # Description
    if description:
        desc_box = slide.shapes.add_textbox(
            Inches(0.5), Inches(1.4), Inches(9), Inches(0.5)
        )
        desc_frame = desc_box.text_frame
        desc_para = desc_frame.paragraphs[0]
        desc_para.text = description
        desc_para.font.size = Pt(16)
        desc_para.font.color.rgb = DARK_COLOR
        code_top = Inches(2)
    else:
        code_top = Inches(1.5)

    # Code box
    code_bg = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE,
        Inches(0.3), code_top, Inches(9.4), Inches(4.5)
    )
    code_bg.fill.solid()
    code_bg.fill.fore_color.rgb = RGBColor(40, 44, 52)  # Dark background
    code_bg.line.fill.background()

    # Code text
    code_box = slide.shapes.add_textbox(
        Inches(0.5), code_top + Inches(0.2), Inches(9), Inches(4.2)
    )
    code_frame = code_box.text_frame
    code_frame.word_wrap = True

    for i, line in enumerate(code_snippet.split('\n')):
        if i == 0:
            para = code_frame.paragraphs[0]
        else:
            para = code_frame.add_paragraph()
        para.text = line
        para.font.name = "Courier New"
        para.font.size = Pt(11)
        para.font.color.rgb = RGBColor(171, 178, 191)  # Light gray
        para.space_after = Pt(2)

    return slide


def add_screenshot_placeholder_slide(prs, title, instructions):
    """Add a slide with placeholder for screenshot."""
    slide_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(slide_layout)

    # Header
    header = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, Inches(1.2)
    )
    header.fill.solid()
    header.fill.fore_color.rgb = PRIMARY_COLOR
    header.line.fill.background()

    title_box = slide.shapes.add_textbox(
        Inches(0.5), Inches(0.3), Inches(9), Inches(0.7)
    )
    title_frame = title_box.text_frame
    title_para = title_frame.paragraphs[0]
    title_para.text = title
    title_para.font.size = Pt(32)
    title_para.font.bold = True
    title_para.font.color.rgb = RGBColor(255, 255, 255)

    # Placeholder box
    placeholder = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE,
        Inches(0.5), Inches(1.5), Inches(9), Inches(4.8)
    )
    placeholder.fill.solid()
    placeholder.fill.fore_color.rgb = LIGHT_COLOR
    placeholder.line.color.rgb = RGBColor(189, 195, 199)
    placeholder.line.width = Pt(2)
    placeholder.line.dash_style = 2  # Dashed

    # Placeholder text
    text_box = slide.shapes.add_textbox(
        Inches(1), Inches(3), Inches(8), Inches(1.5)
    )
    text_frame = text_box.text_frame
    text_frame.word_wrap = True

    para = text_frame.paragraphs[0]
    para.text = "📷 INSERT SCREENSHOT HERE"
    para.font.size = Pt(24)
    para.font.bold = True
    para.font.color.rgb = RGBColor(149, 165, 166)
    para.alignment = PP_ALIGN.CENTER

    para2 = text_frame.add_paragraph()
    para2.text = instructions
    para2.font.size = Pt(14)
    para2.font.color.rgb = RGBColor(149, 165, 166)
    para2.alignment = PP_ALIGN.CENTER

    return slide


def generate_presentation():
    """Generate the complete presentation."""
    prs = Presentation()
    prs.slide_width = Inches(10)
    prs.slide_height = Inches(7.5)

    # Slide 1: Title
    add_title_slide(
        prs,
        "Agentic Calendar",
        "An Intelligent Planning Assistant\nwith LLM-Powered Task Decomposition"
    )

    # Slide 2: Motivation
    add_content_slide(prs, "Motivation", [
        "Traditional calendars only provide reminders, not actionable guidance",
        "Users struggle to break down complex goals into manageable tasks",
        "Finding relevant learning resources is time-consuming",
        "Manual scheduling often ignores realistic time constraints",
        "Gap between goal-setting and execution leads to abandoned plans",
        "Need: An intelligent assistant that understands goals and creates actionable, scheduled plans with real resources"
    ], highlight_first=True)

    # Slide 3: Purpose
    add_content_slide(prs, "Purpose & Goals", [
        "Goal-Driven Planning: Understand user objectives, not just reminders",
        "Intelligent Decomposition: Break complex goals into concrete tasks using LLM",
        "Real Resource Discovery: Search YouTube & web for verified learning materials",
        "Availability-Aware Scheduling: Respect user's time constraints",
        "Seamless Integration: Export to Apple Calendar, Google Calendar, Outlook",
        "HCI-Focused Design: Simple, intuitive interface following Nielsen's heuristics"
    ])

    # Slide 4: System Architecture
    add_architecture_slide(prs)

    # Slide 5: User Flow
    add_flow_slide(prs)

    # Slide 6: HCI Design Principles
    add_content_slide(prs, "Design Principles (Nielsen's Heuristics)", [
        "H1 - Visibility: Progress stepper shows current step clearly",
        "H2 - Match Real World: Familiar calendar metaphors and icons",
        "H3 - User Control: Cancel, go back, edit, regenerate at any step",
        "H5 - Error Prevention: Input validation, confirmation dialogs",
        "H6 - Recognition: Pre-filled examples, auto-complete suggestions",
        "H10 - Help: In-app guidance, tooltips, and user manual"
    ])

    # Slide 7: Code Implementation - LLM Integration
    code1 = '''def decompose_goal(self, goal_summary, deadline):
    """Break down goal into tasks with search queries."""
    prompt = TASK_DECOMPOSITION_PROMPT.format(
        goal_summary=goal_summary,
        deadline=deadline,
        today=datetime.now()
    )

    # Get tasks from LLM
    tasks = self._call_llm(prompt)

    # Search real resources for each task
    resource_results = search_resources_parallel(tasks)

    for idx, task in enumerate(tasks):
        task["resources"] = resource_results.get(idx, [])

    return tasks'''

    add_code_slide(
        prs,
        "Code: LLM Task Decomposition",
        code1,
        "The LLM generates tasks with search queries, then we fetch real resources from YouTube and the web."
    )

    # Slide 8: Code Implementation - Resource Search
    code2 = '''def search_youtube(query: str, num_results: int = 2):
    """Search YouTube and return real video results."""
    url = f"https://youtube.com/results?search_query={query}"
    response = requests.get(url, headers=headers)

    # Extract video IDs from YouTube's embedded JSON
    pattern = r'"videoId":"([a-zA-Z0-9_-]{11})"'
    video_ids = re.findall(pattern, response.text)

    return [{"url": f"https://youtube.com/watch?v={vid}",
             "type": "video"} for vid in video_ids]

def search_web(query: str):
    """Search DuckDuckGo for articles and tutorials."""
    url = f"https://html.duckduckgo.com/html/?q={query}"
    # Parse and return real search results...'''

    add_code_slide(
        prs,
        "Code: Real Resource Search",
        code2,
        "We search YouTube and DuckDuckGo directly to get verified, working URLs - no hallucinated links."
    )

    # Slide 9: Usage Example 1
    add_screenshot_placeholder_slide(
        prs,
        "Demo: Goal Input & Analysis",
        "Take a screenshot of the Input and Analysis steps"
    )

    # Slide 10: Usage Example 2
    add_screenshot_placeholder_slide(
        prs,
        "Demo: Task Review & Resources",
        "Take a screenshot showing tasks with YouTube/web resources"
    )

    # Slide 11: Future Work
    add_content_slide(prs, "Future Work", [
        "Google Calendar API integration for direct sync (no .ics export)",
        "Progress tracking and task completion monitoring",
        "Collaborative planning for team projects",
        "Smart rescheduling when tasks are missed or delayed",
        "Mobile app version for iOS and Android",
        "Learning path recommendations based on user history"
    ])

    # Save
    output_path = os.path.join(os.path.dirname(__file__), "Agentic_Calendar_Presentation.pptx")
    prs.save(output_path)
    print(f"Presentation saved to: {output_path}")
    return output_path


if __name__ == "__main__":
    generate_presentation()
