"""Seed the database with initial data."""
import asyncio
from sqlalchemy import select
from app.database import engine, async_session, Base
from app.models import *  # noqa: F401,F403
from app.services.auth import get_password_hash


async def seed():
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as db:
        # Check if already seeded
        result = await db.execute(select(User))
        if result.first():
            print("Database already seeded.")
            return

        # --- Activity Types ---
        activity_types = [
            ActivityType(name="experiment", description="Lab Experiment"),
            ActivityType(name="project", description="Course Project"),
            ActivityType(name="research", description="Research Work"),
            ActivityType(name="practice", description="Practice / Self-study"),
        ]
        db.add_all(activity_types)

        # --- Users ---
        admin = User(
            student_id="admin",
            name="Lab Administrator",
            email="admin@lab.local",
            password_hash=get_password_hash("admin123"),
            role="admin",
            department="ECE",
        )
        faculty = User(
            student_id="faculty01",
            name="Dr. Kumar",
            email="kumar@lab.local",
            password_hash=get_password_hash("faculty123"),
            role="faculty",
            department="ECE",
        )
        students = []
        for i in range(1, 6):
            students.append(
                User(
                    student_id=f"22EC{i:03d}",
                    name=f"Student {i}",
                    email=f"22ec{i:03d}@college.edu",
                    password_hash=get_password_hash("student123"),
                    role="student",
                    department="ECE",
                )
            )
        db.add_all([admin, faculty] + students)

        # --- Computers ---
        computers = []
        for i in range(1, 41):
            computers.append(
                Computer(
                    hostname=f"VLSI-PC-{i:02d}",
                    lab="VLSI Lab",
                    ip_address=f"192.168.1.{100 + i}",
                    status="available" if i <= 37 else "offline",
                )
            )
        db.add_all(computers)

        # --- Software ---
        software_list = [
            Software(name="Cadence Virtuoso", category="EDA", license_type="commercial"),
            Software(name="Xilinx Vivado", category="EDA", license_type="commercial"),
            Software(name="ModelSim", category="Simulation", license_type="commercial"),
            Software(name="LTspice", category="Simulation", license_type="free"),
            Software(name="MATLAB", category="Computation", license_type="commercial"),
            Software(name="Python", category="Programming", license_type="open-source"),
            Software(name="Synopsys Design Compiler", category="EDA", license_type="commercial"),
            Software(name="Quartus Prime", category="EDA", license_type="commercial"),
            Software(name="KiCad", category="EDA", license_type="open-source"),
            Software(name="GNU Octave", category="Computation", license_type="open-source"),
        ]
        db.add_all(software_list)

        # --- Courses ---
        courses = [
            Course(code="EC401", name="VLSI Design", department="ECE", semester="7"),
            Course(code="EC402", name="Digital Signal Processing", department="ECE", semester="7"),
            Course(code="EC301", name="Analog Electronics", department="ECE", semester="5"),
            Course(code="EC302", name="Microprocessors", department="ECE", semester="5"),
        ]
        db.add_all(courses)
        await db.flush()

        # --- Experiments ---
        vlsi_experiments = [
            Experiment(course_id=courses[0].id, number=1, title="CMOS Inverter Design"),
            Experiment(course_id=courses[0].id, number=2, title="CMOS NAND Gate"),
            Experiment(course_id=courses[0].id, number=3, title="CMOS NOR Gate"),
            Experiment(course_id=courses[0].id, number=4, title="Ring Oscillator"),
            Experiment(course_id=courses[0].id, number=5, title="Current Mirror"),
            Experiment(course_id=courses[0].id, number=6, title="Differential Amplifier"),
        ]
        dsp_experiments = [
            Experiment(course_id=courses[1].id, number=1, title="DFT and FFT"),
            Experiment(course_id=courses[1].id, number=2, title="FIR Filter Design"),
            Experiment(course_id=courses[1].id, number=3, title="IIR Filter Design"),
        ]
        db.add_all(vlsi_experiments + dsp_experiments)

        # --- Projects ---
        projects = [
            Project(title="8-bit ALU Design", course_id=courses[0].id, created_by=faculty.id),
            Project(title="Audio Equalizer", course_id=courses[1].id, created_by=faculty.id),
        ]
        db.add_all(projects)

        # --- Research ---
        research_list = [
            Research(title="Low-Power SRAM Design", supervisor_id=faculty.id),
            Research(title="FinFET Modeling", supervisor_id=faculty.id),
        ]
        db.add_all(research_list)

        await db.commit()
        print("Database seeded successfully!")
        print("\nDefault credentials:")
        print("  Admin:   admin / admin123")
        print("  Faculty: faculty01 / faculty123")
        print("  Student: 22EC001-005 / student123")


if __name__ == "__main__":
    asyncio.run(seed())
