import hashlib
import base64
from datetime import datetime
from pathlib import Path


def get_image_base64(image_path: str) -> str:
    p = Path(image_path)
    if p.exists():
        return base64.b64encode(p.read_bytes()).decode()
    return ""


def hex_to_rgba(hex_color: str, alpha: float) -> str:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


def generate_session_id(name: str) -> str:
    raw = f"{name}-{datetime.now().isoformat()}"
    return hashlib.sha256(raw.encode()).hexdigest()[:12]


def truncate_text(text: str, max_length: int = 200) -> str:
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."


def format_xp(xp: int) -> str:
    if xp >= 1000:
        return f"{xp / 1000:.1f}K"
    return str(xp)


SUGGESTED_QUESTIONS = {
    "general": [
        "What's the most important leadership lesson you've learned?",
        "How do you handle tough decisions under pressure?",
        "What advice would you give to emerging leaders?",
    ],
    "strategy": [
        "How do you approach AI transformation?",
        "What's your framework for long-term strategy?",
        "How do you balance innovation with execution?",
    ],
    "people": [
        "How do you build trust with your team?",
        "What's your approach to handling underperformance?",
        "How do you create a culture of psychological safety?",
    ],
    "growth": [
        "What role does failure play in leadership growth?",
        "How do you stay ahead of industry changes?",
        "What habits define great leaders?",
    ],
}

