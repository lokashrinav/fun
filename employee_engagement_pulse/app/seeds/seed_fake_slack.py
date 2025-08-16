"""Seed synthetic Slack‑like events into the local database or optionally post to Slack."""
import os, random, time, argparse, datetime as dt
from faker import Faker
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
import json

# Add parent directory to path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models import RawEvent, Channel, Base  # reuse your SQLAlchemy model

try:
    from slack_sdk import WebClient
except ImportError:
    WebClient = None  # allow offline mode

fake = Faker()

# -------- utility helpers --------
PERSONA_SENTENCES = {
    "dev": [
        "Pushed hot‑fix to prod — need review",
        "Anyone seen the flaky test in CI?",
        "Refactoring auth module today",
        "Deploy pipeline is red again 😕",
        "Fixed the memory leak in the payment service",
        "Code review ready for feature-auth-2023",
        "Database migration completed successfully",
        "API response time improved by 40%",
        "Unit tests are passing locally but failing in CI",
        "Need to rollback the latest deploy ASAP",
        "Optimized the query, should be much faster now",
        "Docker container keeps crashing on startup",
        "Successfully merged the feature branch",
        "Found the root cause of the timeout issues"
    ],
    "qa": [
        "Test case failing on staging, opening bug ticket",
        "Regression run passed, ready for release",
        "Need repro steps for ISSUE‑123",
        "Smoke tests green 👍",
        "Found critical bug in payment flow",
        "Automation suite completed - 98% pass rate",
        "Manual testing done for user registration",
        "Performance tests show 10% improvement",
        "Browser compatibility issues on IE11",
        "Load testing revealed bottlenecks",
        "Security scan completed with minor findings",
        "User acceptance testing starts tomorrow",
        "Found edge case that breaks the form validation",
        "Mobile app testing complete, all good"
    ],
    "manager": [
        "Reminder: retro moved to 4 PM, please add notes",
        "Stand‑up in five, join the call",
        "Great job shipping sprint goal! 🎉",
        "Please update story points before EOD",
        "Sprint planning meeting tomorrow at 10 AM",
        "Need volunteers for the hackathon team",
        "Q4 OKRs are due next Friday",
        "Team lunch scheduled for Thursday",
        "New intern starts Monday, please help onboard",
        "Budget approved for the monitoring tools",
        "Client demo went really well today!",
        "Performance reviews due by month end",
        "Conference budget available for 2 people",
        "Team building event next month - ideas welcome"
    ],
    "designer": [
        "New mockups ready for the dashboard redesign",
        "User research findings shared in #design",
        "A/B test results favor the blue button",
        "Updated the design system documentation",
        "Accessibility audit completed for main pages",
        "Mobile designs need developer review",
        "Brand guidelines updated with new colors",
        "Prototype ready for user testing session",
        "Icon library expanded with 50+ new icons",
        "Typography scale adjusted for better readability",
        "Dark mode designs are now ready",
        "Competitor analysis shared in Figma"
    ],
    "devops": [
        "Kubernetes cluster upgrade scheduled tonight",
        "Monitoring alerts are working perfectly",
        "Infrastructure costs down 15% this month",
        "New environment provisioned for staging",
        "SSL certificates renewed successfully",
        "Backup restore test completed successfully",
        "CDN performance improved significantly",
        "Security patches applied to all servers",
        "Database replication is now fully synchronized",
        "Container registry cleanup freed up 50GB",
        "Load balancer configuration optimized",
        "Disaster recovery drill scheduled for Friday"
    ],
    "random": [
        "Lunch time? 🍕",
        "Coffee break ☕",
        "Friday fun fact: sloths can hold breath 40 min",
        "Anyone tried the new restaurant downstairs?",
        "Weather is perfect for a walk today",
        "Happy Friday everyone! 🎉",
        "Team trivia night next week",
        "New coffee machine is amazing",
        "Who's up for table tennis after work?",
        "Dog photos always welcome here 🐕",
        "Weekend plans anyone?",
        "Thanks for helping with the move!",
        "Birthday cake in the kitchen 🎂",
        "Office plants need watering again"
    ],
}

EMOJI_POOL = [
    ":thumbsup:", ":thumbsdown:", ":fire:", ":eyes:", ":tada:", ":thinking_face:",
    ":coffee:", ":pizza:", ":rocket:", ":bug:", ":wrench:", ":warning:",
    ":100:", ":muscle:", ":star:", ":heart:", ":laughing:", ":confused:",
    ":rage:", ":disappointed:", ":sweat_smile:"
]

