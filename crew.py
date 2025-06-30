from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List
from thunderautomation.tools.custom_tool import SeleniumScriptExecutor, VisualAnalyzer 

@CrewBase
class Thunderautomation():
    agents: List[BaseAgent]
    tasks: List[Task]

    @agent
    def screenshot_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["screenshot_agent"],
            tools=[SeleniumScriptExecutor()],
            verbose=True
        )

    @agent
    def visual_analyzer(self) -> Agent:
        return Agent(
            config=self.agents_config["visual_analyzer"],
            tools=[VisualAnalyzer()],
            verbose=True
        )

    @agent
    def reporting_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["reporting_analyst"],
            verbose=True
        )

    @task
    def screenshot_task(self) -> Task:
        return Task(
        config=self.tasks_config["screenshot_task"],
        input=lambda ctx: {
            "script_code": ctx.get("screenshot_task"),
            "folder": f"screenshots/{ctx.get('url_hash')}"
        }
    )

    @task
    def analyze_task(self) -> Task:
        return Task(
            config=self.tasks_config["analyze_task"],
            input=lambda ctx: {
                "screenshot_paths": ctx.get("screenshot_task")
            }
        )

    @task
    def reporting_task(self) -> Task:
        return Task(
            config=self.tasks_config["reporting_task"],
            input=lambda _: {
                "insight_path": "insights/insights.json"
            },
            output_file="final_report.md"
        )

    def crew(self):
        return Crew(
            agents=[
                self.screenshot_agent(),
                self.visual_analyzer(),
                self.reporting_analyst()
            ],
            tasks=[
                self.screenshot_task(),
                self.analyze_task(),
                self.reporting_task()
            ],
            process=Process.sequential
        )
