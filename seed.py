"""Seed the database with all 5 bulletins and reference data."""

import asyncio
import os
import sys

from dotenv import load_dotenv

load_dotenv()

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from auth import get_password_hash
from database import Base

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@localhost:5432/church_bulletin")


async def seed():
    engine = create_async_engine(DATABASE_URL)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # Import models after Base is set up
    from models.announcement import Announcement
    from models.bulletin import Bulletin
    from models.calendar_event import CalendarEvent
    from models.contact import Contact
    from models.coordinator import Coordinator
    from models.program import ProgramItem
    from models.user import User

    async with session_factory() as session:
        # --- Users ---
        session.add(User(username="admin", hashed_password=get_password_hash("admin123"), role="admin"))
        session.add(User(username="editor", hashed_password=get_password_hash("editor123"), role="editor"))

        # --- Calendar Events ---
        calendar_events = [
            CalendarEvent(day="Monday-Friday", time="7:00 AM", name="Morning Manna", location="SB102"),
            CalendarEvent(day="Wednesday", time="5:00 PM", name="MIT", location=""),
            CalendarEvent(day="Wednesday", time="7:00 PM", name="Mid-Week Prayer", location=""),
            CalendarEvent(day="Saturday", time="9:00 AM", name="Sabbath School", location=""),
            CalendarEvent(day="Saturday", time="10:30 AM", name="Divine Service", location=""),
            CalendarEvent(day="Saturday", time="3:00 PM", name="Pathfinder", location=""),
            CalendarEvent(day="Saturday", time="5:00 PM", name="AY", location=""),
        ]
        session.add_all(calendar_events)

        # --- Contacts ---
        contacts = [
            Contact(name="Dr. Surachet Insom", category="pastoral_staff", email="surachet@apiu.edu", phone="0898932770", display_order=1),
            Contact(name="Pr. Victor Bejota", category="pastoral_staff", email="int.pastor@apiu.edu", phone="0812604200", display_order=2),
            Contact(name="Pr. Dal Za Kap", category="pastoral_staff", email="dalzakap@apiu.edu", phone="0634193342", display_order=3),
            Contact(name="Khun Thitaree Sirikulpat", category="membership_transfer", email="thitaree@seumsda.org", phone=None, display_order=1),
            Contact(name="Ms. Payom Sriharat", category="flower_donation", email="mc-mart@apiu.edu", phone="0836933916", display_order=1),
            Contact(name="Ms. Chrystal Naltan", category="bulletin", email="chrystal@apiu.edu", phone="0944130176", display_order=1),
        ]
        session.add_all(contacts)

        # =====================================================================
        # BULLETIN 1: January 24, 2026
        # =====================================================================
        b1 = Bulletin(id="2026-01-24", date="January 24, 2026", lesson_code="Q1 L4",
                      lesson_title="Unity Through Humility", sabbath_ends="6:06 PM", next_sabbath="6:09 PM")
        session.add(b1)

        # Coordinators
        session.add_all([
            Coordinator(bulletin_id="2026-01-24", type="worship", value="Combined Worship at the Church"),
            Coordinator(bulletin_id="2026-01-24", type="deacons", value="Anthoney Thangiah & deacons; Marry Jane Bambury & Mirma Naag"),
            Coordinator(bulletin_id="2026-01-24", type="greeters", value="Wan & Group (China)"),
        ])

        # Lesson Study
        session.add(ProgramItem(bulletin_id="2026-01-24", block="lesson_study", sequence=1,
                                role="Lesson Study", note="Q1 L4 – Unity Through Humility", person="SS Classes"))

        # SS Program
        ss1 = [
            ProgramItem(bulletin_id="2026-01-24", block="ss_program", sequence=1, role="Praise & Worship", person="GraceForce"),
            ProgramItem(bulletin_id="2026-01-24", block="ss_program", sequence=2, role="Message in Song", person="GraceForce"),
            ProgramItem(bulletin_id="2026-01-24", block="ss_program", sequence=3, role="Message", note="What the Angels Said", person="Dan Smith"),
            ProgramItem(bulletin_id="2026-01-24", block="ss_program", sequence=4, role="Translator", person="Surachet Insom"),
        ]
        session.add_all(ss1)

        # Divine Service
        ds1 = [
            ProgramItem(bulletin_id="2026-01-24", block="divine_service", sequence=1, role="Welcome", person="Victor Montano"),
            ProgramItem(bulletin_id="2026-01-24", block="divine_service", sequence=2, role="Welcome Song", note="Welcome to the Family", person="GraceForce"),
            ProgramItem(bulletin_id="2026-01-24", block="divine_service", sequence=3, role="Praise & Worship", person="GraceForce"),
            ProgramItem(bulletin_id="2026-01-24", block="divine_service", sequence=4, role="Introit", note="Be Still, For the Presence of the Lord", person="GraceForce"),
            ProgramItem(bulletin_id="2026-01-24", block="divine_service", sequence=5, role="Invocation", person="Dan Smith"),
            ProgramItem(bulletin_id="2026-01-24", block="divine_service", sequence=6, role="Hymn of Praise", note="Worthy is the Lamb", person="GraceForce"),
            ProgramItem(bulletin_id="2026-01-24", block="divine_service", sequence=7, role="Pastoral Prayer", person="Victor Montano"),
            ProgramItem(bulletin_id="2026-01-24", block="divine_service", sequence=8, role="Call for Offering", person="Haydn Golden"),
            ProgramItem(bulletin_id="2026-01-24", block="divine_service", sequence=9, role="Offertory", person="Sergio Leiva"),
            ProgramItem(bulletin_id="2026-01-24", block="divine_service", sequence=10, role="Message in Song", person="AIU Choir"),
            ProgramItem(bulletin_id="2026-01-24", block="divine_service", sequence=11, role="Scripture Reading", note="Matthew 25:10-13", person="Athitiya Kattiya"),
            ProgramItem(bulletin_id="2026-01-24", block="divine_service", sequence=12, role="Message", note="In or Out", person="Dan Smith", is_sermon=True),
            ProgramItem(bulletin_id="2026-01-24", block="divine_service", sequence=13, role="Closing Song", note="Assurance Song", person="GraceForce"),
            ProgramItem(bulletin_id="2026-01-24", block="divine_service", sequence=14, role="Benediction", person="Dan Smith"),
            ProgramItem(bulletin_id="2026-01-24", block="divine_service", sequence=15, role="Translator", person="Nakhon Kitjaroonchai, Kamolnan Taweeyanyongkul"),
            ProgramItem(bulletin_id="2026-01-24", block="divine_service", sequence=16, role="Pianist", person="Sergio Leiva"),
        ]
        session.add_all(ds1)

        # Announcements
        session.add_all([
            Announcement(bulletin_id="2026-01-24", sequence=1, title="Fellowship Lunch",
                         body="Visitors invited to University Cafeteria. Coupons from Mrs. Ritha Maidom at reception desk."),
            Announcement(bulletin_id="2026-01-24", sequence=2, title="Cushion for Church",
                         body="Donate a cushion: 1.9m=1200 baht, 1.4m=800 baht. Krungsri Bank acct 055-1-84654-2. Mark: Cushion for Church."),
            Announcement(bulletin_id="2026-01-24", sequence=3, title="AIU English Bible Camp 2026",
                         body="Feb 20-22 at Mela Garden Cottage. Theme: Chosen, Called, Committed. Speaker: Pr. Kenneth Martinez. Fee: 800 baht."),
            Announcement(bulletin_id="2026-01-24", sequence=4, title="Flower Donation",
                         body="From Arts and Humanities (English Thai Program) for thanksgiving."),
        ])

        # =====================================================================
        # BULLETIN 2: January 31, 2026
        # =====================================================================
        b2 = Bulletin(id="2026-01-31", date="January 31, 2026", lesson_code="Q1 L5",
                      lesson_title="Shining as Lights in the Night", sabbath_ends="6:13 PM", next_sabbath="6:18 PM")
        session.add(b2)

        session.add_all([
            Coordinator(bulletin_id="2026-01-31", type="worship", value="English Service at the Auditorium"),
            Coordinator(bulletin_id="2026-01-31", type="deacons", value="Kameta Katenga; Selfa Montano & Rojean Marcia"),
            Coordinator(bulletin_id="2026-01-31", type="greeters", value="Myanmar Group"),
        ])

        session.add(ProgramItem(bulletin_id="2026-01-31", block="lesson_study", sequence=1,
                                role="Lesson Study", note="Q1 L5 – Shining as Lights in the Night", person="SS Classes"))

        session.add_all([
            ProgramItem(bulletin_id="2026-01-31", block="ss_program", sequence=1, role="Praise & Worship", person="Jubiana Jikson & Co."),
            ProgramItem(bulletin_id="2026-01-31", block="ss_program", sequence=2, role="Mission Spotlight", person="Gerald Mahedhie"),
            ProgramItem(bulletin_id="2026-01-31", block="ss_program", sequence=3, role="Mission 360°", person="Video"),
        ])

        ds2 = [
            ProgramItem(bulletin_id="2026-01-31", block="divine_service", sequence=1, role="Welcome", person="Noah Balraj"),
            ProgramItem(bulletin_id="2026-01-31", block="divine_service", sequence=2, role="Welcome Song", note="Welcome to the Family", person="Jubiana Jikson & Co."),
            ProgramItem(bulletin_id="2026-01-31", block="divine_service", sequence=3, role="Praise & Worship", person="Jubiana Jikson & Co."),
            ProgramItem(bulletin_id="2026-01-31", block="divine_service", sequence=4, role="Introit", note="Be Still, For the Presence of the Lord", person="Jubiana Jikson & Co."),
            ProgramItem(bulletin_id="2026-01-31", block="divine_service", sequence=5, role="Sabbath Song of Celebration", note="It's the Sabbath", person="Jubiana Jikson & Co."),
            ProgramItem(bulletin_id="2026-01-31", block="divine_service", sequence=6, role="Invocation", person="George Knight"),
            ProgramItem(bulletin_id="2026-01-31", block="divine_service", sequence=7, role="Hymn of Praise", note="SDAH#250 O for a Thousand Tongues to Sing", person="Jubiana Jikson & Co."),
            ProgramItem(bulletin_id="2026-01-31", block="divine_service", sequence=8, role="Pastoral Prayer", person="Noah Balraj"),
            ProgramItem(bulletin_id="2026-01-31", block="divine_service", sequence=9, role="Call for Offering", note="Church Combined Budget", person="Hamengamon Kharsynniang"),
            ProgramItem(bulletin_id="2026-01-31", block="divine_service", sequence=10, role="Offertory", person="Pianist"),
            ProgramItem(bulletin_id="2026-01-31", block="divine_service", sequence=11, role="Children's Story", person="Yadahron Hexo"),
            ProgramItem(bulletin_id="2026-01-31", block="divine_service", sequence=12, role="Message in Song", person="Geya and Mario"),
            ProgramItem(bulletin_id="2026-01-31", block="divine_service", sequence=13, role="Scripture Reading", note="John 3:5", person="Josephine Nakalita"),
            ProgramItem(bulletin_id="2026-01-31", block="divine_service", sequence=14, role="Message", note="What Happened to Harry Orchard?", person="George Knight", is_sermon=True),
            ProgramItem(bulletin_id="2026-01-31", block="divine_service", sequence=15, role="Closing Song", note="SDAH#109 Marvelous Grace", person="Jubiana Jikson & Co."),
            ProgramItem(bulletin_id="2026-01-31", block="divine_service", sequence=16, role="Benediction", person="George Knight"),
            ProgramItem(bulletin_id="2026-01-31", block="divine_service", sequence=17, role="Pianist", person="Evelyn Salibio"),
        ]
        session.add_all(ds2)

        session.add_all([
            Announcement(bulletin_id="2026-01-31", sequence=1, title="Fellowship Lunch",
                         body="AIU Church Dining Hall immediately after Divine Service.", recurring=True),
            Announcement(bulletin_id="2026-01-31", sequence=2, title="Cushion for Church",
                         body="Donate a cushion: 1.9m=1200 baht, 1.4m=800 baht. Krungsri Bank acct 055-1-84654-2. Mark: Cushion for Church."),
            Announcement(bulletin_id="2026-01-31", sequence=3, title="AIU English Bible Camp 2026",
                         body="Feb 20-22 at Mela Garden Cottage. Theme: Chosen, Called, Committed. Speaker: Pr. Kenneth Martinez. Fee: 800 baht."),
        ])

        # =====================================================================
        # BULLETIN 3: February 14, 2026
        # =====================================================================
        b3 = Bulletin(id="2026-02-14", date="February 14, 2026", lesson_code="Q1 L7",
                      lesson_title="A Heavenly Citizenship", sabbath_ends="6:18 PM", next_sabbath="6:20 PM")
        session.add(b3)

        session.add_all([
            Coordinator(bulletin_id="2026-02-14", type="worship", value="English Service at the Auditorium"),
            Coordinator(bulletin_id="2026-02-14", type="deacons", value="Haydn Golden; Clarie Gura & Nerliza Flores"),
            Coordinator(bulletin_id="2026-02-14", type="greeters", value="Salem & Ethiopian group"),
        ])

        session.add(ProgramItem(bulletin_id="2026-02-14", block="lesson_study", sequence=1,
                                role="Lesson Study", note="Q1 L7 – A Heavenly Citizenship", person="SS Classes"))

        session.add_all([
            ProgramItem(bulletin_id="2026-02-14", block="ss_program", sequence=1, role="Praise & Worship", person="Praise Him"),
            ProgramItem(bulletin_id="2026-02-14", block="ss_program", sequence=2, role="Opening Remarks", person="Mallen Cortes"),
            ProgramItem(bulletin_id="2026-02-14", block="ss_program", sequence=3, role="Opening Prayer", person="Sreyna Pok"),
            ProgramItem(bulletin_id="2026-02-14", block="ss_program", sequence=4, role="Mission Spotlight", person="Charleen Niebres"),
            ProgramItem(bulletin_id="2026-02-14", block="ss_program", sequence=5, role="Mission 360°", person="Video"),
            ProgramItem(bulletin_id="2026-02-14", block="ss_program", sequence=6, role="Closing Prayer", person="Charleen Niebres"),
        ])

        ds3 = [
            ProgramItem(bulletin_id="2026-02-14", block="divine_service", sequence=1, role="Welcome", person="Franklin Hutabarat"),
            ProgramItem(bulletin_id="2026-02-14", block="divine_service", sequence=2, role="Welcome Song", note="Welcome to the Family", person="Praise Him"),
            ProgramItem(bulletin_id="2026-02-14", block="divine_service", sequence=3, role="Praise & Worship", person="Praise Him"),
            ProgramItem(bulletin_id="2026-02-14", block="divine_service", sequence=4, role="Introit", note="Be Still, For the Presence of the Lord", person="Praise Him"),
            ProgramItem(bulletin_id="2026-02-14", block="divine_service", sequence=5, role="Sabbath Song of Celebration", note="It's the Sabbath", person="Praise Him"),
            ProgramItem(bulletin_id="2026-02-14", block="divine_service", sequence=6, role="Invocation", person="Loren Agrey"),
            ProgramItem(bulletin_id="2026-02-14", block="divine_service", sequence=7, role="Hymn of Praise", note="SDAH#171 Thine is the Glory", person="Praise Him"),
            ProgramItem(bulletin_id="2026-02-14", block="divine_service", sequence=8, role="Pastoral Prayer", person="Franklin Hutabarat"),
            ProgramItem(bulletin_id="2026-02-14", block="divine_service", sequence=9, role="Call for Offering", note="Church Combined Budget", person="Hiram Reagan Panggabean"),
            ProgramItem(bulletin_id="2026-02-14", block="divine_service", sequence=10, role="Offertory", person="Zamira & Nisa"),
            ProgramItem(bulletin_id="2026-02-14", block="divine_service", sequence=11, role="Children's Story", person="Brian Sam Agum"),
            ProgramItem(bulletin_id="2026-02-14", block="divine_service", sequence=12, role="Message in Song", person="Praise Him"),
            ProgramItem(bulletin_id="2026-02-14", block="divine_service", sequence=13, role="Scripture Reading", note="1 John 4:7-12", person="Rhein Daimoye"),
            ProgramItem(bulletin_id="2026-02-14", block="divine_service", sequence=14, role="Message", note="The Final Argument", person="Loren Agrey", is_sermon=True),
            ProgramItem(bulletin_id="2026-02-14", block="divine_service", sequence=15, role="Closing Song", note="SDAH#183 I Will Sing of Jesus Love", person="Praise Him"),
            ProgramItem(bulletin_id="2026-02-14", block="divine_service", sequence=16, role="Benediction", person="Loren Agrey"),
            ProgramItem(bulletin_id="2026-02-14", block="divine_service", sequence=17, role="Pianist", person="Adelaide Francis"),
        ]
        session.add_all(ds3)

        session.add_all([
            Announcement(bulletin_id="2026-02-14", sequence=1, title="Flower Contribution",
                         body="From Mr. Victor Win Htet Aung for thanksgiving for Thai and International Church."),
            Announcement(bulletin_id="2026-02-14", sequence=2, title="Fellowship Lunch",
                         body="Ground Floor of the IT Building (near First Aid Clinic) after Divine Service."),
            Announcement(bulletin_id="2026-02-14", sequence=3, title="Fasting & Prayer Sabbath Feb 21",
                         body="Fri Feb 20: 6-7pm Fellowship Hall. Sat Feb 21: 8-9am and 2-5pm Fellowship Hall/Mother's Room."),
            Announcement(bulletin_id="2026-02-14", sequence=4, title="Health Ministry",
                         body="Outreach group meets at 1:30 PM in SB201.", recurring=True),
            Announcement(bulletin_id="2026-02-14", sequence=5, title="Dorcas Ministry",
                         body="Free lunchboxes Feb 15, 11AM-12:30PM, in front of cafeteria, first come first served."),
            Announcement(bulletin_id="2026-02-14", sequence=6, title="Combined Church Service Feb 21",
                         body="Guest speaker: Dr. Ginger Ketting-Weller, President of AIIAS."),
        ])

        # =====================================================================
        # BULLETIN 4: February 28, 2026
        # =====================================================================
        b4 = Bulletin(id="2026-02-28", date="February 28, 2026", lesson_code="Q1 L9",
                      lesson_title="Reconciliation and Hope", sabbath_ends="6:22 PM", next_sabbath="6:24 PM")
        session.add(b4)

        session.add_all([
            Coordinator(bulletin_id="2026-02-28", type="worship", value="Combined Service at the Church"),
            Coordinator(bulletin_id="2026-02-28", type="deacons", value="Alby Mathew Jacob; Deanna Hutabarat & Lalhmunmawii Kachchhap"),
            Coordinator(bulletin_id="2026-02-28", type="greeters", value="Mili and Indian group"),
        ])

        session.add(ProgramItem(bulletin_id="2026-02-28", block="lesson_study", sequence=1,
                                role="Lesson Study", note="Q1 L9 – Reconciliation and Hope", person="SS Classes"))

        session.add_all([
            ProgramItem(bulletin_id="2026-02-28", block="ss_program", sequence=1, role="Praise & Worship", person="AIU Chorale"),
            ProgramItem(bulletin_id="2026-02-28", block="ss_program", sequence=2, role="Presentation",
                        note="Grounded in the Bible. Focused on the Mission through Literature Ministry", person="Rey Cabanero"),
        ])

        ds4 = [
            ProgramItem(bulletin_id="2026-02-28", block="divine_service", sequence=1, role="Welcome", person="Gerard Bernard"),
            ProgramItem(bulletin_id="2026-02-28", block="divine_service", sequence=2, role="Welcome Song", note="Welcome to the Family", person="AIU Chorale"),
            ProgramItem(bulletin_id="2026-02-28", block="divine_service", sequence=3, role="Praise & Worship", person="AIU Chorale"),
            ProgramItem(bulletin_id="2026-02-28", block="divine_service", sequence=4, role="Introit", note="Be Still, For the Presence of the Lord", person="AIU Chorale"),
            ProgramItem(bulletin_id="2026-02-28", block="divine_service", sequence=5, role="Sabbath Song of Celebration", note="It's the Sabbath", person="AIU Chorale"),
            ProgramItem(bulletin_id="2026-02-28", block="divine_service", sequence=6, role="Invocation", person="Ginger Ketting-Weller"),
            ProgramItem(bulletin_id="2026-02-28", block="divine_service", sequence=7, role="Hymn of Praise", note="SDAH#528 A Shelter in the Time of Storm", person="AIU Chorale"),
            ProgramItem(bulletin_id="2026-02-28", block="divine_service", sequence=8, role="Pastoral Prayer", person="Gerard Bernard"),
            ProgramItem(bulletin_id="2026-02-28", block="divine_service", sequence=9, role="Call for Offering", note="Church Combined Budget", person="Kameta Katenga"),
            ProgramItem(bulletin_id="2026-02-28", block="divine_service", sequence=10, role="Offertory", person="AIMS Connection"),
            ProgramItem(bulletin_id="2026-02-28", block="divine_service", sequence=11, role="Children's Story", note="Translator: Peeranat Kongsang", person="Judith Joel"),
            ProgramItem(bulletin_id="2026-02-28", block="divine_service", sequence=12, role="Message in Song", person="AIU Chorale"),
            ProgramItem(bulletin_id="2026-02-28", block="divine_service", sequence=13, role="Scripture Reading", note="Psalm 56:8-11", person="Leonarde Valwen Tan"),
            ProgramItem(bulletin_id="2026-02-28", block="divine_service", sequence=14, role="Message", note="Praise the Lord; the Tractor's Broken", person="Ginger Ketting-Weller", is_sermon=True),
            ProgramItem(bulletin_id="2026-02-28", block="divine_service", sequence=15, role="Closing Song", note="SDAH#99 God Will Take Care of You", person="AIU Chorale"),
            ProgramItem(bulletin_id="2026-02-28", block="divine_service", sequence=16, role="Benediction", person="Ginger Ketting-Weller"),
            ProgramItem(bulletin_id="2026-02-28", block="divine_service", sequence=17, role="Pianist", person="Anna Mathew"),
            ProgramItem(bulletin_id="2026-02-28", block="divine_service", sequence=18, role="Translators", person="Tantip Kitjaroonchai, Surachet Insom"),
        ]
        session.add_all(ds4)

        session.add_all([
            Announcement(bulletin_id="2026-02-28", sequence=1, title="Fellowship Lunch",
                         body="AIU Church Dining Hall immediately after Divine Service.", recurring=True),
            Announcement(bulletin_id="2026-02-28", sequence=2, title="Health Ministry",
                         body="Outreach group meets at 1:30 PM in SB201.", recurring=True),
            Announcement(bulletin_id="2026-02-28", sequence=3, title="Church Services Next Sabbath Mar 7",
                         body="International Church: AIU Church. Thai Church: Fellowship Hall."),
            Announcement(bulletin_id="2026-02-28", sequence=4, title="Indoor Games Multi-Generational Mar 3",
                         body="Tue March 3, 9AM-5PM, IT Second Floor APIU. Free. Bible games, fellowship, themed meals. Contact: Prema Marshall +66 954 670 461."),
        ])

        # =====================================================================
        # BULLETIN 5: March 7, 2026
        # =====================================================================
        b5 = Bulletin(id="2026-03-07", date="March 7, 2026", lesson_code="Q1 L10",
                      lesson_title="Complete in Christ", sabbath_ends="6:24 PM", next_sabbath="6:26 PM")
        session.add(b5)

        session.add_all([
            Coordinator(bulletin_id="2026-03-07", type="worship", value="English Service at the Church"),
            Coordinator(bulletin_id="2026-03-07", type="deacons", value="Honesto Encapas; Alvina Sulankey & Yarmichon Zimik"),
            Coordinator(bulletin_id="2026-03-07", type="greeters", value="Melody and Indonesian group"),
        ])

        session.add(ProgramItem(bulletin_id="2026-03-07", block="lesson_study", sequence=1,
                                role="Lesson Study", note="Q1 L10 – Complete in Christ", person="SS Classes"))

        session.add_all([
            ProgramItem(bulletin_id="2026-03-07", block="ss_program", sequence=1, role="Praise & Worship", person="Addel Joe & Co."),
            ProgramItem(bulletin_id="2026-03-07", block="ss_program", sequence=2, role="Mission Spotlight", person="Moite Kachchhap"),
            ProgramItem(bulletin_id="2026-03-07", block="ss_program", sequence=3, role="Mission 360°", person="Video"),
            ProgramItem(bulletin_id="2026-03-07", block="ss_program", sequence=4, role="Pianist", person="Adriana Masilung"),
        ])

        ds5 = [
            ProgramItem(bulletin_id="2026-03-07", block="divine_service", sequence=1, role="Welcome", person="Alfredo Agustin"),
            ProgramItem(bulletin_id="2026-03-07", block="divine_service", sequence=2, role="Welcome Song", note="Welcome to the Family", person="Addel Joe & Co."),
            ProgramItem(bulletin_id="2026-03-07", block="divine_service", sequence=3, role="Praise & Worship", person="Addel Joe & Co."),
            ProgramItem(bulletin_id="2026-03-07", block="divine_service", sequence=4, role="Introit", note="Be Still, For the Presence of the Lord", person="Addel Joe & Co."),
            ProgramItem(bulletin_id="2026-03-07", block="divine_service", sequence=5, role="Sabbath Song of Celebration", note="It's the Sabbath", person="Addel Joe & Co."),
            ProgramItem(bulletin_id="2026-03-07", block="divine_service", sequence=6, role="Invocation", person="Victor Bejota"),
            ProgramItem(bulletin_id="2026-03-07", block="divine_service", sequence=7, role="Hymn of Praise", note="SDAH#272 Give Me the Bible", person="Addel Joe & Co."),
            ProgramItem(bulletin_id="2026-03-07", block="divine_service", sequence=8, role="Pastoral Prayer", person="Alfredo Agustin"),
            ProgramItem(bulletin_id="2026-03-07", block="divine_service", sequence=9, role="Call for Offering", note="Church Combined Budget", person="Anthoney Thangiah"),
            ProgramItem(bulletin_id="2026-03-07", block="divine_service", sequence=10, role="Offertory", person="Masilung Sisters"),
            ProgramItem(bulletin_id="2026-03-07", block="divine_service", sequence=11, role="Children's Story", person="Yarmichon Zimik"),
            ProgramItem(bulletin_id="2026-03-07", block="divine_service", sequence=12, role="Message in Song", person="Voice of Harmony"),
            ProgramItem(bulletin_id="2026-03-07", block="divine_service", sequence=13, role="Scripture Reading", note="Acts 8:29-31", person="Selected"),
            ProgramItem(bulletin_id="2026-03-07", block="divine_service", sequence=14, role="Message", note="Teachers Wanted", person="Victor Bejota", is_sermon=True),
            ProgramItem(bulletin_id="2026-03-07", block="divine_service", sequence=15, role="Closing Song", note="SDAH#340 Jesus Saves", person="Addel Joe & Co."),
            ProgramItem(bulletin_id="2026-03-07", block="divine_service", sequence=16, role="Benediction", person="Victor Bejota"),
            ProgramItem(bulletin_id="2026-03-07", block="divine_service", sequence=17, role="Pianist", person="Adriana Masilung"),
        ]
        session.add_all(ds5)

        session.add_all([
            Announcement(bulletin_id="2026-03-07", sequence=1, title="Flower Contribution",
                         body="From Mr. Victor Win Htet Aung for thanksgiving for Thai and International Church."),
            Announcement(bulletin_id="2026-03-07", sequence=2, title="Note of Appreciation",
                         body="Gratitude to Korean donors for two brand-new projectors now installed and operational."),
            Announcement(bulletin_id="2026-03-07", sequence=3, title="Fellowship Lunch",
                         body="University Cafeteria. Coupons from Mrs. Ritha Maidom at reception desk."),
            Announcement(bulletin_id="2026-03-07", sequence=4, title="Health Ministry",
                         body="Outreach group meets at 1:30 PM in SB201.", recurring=True),
        ])

        await session.commit()

    await engine.dispose()
    print("Database seeded successfully!")
    print("Users created: admin/admin123 (admin), editor/editor123 (editor)")
    print(f"Bulletins created: 5 (Jan 24, Jan 31, Feb 14, Feb 28, Mar 7 — all 2026)")


if __name__ == "__main__":
    asyncio.run(seed())