WORK_TOPICS = {
    "deploy": ["Deployment successful", "Rolling back deploy", "Deploy scheduled for 2 PM", "Production deploy completed"],
    "incident": ["P1 incident in progress", "Service restored", "Investigating high error rates", "Post-mortem scheduled"],
    "code-review": ["PR ready for review", "LGTM, approved", "Please fix the linting issues", "Great refactoring work!"],
    "planning": ["Sprint planning notes", "Story points updated", "Backlog refinement done", "Roadmap priorities set"],
    "meeting": ["Daily standup in 5 minutes", "Retro feedback captured", "All-hands meeting summary", "Client meeting went well"],
    "testing": ["Test suite passing", "Found regression bug", "Load test results", "User acceptance complete"],
    "infrastructure": ["Server maintenance window", "Database migration done", "Monitoring setup complete", "Performance improvements"],
    "release": ["Release notes published", "Version 2.1 is live", "Hotfix deployed", "Beta testing starts Monday"]
}

def pick_sentence(persona, topics=None):
    """Pick a sentence based on persona and optional topics"""
    pool = PERSONA_SENTENCES.get(persona, PERSONA_SENTENCES["random"])
    
    # If topics are specified, sometimes use topic-specific messages
    if topics and random.random() < 0.3:
        topic = random.choice(topics.split(','))
        if topic in WORK_TOPICS:
            pool.extend(WORK_TOPICS[topic])
    
    return random.choice(pool)

def random_ts(days_back: int, start_date: dt.date | None):
    """Generate random timestamp within the specified range"""
    if start_date:
        start_epoch = int(time.mktime(start_date.timetuple()))
        end_epoch = int(time.time())
    else:
        end_epoch = int(time.time())
        start_epoch = end_epoch - days_back * 86400
    return random.randint(start_epoch, end_epoch)

def create_fake_user(i: int, personas: list) -> dict:
    """Create a fake user with realistic developer-style names"""
    dev_names = [
        "Alex Chen", "Jordan Smith", "Sam Rodriguez", "Casey Johnson", "Morgan Lee",
        "Taylor Brown", "Jamie Wilson", "Avery Davis", "Riley Martinez", "Blake Anderson",
        "Quinn Taylor", "Sage Thompson", "River Johnson", "Phoenix Garcia", "Kai Patel"
    ]
    
    name = fake.name() if i >= len(dev_names) else dev_names[i]
    
    return {
        "id": f"U{1000+i:04d}",
        "real_name": name,
        "display_name": name.split()[0].lower() + str(random.randint(10, 99)),
        "persona": random.choice(personas),
    }

# -------- main seeding logic --------