SCENARIOS: list[dict] = [
    {
        "category": "AI Transformation",
        "icon": "🤖",
        "items": [
            {"title": "AI Resistance from Senior Staff", "prompt": "My senior managers are pushing back on adopting AI tools — they see it as a threat to their teams. How would you handle this resistance without losing their trust?"},
            {"title": "Choosing the First AI Use Case", "prompt": "We have budget for one AI pilot project this quarter. How do you decide which use case to prioritize when every department wants to go first?"},
            {"title": "AI Ethics Dilemma", "prompt": "Our AI model is performing well but we discovered it has bias against certain demographics. Fixing it would delay the launch by 3 months. What would you do?"},
            {"title": "GenAI Replacing Jobs", "prompt": "My team is terrified that GenAI will eliminate their roles within 2 years. Morale is dropping. How do I address their fears honestly without making promises I can't keep?"},
            {"title": "AI Governance Framework", "prompt": "We have 15 teams building AI solutions independently with no standards. The CEO wants a governance framework by next month. Where do you start?"},
            {"title": "ROI of AI Investment", "prompt": "We spent $2M on AI last year and the board is asking where the ROI is. Most projects are still in pilot. How do you justify continued investment?"},
            {"title": "Build vs. Buy AI", "prompt": "We can build a custom ML model in 6 months or buy an off-the-shelf solution now. Engineering wants to build, business wants speed. How do you decide?"},
        ],
    },
    {
        "category": "Crisis Leadership",
        "icon": "🔥",
        "items": [
            {"title": "Major Client Escalation", "prompt": "Our biggest client just threatened to leave because of repeated delivery failures. The team is demoralized. How do you handle the next 48 hours?"},
            {"title": "Key Leader Suddenly Quits", "prompt": "Your star VP just resigned to join a competitor — taking two senior directors with them. How do you stabilize the team and prevent further attrition?"},
            {"title": "Public PR Crisis", "prompt": "A data breach has been reported in the media and clients are calling. The board wants answers by tomorrow. How do you lead through this?"},
            {"title": "Failed Product Launch", "prompt": "We launched a major product last week and it flopped — zero adoption, negative reviews, and $500K spent. The team who built it is devastated. What now?"},
            {"title": "Layoffs Announcement", "prompt": "You've been told to lay off 20% of your team next Monday. You disagree with the decision but can't change it. How do you handle the communication and aftermath?"},
            {"title": "Whistleblower Complaint", "prompt": "An anonymous whistleblower reported that a senior director has been falsifying project metrics to clients. How do you investigate without creating panic?"},
        ],
    },
    {
        "category": "Team & Culture",
        "icon": "🤝",
        "items": [
            {"title": "Toxic High Performer", "prompt": "Your top revenue-generating employee is brilliant but toxic — they bully peers and juniors avoid working with them. Do you keep them or let them go?"},
            {"title": "Remote vs. Return to Office", "prompt": "Half your team wants full remote, the other half wants in-office collaboration. Leadership is pushing for 4 days in office. How do you navigate this?"},
            {"title": "Merging Two Rival Teams", "prompt": "After a reorg, you need to merge two teams that have historically competed against each other. There's tension and mistrust. What's your 90-day plan?"},
            {"title": "Diversity Hiring Pushback", "prompt": "You set a goal to increase diversity in leadership by 30%. Some managers say you're lowering the bar. How do you respond?"},
            {"title": "Team Trust Breakdown", "prompt": "Your team has stopped sharing honest feedback. Meetings are silent, 1-on-1s are surface-level. You suspect fear of retaliation from a previous manager. How do you rebuild trust?"},
            {"title": "Cross-Generational Conflict", "prompt": "Your Gen-Z hires want flexible hours and purpose-driven work. Your senior team calls them 'entitled.' The tension is real. How do you bridge this gap?"},
            {"title": "Micromanager Complaint", "prompt": "Three team members independently told HR that their manager is a micromanager destroying morale. That manager is one of your best executors. How do you handle it?"},
        ],
    },
    {
        "category": "Strategy & Growth",
        "icon": "📈",
        "items": [
            {"title": "Should We Enter a New Market?", "prompt": "We have an opportunity to expand into healthcare analytics but zero domain expertise. The market is huge but the learning curve is steep. Would you go for it?"},
            {"title": "Cutting Costs Without Cutting People", "prompt": "The board wants 15% cost reduction this year. You believe layoffs destroy culture. What creative alternatives would you propose?"},
            {"title": "Competitor Undercutting Pricing", "prompt": "A competitor just slashed prices by 30% and two of our prospects switched. Do you match their price, or hold your ground? What's the playbook?"},
            {"title": "Acquisition Opportunity", "prompt": "A smaller competitor is up for sale at 3x revenue. They have great talent and clients but a messy tech stack. Do you acquire or grow organically?"},
            {"title": "Pivoting the Business Model", "prompt": "Our traditional consulting revenue is declining 10% YoY while our SaaS product is growing 40%. Should we pivot the entire company to product-led growth?"},
            {"title": "Innovation Lab Failing", "prompt": "Our innovation lab has existed for 2 years and produced zero revenue-generating products. The team says they need more time. Do you shut it down or restructure?"},
        ],
    },
    {
        "category": "Personal Leadership",
        "icon": "🧭",
        "items": [
            {"title": "First 90 Days as New Leader", "prompt": "I just got promoted to lead a team I was previously a peer on. Some colleagues are resentful. How should I approach my first 90 days?"},
            {"title": "Saying No to Your Boss", "prompt": "My CEO wants me to commit to an aggressive timeline that I know my team can't deliver. How do I push back without damaging the relationship?"},
            {"title": "Burnout While Leading Others", "prompt": "I'm burned out but my team depends on me to set the energy. I can't show weakness. How do you handle burnout at the leadership level?"},
            {"title": "Imposter Syndrome at the Top", "prompt": "I just joined as SVP and everyone assumes I have all the answers. Privately, I feel like I'm faking it. How do you deal with imposter syndrome in senior leadership?"},
            {"title": "Difficult Feedback to a Friend", "prompt": "My closest work friend is now my direct report and their performance is slipping. I need to put them on a PIP. How do I have this conversation without destroying our relationship?"},
            {"title": "Skipped for Promotion", "prompt": "I was passed over for a promotion I deserved. The person who got it has less experience. I'm angry but don't want to burn bridges. What would you advise?"},
        ],
    },
    {
        "category": "Client & Delivery",
        "icon": "🎯",
        "items": [
            {"title": "Scope Creep Nightmare", "prompt": "The client keeps adding requirements without adjusting the budget or timeline. My team is working weekends. How do I reset expectations without jeopardizing the relationship?"},
            {"title": "Underperforming Offshore Team", "prompt": "Our offshore delivery team is consistently missing quality benchmarks. The client is noticing. Replacing the team would take 3 months. What's the short-term fix?"},
            {"title": "Client Wants Impossible Deadline", "prompt": "A key client wants a 6-month project delivered in 8 weeks for a board presentation. Saying no might lose the deal. How do you negotiate this?"},
            {"title": "Transition from Project to Product", "prompt": "Our client wants to move from a project-based engagement to a managed services model. The team has no experience in recurring delivery. How do you make this transition?"},
            {"title": "Multiple Clients, Same Resources", "prompt": "Three clients all need your best architect at the same time. You can only assign them to one. How do you allocate scarce talent without losing any client?"},
        ],
    },
    {
        "category": "Change Management",
        "icon": "🔄",
        "items": [
            {"title": "Failed Digital Transformation", "prompt": "Our 18-month digital transformation is behind schedule, over budget, and the organization has change fatigue. Do you push forward, pause, or reset entirely?"},
            {"title": "Resistance to New Process", "prompt": "You rolled out a new project management process and 60% of teams are ignoring it. They say the old way was fine. How do you drive adoption without being authoritarian?"},
            {"title": "Merger Culture Clash", "prompt": "We just merged with a company that has a completely opposite culture — they're aggressive and sales-driven, we're collaborative and process-oriented. How do you unify this?"},
            {"title": "Legacy System Migration", "prompt": "We need to migrate off a 15-year-old system that everyone hates but knows inside-out. Every past attempt failed. How do you finally get this done?"},
            {"title": "Communicating Unpopular Changes", "prompt": "You need to announce that annual bonuses are being cut by 40% this year due to market conditions. How do you communicate this without destroying morale?"},
        ],
    },
    {
        "category": "Data & Analytics",
        "icon": "📊",
        "items": [
            {"title": "Data Quality Chaos", "prompt": "Our analytics team doesn't trust the data. Different dashboards show different numbers. Leadership is making decisions on bad data. Where do you start fixing this?"},
            {"title": "Democratizing Data Access", "prompt": "Business teams want self-serve analytics but IT says it's a security risk. How do you balance data access with governance?"},
            {"title": "Proving Value of Analytics", "prompt": "We built a world-class analytics platform but business adoption is only 15%. Teams still use Excel. How do you drive adoption and prove the investment was worth it?"},
            {"title": "Real-Time Decision Making", "prompt": "Our competitor is making real-time pricing decisions using AI while we still rely on monthly reports. How do you fast-track our move to real-time analytics?"},
            {"title": "CDO vs CTO Conflict", "prompt": "The Chief Data Officer and CTO are in constant conflict over data ownership, tooling, and budget. Both report to you. How do you resolve this structural tension?"},
        ],
    },
]


def get_suggested_questions(category: str = "general") -> list[str]:
    return SUGGESTED_QUESTIONS.get(category, SUGGESTED_QUESTIONS["general"])


def get_scenarios() -> list[dict]:
    return SCENARIOS