def seed(args):
    """Main seeding function"""
    # Setup database connection
    database_url = os.getenv("DATABASE_URL", "sqlite:///./employee_pulse.db")
    engine = create_engine(database_url)
    
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    
    Session = sessionmaker(bind=engine)
    session = Session()

    # Slack client (optional)
    client = None
    if args.real:
        if WebClient is None:
            raise RuntimeError("slack_sdk not installed; pip install slack_sdk")
        client = WebClient(token=os.getenv("SLACK_BOT_TOKEN"))

    # Create/ensure channels exist
    channel_objects = []
    for channel_name in args.channels:
        channel_id = f"C{random.randint(100000, 999999)}"  # Fake channel ID
        
        # Check if channel exists
        existing_channel = session.query(Channel).filter(Channel.name == channel_name).first()
        if existing_channel:
            channel_objects.append(existing_channel)
            print(f"Using existing channel: {channel_name}")
        else:
            new_channel = Channel(
                id=channel_id,
                name=channel_name,
                description=f"Auto-generated channel for {channel_name}",
                is_active=True
            )
            session.add(new_channel)
            session.commit()
            channel_objects.append(new_channel)
            print(f"Created new channel: {channel_name} ({channel_id})")

    # build fake users
    personas = args.personas.split(",") if args.personas else ["random"]
    users = [create_fake_user(i, personas) for i in range(args.users)]
    
    print(f"Generated {len(users)} fake users with personas: {personas}")
    
    messages_created = 0
    reactions_created = 0

    # Generate messages
    for _ in range(args.messages):
        user = random.choice(users)
        channel = random.choice(channel_objects)
        ts_int = random_ts(args.days, args.start_date)
        ts = f"{ts_int}.{random.randint(100000, 999999)}"
        
        # Generate message text
        text = pick_sentence(user["persona"], args.topics)
        
        # Maybe add emoji inside text
        if random.random() < 0.3:
            text += " " + random.choice(EMOJI_POOL)

        # Create event structure
        event_dict = {
            "token": "fake_token",
            "team_id": "T12345",
            "api_app_id": "A12345", 
            "event": {
                "type": "message",
                "user": user["id"],
                "text": text,
                "channel": channel.id,
                "ts": ts,
                "event_ts": ts,
                "channel_type": "channel"
            },
            "type": "event_callback",
            "event_id": f"Ev{random.randint(100000000, 999999999)}",
            "event_time": ts_int
        }

        if args.real and client:
            try:
                # Post to actual Slack
                response = client.chat_postMessage(
                    channel=channel.name,  # Use channel name for real posting
                    text=text,
                    username=user["display_name"]
                )
                print(f"Posted message to #{channel.name}: {text[:50]}...")
            except Exception as e:
                print(f"Error posting to Slack: {e}")
        else:
            # Store in database
            raw_event = RawEvent(
                event_type="message",
                channel_id=channel.id,
                user_id=user["id"],
                timestamp=ts,
                json_data=event_dict,
                processed=False
            )
            session.add(raw_event)
            messages_created += 1

        # Maybe add reactions
        if random.random() < 0.4:  # 40% chance of reactions
            num_reactions = random.randint(1, 3)
            for _ in range(num_reactions):
                reactor = random.choice(users)
                if reactor["id"] != user["id"]:  # Don't react to own messages
                    reaction = random.choice(EMOJI_POOL).strip(":")
                    
                    react_event = {
                        "token": "fake_token",
                        "team_id": "T12345",
                        "api_app_id": "A12345",
                        "event": {
                            "type": "reaction_added",
                            "user": reactor["id"],
                            "reaction": reaction,
                            "item_user": user["id"],
                            "item": {
                                "type": "message",
                                "channel": channel.id,
                                "ts": ts
                            },
                            "event_ts": f"{ts_int + 1}.000000"
                        },
                        "type": "event_callback",
                        "event_id": f"Ev{random.randint(100000000, 999999999)}"
                    }
                    
                    if not args.real:
                        raw_reaction = RawEvent(
                            event_type="reaction_added",
                            channel_id=channel.id,
                            user_id=reactor["id"],
                            timestamp=ts,
                            json_data=react_event,
                            processed=False
                        )
                        session.add(raw_reaction)
                        reactions_created += 1

        # Commit in batches for better performance
        if messages_created % 50 == 0:
            session.commit()
            print(f"Processed {messages_created} messages so far...")

    # Final commit
    session.commit()
    session.close()

    print(f"\n✅ Seeding completed!")
    print(f"📊 Created {messages_created} messages and {reactions_created} reactions")
    print(f"📋 Across {len(args.channels)} channels with {len(users)} users")
    if args.real:
        print(f"🔗 Posted to actual Slack workspace")
    else:
        print(f"💾 Stored in local database only")

# -------- argparse --------
if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Generate synthetic Slack data for testing")
    p.add_argument("--channels", nargs="+", default=["general"], 
                  help="Channel names to populate")
    p.add_argument("--days", type=int, default=7, 
                  help="Number of days back to spread messages")
    p.add_argument("--messages", type=int, default=200, 
                  help="Total number of messages to generate")
    p.add_argument("--users", type=int, default=10, 
                  help="Number of fake users to create")
    p.add_argument("--personas", default="dev,qa,manager", 
                  help="Comma-separated list of user personas")
    p.add_argument("--topics", default="", 
                  help="Comma-separated list of work topics to include")
    p.add_argument("--start-date", type=lambda s: dt.datetime.strptime(s, "%Y-%m-%d").date(), 
                  help="Fixed start date (YYYY-MM-DD)")
    p.add_argument("--real", action="store_true", 
                  help="Actually post to Slack (requires SLACK_BOT_TOKEN)")
    
    args = p.parse_args()

    # Validate arguments
    if args.real and not os.getenv("SLACK_BOT_TOKEN"):
        print("❌ Error: SLACK_BOT_TOKEN environment variable required for --real mode")
        exit(1)
    
    if args.messages <= 0 or args.users <= 0:
        print("❌ Error: messages and users must be positive integers")
        exit(1)

    print(f"🎯 Starting data generation...")
    print(f"📱 Channels: {args.channels}")
    print(f"👥 Users: {args.users} ({args.personas})")
    print(f"💬 Messages: {args.messages}")
    print(f"📅 Time range: {args.days} days back" + 
          (f" from {args.start_date}" if args.start_date else ""))
    print(f"🎭 Topics: {args.topics or 'none specified'}")
    print()

    seed(args)
